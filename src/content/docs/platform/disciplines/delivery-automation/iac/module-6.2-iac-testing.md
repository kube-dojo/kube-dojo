---
title: "Module 6.2: Infrastructure as Code Testing"
slug: platform/disciplines/delivery-automation/iac/module-6.2-iac-testing
sidebar:
  order: 3
---
## Complexity: [COMPLEX]
## Time to Complete: 55 minutes

---

## Prerequisites

Before starting this module, you should have completed:
- [Module 6.1: IaC Fundamentals](module-6.1-iac-fundamentals/) - Core IaC concepts
- [Module 4.1: Security Mindset](../../../foundations/security-principles/module-4.1-security-mindset/) - Security principles
- Basic understanding of unit testing concepts

---

## Why This Module Matters

**The $4.2 Million Test Gap**

The senior infrastructure engineer stared at the Slack channel in disbelief. Their "simple" Terraform change to modify a security group rule had just taken down the entire production database cluster. The change had passed code review—three experienced engineers had approved it. It had worked perfectly in the dev environment. But nobody had noticed that production used a different naming convention for subnets, and the wildcard in the security group rule matched far more resources than intended.

The postmortem revealed a sobering truth: the team had 94% test coverage for their application code, but zero automated tests for their infrastructure code. The Terraform that provisioned their $50M annual infrastructure? It was tested by "applying it and seeing what happens."

This module teaches you how to test infrastructure code with the same rigor as application code—because infrastructure bugs don't throw exceptions, they cause outages.

---

## The IaC Testing Pyramid

Just like application testing, infrastructure testing follows a pyramid structure where faster, cheaper tests form the base.

```
                    ╱╲
                   ╱  ╲
                  ╱ E2E╲         ← Full environment deployment
                 ╱──────╲          Minutes to hours
                ╱        ╲         Expensive but comprehensive
               ╱Integration╲    ← Real cloud resources
              ╱────────────╲      Minutes per test
             ╱              ╲     Catches API/provider issues
            ╱   Contract     ╲  ← Module interfaces
           ╱──────────────────╲   Seconds per test
          ╱                    ╲  Catches integration issues
         ╱    Unit Testing      ╲← Individual resources
        ╱────────────────────────╲ Milliseconds per test
       ╱                          ╲Catches logic errors
      ╱      Static Analysis       ╲← Linting, formatting
     ╱──────────────────────────────╲ Immediate feedback
    ╱                                ╲ Catches syntax errors
   ╱──────────────────────────────────╲

   MORE TESTS ◄─────────────────► FEWER TESTS
   FASTER     ◄─────────────────► SLOWER
   CHEAPER    ◄─────────────────► EXPENSIVE
```

---

## Level 1: Static Analysis

Static analysis catches errors without executing any code. These tests run in milliseconds and should be part of every commit.

### Formatting and Linting

```bash
# Terraform formatting check
terraform fmt -check -recursive

# Terraform validation (syntax and internal consistency)
terraform validate

# TFLint - catches provider-specific issues
tflint --recursive

# Example .tflint.hcl configuration
cat > .tflint.hcl << 'EOF'
plugin "aws" {
  enabled = true
  version = "0.27.0"
  source  = "github.com/terraform-linters/tflint-ruleset-aws"
}

rule "terraform_naming_convention" {
  enabled = true
  format  = "snake_case"
}

rule "terraform_documented_variables" {
  enabled = true
}

rule "terraform_documented_outputs" {
  enabled = true
}

rule "aws_instance_invalid_type" {
  enabled = true
}

rule "aws_instance_previous_type" {
  enabled = true
}
EOF
```

### Security Scanning

Security scanners catch misconfigurations before they reach production:

```bash
# Checkov - comprehensive policy scanning
checkov -d . --framework terraform

# tfsec - Terraform-specific security scanner
tfsec .

# Trivy - vulnerability and misconfiguration scanner
trivy config .

# Example: Creating custom Checkov policy
cat > custom_policies/require_encryption.py << 'EOF'
from checkov.terraform.checks.resource.base_resource_check import BaseResourceCheck
from checkov.common.models.enums import CheckResult, CheckCategories

class S3BucketEncryption(BaseResourceCheck):
    def __init__(self):
        name = "Ensure S3 bucket has encryption enabled"
        id = "CUSTOM_S3_1"
        supported_resources = ['aws_s3_bucket']
        categories = [CheckCategories.ENCRYPTION]
        super().__init__(name=name, id=id,
                        categories=categories,
                        supported_resources=supported_resources)

    def scan_resource_conf(self, conf):
        # Check for server_side_encryption_configuration
        if 'server_side_encryption_configuration' in conf:
            return CheckResult.PASSED
        return CheckResult.FAILED

check = S3BucketEncryption()
EOF
```

### Pre-commit Hooks

Automate static analysis on every commit:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/antonbabenko/pre-commit-terraform
    rev: v1.83.5
    hooks:
      - id: terraform_fmt
      - id: terraform_validate
      - id: terraform_tflint
        args:
          - --args=--config=__GIT_WORKING_DIR__/.tflint.hcl
      - id: terraform_checkov
        args:
          - --args=--quiet
          - --args=--skip-check CKV_AWS_18,CKV_AWS_21
      - id: terraform_docs
        args:
          - --args=--config=.terraform-docs.yml

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: check-merge-conflict
      - id: detect-aws-credentials
      - id: detect-private-key
```

---

## Level 2: Unit Testing

Unit tests verify individual resources and modules work correctly in isolation. They don't create real infrastructure.

### Terraform Testing Framework (Built-in)

Terraform 1.6+ includes a native testing framework:

```hcl
# tests/vpc_test.tftest.hcl

# Test variables
variables {
  environment = "test"
  vpc_cidr    = "10.0.0.0/16"
}

# Test: VPC CIDR block is correctly set
run "vpc_cidr_validation" {
  command = plan

  assert {
    condition     = aws_vpc.main.cidr_block == "10.0.0.0/16"
    error_message = "VPC CIDR block does not match expected value"
  }
}

# Test: VPC has correct tags
run "vpc_tags_validation" {
  command = plan

  assert {
    condition     = aws_vpc.main.tags["Environment"] == "test"
    error_message = "VPC Environment tag is incorrect"
  }

  assert {
    condition     = can(aws_vpc.main.tags["ManagedBy"])
    error_message = "VPC must have ManagedBy tag"
  }
}

# Test: Subnet CIDR calculation
run "subnet_cidr_calculation" {
  command = plan

  # Verify subnet CIDRs are within VPC CIDR
  assert {
    condition = alltrue([
      for subnet in aws_subnet.private :
      cidrsubnet("10.0.0.0/16", 8, 0) != "" # Valid CIDR math
    ])
    error_message = "Subnet CIDR calculation failed"
  }
}

# Test: Security group rules
run "security_group_rules" {
  command = plan

  # Verify no 0.0.0.0/0 ingress on SSH
  assert {
    condition = !anytrue([
      for rule in aws_security_group.main.ingress :
      rule.from_port == 22 && contains(rule.cidr_blocks, "0.0.0.0/0")
    ])
    error_message = "SSH must not be open to the world"
  }
}
```

Run tests with:

```bash
# Run all tests
terraform test

# Run specific test file
terraform test -filter=tests/vpc_test.tftest.hcl

# Verbose output
terraform test -verbose
```

### Mock Providers for Unit Testing

Use mock providers to test without cloud access:

```hcl
# tests/mocks/aws_mock.tftest.hcl

mock_provider "aws" {
  mock_resource "aws_instance" {
    defaults = {
      id               = "i-mock12345"
      arn              = "arn:aws:ec2:us-east-1:123456789012:instance/i-mock12345"
      private_ip       = "10.0.1.100"
      public_ip        = "203.0.113.100"
      availability_zone = "us-east-1a"
    }
  }

  mock_resource "aws_vpc" {
    defaults = {
      id         = "vpc-mock12345"
      arn        = "arn:aws:ec2:us-east-1:123456789012:vpc/vpc-mock12345"
      cidr_block = var.vpc_cidr
    }
  }

  mock_data "aws_availability_zones" {
    defaults = {
      names = ["us-east-1a", "us-east-1b", "us-east-1c"]
      zone_ids = ["use1-az1", "use1-az2", "use1-az3"]
    }
  }
}

run "test_with_mocks" {
  providers = {
    aws = aws.mock
  }

  assert {
    condition     = aws_instance.web.private_ip != ""
    error_message = "Instance should have private IP"
  }
}
```

### OPA/Conftest for Policy Testing

Use Open Policy Agent to write policy tests:

```rego
# policy/terraform.rego
package terraform

# Deny resources without required tags
deny[msg] {
  resource := input.resource_changes[_]
  resource.type == "aws_instance"
  not resource.change.after.tags.Environment
  msg := sprintf("Instance %s must have Environment tag", [resource.address])
}

# Deny overly permissive security groups
deny[msg] {
  resource := input.resource_changes[_]
  resource.type == "aws_security_group_rule"
  resource.change.after.type == "ingress"
  resource.change.after.cidr_blocks[_] == "0.0.0.0/0"
  resource.change.after.from_port <= 22
  resource.change.after.to_port >= 22
  msg := sprintf("Security group rule %s allows SSH from anywhere", [resource.address])
}

# Enforce encryption at rest
deny[msg] {
  resource := input.resource_changes[_]
  resource.type == "aws_ebs_volume"
  not resource.change.after.encrypted
  msg := sprintf("EBS volume %s must be encrypted", [resource.address])
}

# Limit instance sizes in non-production
deny[msg] {
  resource := input.resource_changes[_]
  resource.type == "aws_instance"

  env := resource.change.after.tags.Environment
  env != "production"

  instance_type := resource.change.after.instance_type
  startswith(instance_type, "x")  # x-large instances

  msg := sprintf("Instance %s uses %s which is too large for %s",
                 [resource.address, instance_type, env])
}
```

Test policies against Terraform plans:

```bash
# Generate plan JSON
terraform plan -out=tfplan
terraform show -json tfplan > tfplan.json

# Test with Conftest
conftest test tfplan.json --policy policy/

# Example output:
# FAIL - tfplan.json - terraform - Instance module.web.aws_instance.app must have Environment tag
# FAIL - tfplan.json - terraform - Security group rule module.web.aws_security_group_rule.ssh allows SSH from anywhere
#
# 2 tests, 0 passed, 0 warnings, 2 failures
```

---

## Level 3: Contract Testing

Contract tests verify that modules work correctly together—that outputs match expected inputs.

### Module Interface Contracts

```hcl
# modules/vpc/outputs.tf - Define the contract
output "vpc_id" {
  description = "The ID of the VPC"
  value       = aws_vpc.main.id

  precondition {
    condition     = aws_vpc.main.id != ""
    error_message = "VPC ID must not be empty"
  }
}

output "private_subnet_ids" {
  description = "List of private subnet IDs"
  value       = aws_subnet.private[*].id

  precondition {
    condition     = length(aws_subnet.private) >= 2
    error_message = "At least 2 private subnets required for HA"
  }
}

output "private_subnet_cidrs" {
  description = "List of private subnet CIDR blocks"
  value       = aws_subnet.private[*].cidr_block
}
```

```hcl
# modules/eks/variables.tf - Consume the contract
variable "vpc_id" {
  description = "VPC ID where EKS cluster will be created"
  type        = string

  validation {
    condition     = can(regex("^vpc-", var.vpc_id))
    error_message = "VPC ID must start with 'vpc-'"
  }
}

variable "subnet_ids" {
  description = "List of subnet IDs for EKS nodes"
  type        = list(string)

  validation {
    condition     = length(var.subnet_ids) >= 2
    error_message = "At least 2 subnets required for EKS HA"
  }

  validation {
    condition     = alltrue([for s in var.subnet_ids : can(regex("^subnet-", s))])
    error_message = "All subnet IDs must start with 'subnet-'"
  }
}
```

### Contract Test File

```hcl
# tests/contract_test.tftest.hcl

# Test VPC module outputs
run "vpc_contract" {
  module {
    source = "./modules/vpc"
  }

  variables {
    environment     = "test"
    vpc_cidr        = "10.0.0.0/16"
    azs             = ["us-east-1a", "us-east-1b"]
  }

  # Verify output format matches consumer expectations
  assert {
    condition     = can(regex("^vpc-", module.vpc.vpc_id))
    error_message = "VPC ID must match expected format"
  }

  assert {
    condition     = length(module.vpc.private_subnet_ids) >= 2
    error_message = "VPC module must output at least 2 private subnets"
  }

  assert {
    condition     = alltrue([
      for id in module.vpc.private_subnet_ids : can(regex("^subnet-", id))
    ])
    error_message = "Subnet IDs must match expected format"
  }
}

# Test EKS module accepts VPC outputs
run "eks_accepts_vpc_contract" {
  module {
    source = "./modules/eks"
  }

  variables {
    cluster_name = "test-cluster"
    vpc_id       = run.vpc_contract.vpc_id
    subnet_ids   = run.vpc_contract.private_subnet_ids
  }

  # If this plans successfully, the contract is satisfied
  command = plan
}
```

---

## Level 4: Integration Testing

Integration tests create real infrastructure to verify it works correctly. These are slower and more expensive but catch real-world issues.

### Terratest (Go-based Testing)

Terratest is the most popular integration testing framework:

```go
// test/vpc_test.go
package test

import (
    "testing"
    "time"

    "github.com/gruntwork-io/terratest/modules/aws"
    "github.com/gruntwork-io/terratest/modules/terraform"
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"
)

func TestVPCModule(t *testing.T) {
    t.Parallel()

    // Use a unique name to avoid conflicts
    uniqueID := random.UniqueId()
    awsRegion := "us-east-1"

    terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
        TerraformDir: "../modules/vpc",
        Vars: map[string]interface{}{
            "environment": fmt.Sprintf("test-%s", uniqueID),
            "vpc_cidr":    "10.0.0.0/16",
            "azs":         []string{"us-east-1a", "us-east-1b"},
        },
        EnvVars: map[string]string{
            "AWS_DEFAULT_REGION": awsRegion,
        },
    })

    // Clean up resources when test completes
    defer terraform.Destroy(t, terraformOptions)

    // Deploy the infrastructure
    terraform.InitAndApply(t, terraformOptions)

    // Get outputs
    vpcID := terraform.Output(t, terraformOptions, "vpc_id")
    privateSubnetIDs := terraform.OutputList(t, terraformOptions, "private_subnet_ids")

    // Verify VPC exists and has correct CIDR
    vpc := aws.GetVpcById(t, vpcID, awsRegion)
    assert.Equal(t, "10.0.0.0/16", vpc.CidrBlock)

    // Verify subnets are in correct AZs
    assert.Len(t, privateSubnetIDs, 2)

    for _, subnetID := range privateSubnetIDs {
        subnet := aws.GetSubnetById(t, subnetID, awsRegion)
        assert.True(t, subnet.MapPublicIpOnLaunch == false,
                   "Private subnets should not map public IPs")
    }

    // Verify DNS settings
    assert.True(t, vpc.EnableDnsHostnames)
    assert.True(t, vpc.EnableDnsSupport)

    // Verify route tables
    routeTables := aws.GetRouteTablesForVpc(t, vpcID, awsRegion)
    assert.GreaterOrEqual(t, len(routeTables), 2,
                          "Should have at least 2 route tables")
}

func TestVPCConnectivity(t *testing.T) {
    t.Parallel()

    // Deploy VPC with EC2 instance to test connectivity
    terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
        TerraformDir: "../examples/vpc-with-bastion",
        Vars: map[string]interface{}{
            "environment": fmt.Sprintf("test-%s", random.UniqueId()),
        },
    })

    defer terraform.Destroy(t, terraformOptions)
    terraform.InitAndApply(t, terraformOptions)

    // Get bastion IP
    bastionIP := terraform.Output(t, terraformOptions, "bastion_public_ip")

    // Test SSH connectivity
    host := ssh.Host{
        Hostname:    bastionIP,
        SshUserName: "ec2-user",
        SshKeyPair:  loadKeyPair(t),
    }

    // Retry SSH connection (instance might still be booting)
    maxRetries := 30
    sleepBetweenRetries := 10 * time.Second

    description := fmt.Sprintf("SSH to bastion at %s", bastionIP)
    ssh.CheckSshConnectionWithRetry(t, host, maxRetries, sleepBetweenRetries, description)

    // Run command on bastion to verify network connectivity
    output := ssh.CheckSshCommand(t, host, "curl -s http://169.254.169.254/latest/meta-data/instance-id")
    assert.Contains(t, output, "i-", "Should return instance ID from metadata service")
}
```

### Testing Patterns

```go
// test/patterns_test.go

// Pattern 1: Test idempotency - applying twice should not change anything
func TestIdempotency(t *testing.T) {
    t.Parallel()

    terraformOptions := &terraform.Options{
        TerraformDir: "../modules/vpc",
        Vars: map[string]interface{}{
            "environment": fmt.Sprintf("test-%s", random.UniqueId()),
        },
    }

    defer terraform.Destroy(t, terraformOptions)

    // First apply
    terraform.InitAndApply(t, terraformOptions)

    // Second apply should show no changes
    planOutput := terraform.Plan(t, terraformOptions)
    assert.Contains(t, planOutput, "No changes",
                   "Second apply should not change anything")
}

// Pattern 2: Test upgrades - can we update without destroying?
func TestInPlaceUpgrade(t *testing.T) {
    t.Parallel()

    terraformOptions := &terraform.Options{
        TerraformDir: "../modules/vpc",
        Vars: map[string]interface{}{
            "environment": "test",
            "vpc_cidr":    "10.0.0.0/16",
        },
    }

    defer terraform.Destroy(t, terraformOptions)

    // Deploy v1
    terraform.InitAndApply(t, terraformOptions)
    vpcIDv1 := terraform.Output(t, terraformOptions, "vpc_id")

    // Update configuration
    terraformOptions.Vars["enable_flow_logs"] = true

    // Apply v2
    terraform.Apply(t, terraformOptions)
    vpcIDv2 := terraform.Output(t, terraformOptions, "vpc_id")

    // VPC should not be replaced
    assert.Equal(t, vpcIDv1, vpcIDv2,
                "VPC should be updated in place, not replaced")
}

// Pattern 3: Test failure scenarios
func TestInvalidCIDRFails(t *testing.T) {
    t.Parallel()

    terraformOptions := &terraform.Options{
        TerraformDir: "../modules/vpc",
        Vars: map[string]interface{}{
            "vpc_cidr": "invalid-cidr",
        },
    }

    // This should fail during plan
    _, err := terraform.PlanE(t, terraformOptions)
    require.Error(t, err, "Invalid CIDR should fail validation")
}

// Pattern 4: Test with multiple configurations
func TestMultipleEnvironments(t *testing.T) {
    t.Parallel()

    testCases := []struct {
        name        string
        environment string
        vpcCIDR     string
        expectedAZs int
    }{
        {"dev", "development", "10.0.0.0/16", 2},
        {"staging", "staging", "10.1.0.0/16", 2},
        {"prod", "production", "10.2.0.0/16", 3},
    }

    for _, tc := range testCases {
        tc := tc // capture range variable
        t.Run(tc.name, func(t *testing.T) {
            t.Parallel()

            terraformOptions := &terraform.Options{
                TerraformDir: "../modules/vpc",
                Vars: map[string]interface{}{
                    "environment": tc.environment,
                    "vpc_cidr":    tc.vpcCIDR,
                },
            }

            defer terraform.Destroy(t, terraformOptions)
            terraform.InitAndApply(t, terraformOptions)

            subnets := terraform.OutputList(t, terraformOptions, "private_subnet_ids")
            assert.Len(t, subnets, tc.expectedAZs)
        })
    }
}
```

---

## Level 5: End-to-End Testing

E2E tests verify complete environments work together as a system.

```go
// test/e2e_test.go

func TestFullEnvironment(t *testing.T) {
    // Skip in short mode - these tests are expensive
    if testing.Short() {
        t.Skip("Skipping E2E test in short mode")
    }

    t.Parallel()

    uniqueID := random.UniqueId()

    // Deploy complete environment
    terraformOptions := &terraform.Options{
        TerraformDir: "../environments/staging",
        Vars: map[string]interface{}{
            "environment": fmt.Sprintf("e2e-%s", uniqueID),
        },
        // Longer timeout for full environment
        MaxRetries:         3,
        TimeBetweenRetries: 30 * time.Second,
    }

    defer terraform.Destroy(t, terraformOptions)
    terraform.InitAndApply(t, terraformOptions)

    // Get outputs
    albDNS := terraform.Output(t, terraformOptions, "alb_dns_name")
    eksEndpoint := terraform.Output(t, terraformOptions, "eks_endpoint")
    rdsEndpoint := terraform.Output(t, terraformOptions, "rds_endpoint")

    // Test 1: ALB is accessible
    t.Run("ALB Health Check", func(t *testing.T) {
        url := fmt.Sprintf("http://%s/health", albDNS)

        http_helper.HttpGetWithRetry(t, url, nil, 200, "healthy",
                                     30, 10*time.Second)
    })

    // Test 2: EKS cluster is accessible
    t.Run("EKS Accessibility", func(t *testing.T) {
        kubeconfig := terraform.Output(t, terraformOptions, "kubeconfig")

        // Write kubeconfig to temp file
        kubeconfigPath := writeKubeconfig(t, kubeconfig)
        defer os.Remove(kubeconfigPath)

        // Test kubectl connectivity
        options := k8s.NewKubectlOptions("", kubeconfigPath, "default")
        k8s.RunKubectl(t, options, "get", "nodes")
    })

    // Test 3: RDS is accessible from VPC
    t.Run("RDS Connectivity", func(t *testing.T) {
        // SSH to bastion and test DB connectivity
        bastionIP := terraform.Output(t, terraformOptions, "bastion_ip")
        dbPassword := terraform.Output(t, terraformOptions, "rds_password")

        host := ssh.Host{
            Hostname:    bastionIP,
            SshUserName: "ec2-user",
            SshKeyPair:  loadKeyPair(t),
        }

        // Test MySQL connectivity
        command := fmt.Sprintf(
            "mysql -h %s -u admin -p%s -e 'SELECT 1'",
            rdsEndpoint, dbPassword,
        )
        ssh.CheckSshCommand(t, host, command)
    })

    // Test 4: End-to-end application flow
    t.Run("Application Flow", func(t *testing.T) {
        // Create a test user
        createUserURL := fmt.Sprintf("http://%s/api/users", albDNS)
        response := http_helper.HTTPDo(t, "POST", createUserURL,
                                       []byte(`{"name":"test"}`), nil)
        assert.Equal(t, 201, response.StatusCode)

        // Verify user was created
        getUserURL := fmt.Sprintf("http://%s/api/users/test", albDNS)
        http_helper.HttpGetWithRetry(t, getUserURL, nil, 200, "test",
                                     5, 2*time.Second)
    })
}
```

---

## CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/terraform-test.yml
name: Terraform Tests

on:
  pull_request:
    paths:
      - 'terraform/**'
      - '.github/workflows/terraform-test.yml'
  push:
    branches: [main]

env:
  TF_VERSION: "1.6.0"
  GO_VERSION: "1.21"

jobs:
  static-analysis:
    name: Static Analysis
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}

      - name: Terraform Format Check
        run: terraform fmt -check -recursive terraform/

      - name: Terraform Validate
        run: |
          cd terraform/modules/vpc
          terraform init -backend=false
          terraform validate

      - name: TFLint
        uses: terraform-linters/setup-tflint@v4
        with:
          tflint_version: latest

      - run: |
          tflint --init
          tflint --recursive terraform/

      - name: Checkov Security Scan
        uses: bridgecrewio/checkov-action@v12
        with:
          directory: terraform/
          framework: terraform
          soft_fail: false

      - name: tfsec Security Scan
        uses: aquasecurity/tfsec-action@v1.0.3
        with:
          working_directory: terraform/

  unit-tests:
    name: Unit Tests
    runs-on: ubuntu-latest
    needs: static-analysis
    steps:
      - uses: actions/checkout@v4

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}

      - name: Run Terraform Tests
        run: |
          cd terraform/modules/vpc
          terraform init -backend=false
          terraform test

  policy-tests:
    name: Policy Tests
    runs-on: ubuntu-latest
    needs: static-analysis
    steps:
      - uses: actions/checkout@v4

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}

      - name: Generate Plan
        run: |
          cd terraform/environments/dev
          terraform init -backend=false
          terraform plan -out=tfplan
          terraform show -json tfplan > tfplan.json
        env:
          # Use mock credentials for plan
          AWS_ACCESS_KEY_ID: mock
          AWS_SECRET_ACCESS_KEY: mock

      - name: Install Conftest
        run: |
          wget https://github.com/open-policy-agent/conftest/releases/download/v0.45.0/conftest_0.45.0_Linux_x86_64.tar.gz
          tar xzf conftest_0.45.0_Linux_x86_64.tar.gz
          sudo mv conftest /usr/local/bin/

      - name: Run Policy Tests
        run: |
          conftest test terraform/environments/dev/tfplan.json \
            --policy policy/

  integration-tests:
    name: Integration Tests
    runs-on: ubuntu-latest
    needs: [unit-tests, policy-tests]
    # Only run on main branch or when label is added
    if: github.ref == 'refs/heads/main' || contains(github.event.pull_request.labels.*.name, 'run-integration-tests')
    steps:
      - uses: actions/checkout@v4

      - name: Setup Go
        uses: actions/setup-go@v4
        with:
          go-version: ${{ env.GO_VERSION }}

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}
          terraform_wrapper: false

      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: us-east-1

      - name: Run Integration Tests
        run: |
          cd test
          go test -v -timeout 30m -run TestVPCModule
        env:
          # Limit parallelism to avoid rate limits
          TF_CLI_ARGS: "-parallelism=5"

  e2e-tests:
    name: E2E Tests
    runs-on: ubuntu-latest
    needs: integration-tests
    # Only run on main branch merges
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4

      - name: Setup Go
        uses: actions/setup-go@v4
        with:
          go-version: ${{ env.GO_VERSION }}

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}
          terraform_wrapper: false

      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: us-east-1

      - name: Run E2E Tests
        run: |
          cd test
          go test -v -timeout 60m -run TestFullEnvironment
```

---

## War Story: The $3.8 Million Testing Gap

**Company**: Global logistics company
**Incident**: Complete production outage during Black Friday

**Timeline**:
- **T-30 days**: Team decides to migrate from self-managed Kubernetes to EKS
- **T-14 days**: Terraform modules written, manually tested in dev environment
- **T-7 days**: Migration proceeds to staging, "looks good"
- **T-1 day**: Production migration scheduled for Black Friday eve
- **T+0**: Migration starts at 2 AM
- **T+2 hours**: EKS cluster created, but nodes won't join
- **T+4 hours**: Discovered - security group rules reference wrong VPC
- **T+6 hours**: Manual fix applied, nodes joining
- **T+8 hours**: Application won't start - IAM roles have wrong trust policy
- **T+10 hours**: Black Friday begins, system still unstable
- **T+12 hours**: Full rollback to old infrastructure
- **Total downtime**: 8 hours during peak shopping period

**Root Cause Analysis**:
```
Why did nodes not join?
└── Security group referenced wrong VPC
    └── Why? Terraform variable interpolation error
        └── Why not caught? No security group connectivity tests
            └── Why no tests? "Manual testing in dev was enough"
                └── Why different in prod? Environment-specific naming conventions

Why did IAM roles fail?
└── Trust policy had wrong OIDC provider URL
    └── Why? Copy-paste from documentation example
        └── Why not caught? No IAM policy validation tests
            └── Why no tests? "IAM is too complex to test"
```

**Financial Impact**:
- Lost revenue (8 hours Black Friday): $3.2M
- Emergency consulting fees: $180K
- Overtime and incident response: $85K
- Customer compensation: $340K
- **Total**: $3.8M

**Tests That Would Have Caught This**:

```go
// test/eks_test.go - Would have caught both issues

func TestEKSNodeConnectivity(t *testing.T) {
    terraformOptions := &terraform.Options{
        TerraformDir: "../modules/eks",
        Vars: map[string]interface{}{
            "environment": "test",
        },
    }

    defer terraform.Destroy(t, terraformOptions)
    terraform.InitAndApply(t, terraformOptions)

    // Test 1: Verify security group allows node communication
    sgID := terraform.Output(t, terraformOptions, "node_security_group_id")
    vpcID := terraform.Output(t, terraformOptions, "vpc_id")

    sg := aws.GetSecurityGroup(t, sgID, "us-east-1")
    assert.Equal(t, vpcID, sg.VpcId,
                "Security group must be in correct VPC")

    // Test 2: Verify nodes can actually join
    eksClusterName := terraform.Output(t, terraformOptions, "cluster_name")

    // Wait for nodes to join (with timeout)
    maxRetries := 30
    for i := 0; i < maxRetries; i++ {
        nodes := getEKSNodes(t, eksClusterName)
        if len(nodes) >= 2 {
            return // Success
        }
        time.Sleep(30 * time.Second)
    }
    t.Fatal("Nodes did not join cluster within timeout")
}

func TestIAMRoleTrustPolicy(t *testing.T) {
    terraformOptions := &terraform.Options{
        TerraformDir: "../modules/eks",
    }

    defer terraform.Destroy(t, terraformOptions)
    terraform.InitAndApply(t, terraformOptions)

    // Verify OIDC provider URL matches cluster
    oidcURL := terraform.Output(t, terraformOptions, "oidc_provider_url")
    roleARN := terraform.Output(t, terraformOptions, "node_role_arn")

    role := aws.GetIAMRole(t, roleARN)
    trustPolicy := parseTrustPolicy(role.AssumeRolePolicyDocument)

    // Trust policy should reference our OIDC provider
    assert.Contains(t, trustPolicy.Statement[0].Principal.Federated, oidcURL,
                   "Trust policy must reference correct OIDC provider")
}
```

**Aftermath**: The team implemented:
- Mandatory integration tests for all infrastructure changes
- Contract tests between modules
- E2E tests that verify node joining and application startup
- Test coverage requirements (minimum 80% for critical modules)

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Testing only happy paths | Edge cases cause production issues | Test failure scenarios, invalid inputs, boundary conditions |
| No cleanup in tests | Orphaned resources accumulate costs | Always use `defer terraform.Destroy()` |
| Hardcoded values in tests | Tests aren't portable | Use variables, random unique IDs |
| Testing implementation not behavior | Tests break on refactoring | Test outputs and behavior, not internal structure |
| Skipping integration tests | "Too slow/expensive" | Run on merge to main, use ephemeral environments |
| Not testing idempotency | Apply twice causes drift | Always test multiple applies |
| Testing in production account | Risk and cost | Use dedicated testing account with spending limits |
| No test parallelization | Slow feedback loops | Use `t.Parallel()`, parallel-friendly naming |

---

## Quiz

Test your understanding of IaC testing:

<details>
<summary>1. What is the primary purpose of static analysis in IaC testing?</summary>

**Answer**: Static analysis catches syntax errors, formatting issues, security misconfigurations, and policy violations without executing any code or creating real infrastructure. It provides immediate feedback (milliseconds) and should run on every commit. Examples include `terraform fmt`, `terraform validate`, TFLint, Checkov, and tfsec.
</details>

<details>
<summary>2. Why is idempotency testing important for Terraform?</summary>

**Answer**: Idempotency testing verifies that applying the same configuration multiple times produces the same result with no changes on subsequent applies. This is critical because:
- Terraform state might drift from reality
- Some resources may have default values that differ from explicit ones
- Data sources might return different values
- Provider bugs might cause phantom changes

A non-idempotent configuration can cause unexpected resource replacements or failures during routine applies.
</details>

<details>
<summary>3. What's the difference between unit tests and integration tests for IaC?</summary>

**Answer**:
- **Unit tests** verify individual resources and modules in isolation, typically using mock providers or plan-only commands. They run in seconds, don't create real infrastructure, and catch logic errors.
- **Integration tests** create real infrastructure in a cloud provider to verify it actually works. They run in minutes, cost money, and catch provider-specific issues, API limitations, and real-world problems that mocks can't simulate.
</details>

<details>
<summary>4. Calculate the testing pyramid ratio for a well-balanced IaC test suite with 100 total tests.</summary>

**Answer**: A well-balanced IaC testing pyramid might look like:
- **Static Analysis**: 40 tests (40%) - formatting, linting, security scans, policy checks
- **Unit Tests**: 35 tests (35%) - individual resource validation, variable constraints
- **Contract Tests**: 15 tests (15%) - module interface verification
- **Integration Tests**: 8 tests (8%) - real infrastructure deployment
- **E2E Tests**: 2 tests (2%) - full environment validation

This ratio ensures fast feedback for most changes while still catching real-world issues.
</details>

<details>
<summary>5. What is a contract test in the context of IaC modules?</summary>

**Answer**: A contract test verifies that the outputs of one module match the expected inputs of modules that consume it. For example, if a VPC module outputs `vpc_id` and an EKS module expects a `vpc_id` input that starts with "vpc-", the contract test verifies this interface. Contract tests catch integration issues early without deploying full environments.
</details>

<details>
<summary>6. Why should you use `defer terraform.Destroy()` in Go-based integration tests?</summary>

**Answer**: `defer terraform.Destroy()` ensures resources are cleaned up even if the test fails or panics. Without it:
- Failed tests leave orphaned resources
- Cloud costs accumulate
- Resource limits may be exceeded
- Subsequent tests may fail due to naming conflicts

The `defer` statement guarantees cleanup runs regardless of how the test exits.
</details>

<details>
<summary>7. A team has 94% code coverage on application tests but zero IaC tests. Their Terraform manages $50M in annual infrastructure. What testing strategy would you recommend implementing first?</summary>

**Answer**: Recommended priority order:
1. **Static analysis (Week 1)**: Implement pre-commit hooks with `terraform fmt`, `terraform validate`, and Checkov. Zero cost, immediate value.
2. **Policy tests (Week 2)**: Add Conftest/OPA policies for critical rules (encryption, no public access, required tags).
3. **Unit tests (Week 3-4)**: Add Terraform native tests for critical modules (VPC, IAM, security groups).
4. **Contract tests (Week 5-6)**: Define and test module interfaces.
5. **Integration tests (Week 7-8)**: Add Terratest for VPC connectivity, security group rules, IAM permissions.
6. **E2E tests (Week 9+)**: Full environment deployment tests before major releases.

This order maximizes value while building testing infrastructure incrementally.
</details>

<details>
<summary>8. What is the purpose of mock providers in Terraform testing?</summary>

**Answer**: Mock providers allow testing Terraform configurations without:
- Cloud provider credentials
- Real API calls (which are slow and rate-limited)
- Creating actual resources (which cost money)
- Network connectivity

Mock providers return predictable, controllable values, enabling fast unit tests that verify logic without external dependencies. They're particularly useful for testing variable validation, conditional resource creation, and output formatting.
</details>

---

## Hands-On Exercise

**Objective**: Implement a complete testing pipeline for a VPC module.

### Part 1: Static Analysis Setup

```bash
# Create project structure
mkdir -p terraform-testing-lab/{modules/vpc,test,policy}
cd terraform-testing-lab

# Create VPC module
cat > modules/vpc/main.tf << 'EOF'
variable "environment" {
  description = "Environment name"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod"
  }
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"

  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "VPC CIDR must be a valid CIDR block"
  }
}

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "${var.environment}-vpc"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name        = "${var.environment}-private-${count.index + 1}"
    Environment = var.environment
    Type        = "private"
  }
}

data "aws_availability_zones" "available" {
  state = "available"
}

output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "private_subnet_ids" {
  description = "IDs of private subnets"
  value       = aws_subnet.private[*].id
}
EOF

# Create pre-commit config
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/antonbabenko/pre-commit-terraform
    rev: v1.83.5
    hooks:
      - id: terraform_fmt
      - id: terraform_validate
      - id: terraform_tflint
      - id: terraform_checkov
EOF

# Install and run pre-commit
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

### Part 2: Unit Tests

```bash
# Create Terraform test file
cat > modules/vpc/tests/vpc_test.tftest.hcl << 'EOF'
variables {
  environment = "dev"
  vpc_cidr    = "10.0.0.0/16"
}

run "valid_environment" {
  command = plan

  assert {
    condition     = aws_vpc.main.tags["Environment"] == "dev"
    error_message = "Environment tag should be dev"
  }
}

run "invalid_environment_fails" {
  command = plan

  variables {
    environment = "invalid"
  }

  expect_failures = [var.environment]
}

run "subnet_count" {
  command = plan

  assert {
    condition     = length(aws_subnet.private) == 2
    error_message = "Should create 2 private subnets"
  }
}
EOF

# Run tests
cd modules/vpc
terraform init -backend=false
terraform test
```

### Part 3: Policy Tests

```bash
# Create OPA policy
cat > policy/terraform.rego << 'EOF'
package terraform

deny[msg] {
  resource := input.resource_changes[_]
  resource.type == "aws_vpc"
  not resource.change.after.tags.ManagedBy
  msg := sprintf("VPC %s must have ManagedBy tag", [resource.address])
}

deny[msg] {
  resource := input.resource_changes[_]
  resource.type == "aws_subnet"
  not resource.change.after.tags.Type
  msg := sprintf("Subnet %s must have Type tag", [resource.address])
}
EOF

# Generate plan and test
terraform plan -out=tfplan
terraform show -json tfplan > tfplan.json
conftest test tfplan.json --policy ../../../policy/
```

### Success Criteria

- [ ] Pre-commit hooks run on every commit
- [ ] All static analysis checks pass
- [ ] Terraform unit tests pass
- [ ] Policy tests validate tagging requirements
- [ ] Invalid inputs are rejected with clear error messages

---

## Key Takeaways

- [ ] **IaC testing follows a pyramid** - More fast/cheap tests, fewer slow/expensive ones
- [ ] **Static analysis catches 70%+ of issues** - Run on every commit with pre-commit hooks
- [ ] **Unit tests verify logic without cloud access** - Use Terraform's native test framework
- [ ] **Contract tests catch integration issues early** - Verify module interfaces match
- [ ] **Integration tests create real infrastructure** - Essential but expensive, run selectively
- [ ] **Always test idempotency** - Apply twice, expect no changes
- [ ] **Clean up after tests** - Use `defer` to avoid orphaned resources
- [ ] **Test failure scenarios** - Invalid inputs, edge cases, upgrade paths
- [ ] **Automate in CI/CD** - Fast tests on every PR, integration tests on merge
- [ ] **No IaC tests = no safety net** - Treat infrastructure code like application code

---

## Did You Know?

> **Testing Pioneer**: HashiCorp added native testing to Terraform in version 1.6 (2023) after years of community demand. Before this, teams had to use external tools like Terratest, Kitchen-Terraform, or custom scripts.

> **Cost of Testing vs. Not Testing**: A 2023 study found that companies with comprehensive IaC testing had 73% fewer production incidents and 89% faster recovery times compared to those with manual testing only.

> **Mock Provider Origins**: The mock provider feature in Terraform testing was inspired by unit testing patterns from traditional software development, where mocking external dependencies has been standard practice since the 1990s.

> **Terratest Statistics**: Gruntwork's Terratest framework has been used to test over 1 million infrastructure deployments, catching issues that would have cost an estimated $2.3 billion in downtime and remediation.

---

## Next Module

Continue to [Module 6.3: IaC Security](module-6.3-iac-security/) to learn about security scanning, secrets management, and compliance automation in infrastructure as code.

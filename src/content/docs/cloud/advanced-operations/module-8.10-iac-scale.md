---
title: "Module 8.10: Scaling IaC & State Management"
slug: cloud/advanced-operations/module-8.10-iac-scale
sidebar:
  order: 11
---
> **Complexity**: `[MEDIUM]`
>
> **Time to Complete**: 2 hours
>
> **Prerequisites**: Basic Terraform experience (variables, modules, state), familiarity with Git workflows
>
> **Track**: Advanced Cloud Operations

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Design Terraform or Pulumi state management strategies for large-scale multi-account infrastructure**
- **Implement modular IaC patterns with versioned modules, workspace isolation, and policy-as-code validation**
- **Configure automated drift detection and remediation pipelines for infrastructure managed by Terraform or CloudFormation**
- **Evaluate IaC tools (Terraform, Pulumi, CloudFormation, Bicep, Crossplane) for multi-cloud Kubernetes platform engineering**

---

## Why This Module Matters

**May 2023. A platform engineering team at a logistics company. 280 Terraform resources. One state file.**

A routine `terraform plan` took 12 minutes. A `terraform apply` for a single security group change took 18 minutes because Terraform refreshed the state of all 280 resources before making one change. The team had adopted Terraform early, put everything in one root module, and never refactored. The state file was 45MB of JSON. Merging pull requests was a nightmare because two engineers running `terraform apply` simultaneously could corrupt the state file. The team had experienced three state corruption incidents in six months, each requiring manual state surgery with `terraform state rm` and `terraform import`.

The breaking point came during a production incident. A load balancer needed a target group update. The engineer ran `terraform apply`. Twelve minutes of state refresh. During those twelve minutes, the incident escalated from P2 to P1. The engineer resorted to making the change manually in the AWS console -- which worked immediately but introduced drift that broke the next Terraform run.

This module teaches you how to structure Terraform (and other IaC tools) for scale: how to split state files to keep operations fast, how to design reusable modules for Kubernetes infrastructure, how to bridge IaC with GitOps (Crossplane vs. Terraform Operator), and how to detect and prevent configuration drift. These are the patterns that let platform teams manage hundreds of resources across dozens of accounts without drowning in state files.

---

## The State File Problem

Terraform state is the mapping between your configuration files and real infrastructure. Every resource you manage adds to the state file. As the state grows, every operation slows down because Terraform refreshes the entire state before making changes.

```
STATE FILE GROWTH AND ITS CONSEQUENCES
════════════════════════════════════════════════════════════════

Resources   State Size   Plan Time    Apply Time   Risk
────────────────────────────────────────────────────────────
10          ~100KB       5 sec        30 sec       Low
50          ~500KB       30 sec       2 min        Low
100         ~2MB         2 min        5 min        Medium
250         ~10MB        8 min        15 min       High
500         ~30MB        15 min       25 min       Very High
1000+       ~100MB+      30+ min      45+ min      Extreme

At 250+ resources, you WILL experience:
- Slow plans blocking CI/CD pipelines
- State lock timeouts
- Team members waiting to apply changes
- Temptation to make manual changes (drift)
- State corruption from concurrent operations
```

### State Splitting Strategy

The solution is to split your Terraform configuration into multiple independent state files, each managing a logical group of resources.

```
STATE SPLITTING ARCHITECTURE
════════════════════════════════════════════════════════════════

BEFORE (monolith):
  terraform/
  └── main.tf          # 280 resources, one state file
      ├── VPC
      ├── Subnets
      ├── EKS cluster
      ├── Node groups
      ├── RDS
      ├── ElastiCache
      ├── S3 buckets
      ├── IAM roles
      ├── Route53
      └── CloudWatch

AFTER (split by concern):
  terraform/
  ├── networking/       # 30 resources, own state
  │   ├── vpc.tf
  │   ├── subnets.tf
  │   ├── transit-gw.tf
  │   └── outputs.tf    # VPC ID, subnet IDs exported
  │
  ├── eks-cluster/      # 25 resources, own state
  │   ├── cluster.tf
  │   ├── node-groups.tf
  │   ├── addons.tf
  │   └── data.tf       # Reads networking outputs
  │
  ├── databases/        # 20 resources, own state
  │   ├── rds.tf
  │   ├── elasticache.tf
  │   └── data.tf       # Reads networking outputs
  │
  ├── iam/              # 40 resources, own state
  │   ├── roles.tf
  │   ├── policies.tf
  │   └── irsa.tf
  │
  └── dns/              # 15 resources, own state
      ├── zones.tf
      └── records.tf

  Each directory: independent terraform init, plan, apply
  Each has ~20-40 resources: plans take seconds, not minutes
```

### Remote State Data Sources

Split state files need to reference each other. Use `terraform_remote_state` or data sources.

```hcl
# networking/outputs.tf -- Export values from networking state
output "vpc_id" {
  value = aws_vpc.main.id
}

output "private_subnet_ids" {
  value = aws_subnet.private[*].id
}

output "eks_security_group_id" {
  value = aws_security_group.eks.id
}

# eks-cluster/data.tf -- Read from networking state
data "terraform_remote_state" "networking" {
  backend = "s3"
  config = {
    bucket = "company-terraform-state"
    key    = "networking/terraform.tfstate"
    region = "us-east-1"
  }
}

# eks-cluster/cluster.tf -- Use the imported values
resource "aws_eks_cluster" "main" {
  name     = "prod-cluster"
  role_arn = aws_iam_role.eks.arn

  vpc_config {
    subnet_ids         = data.terraform_remote_state.networking.outputs.private_subnet_ids
    security_group_ids = [data.terraform_remote_state.networking.outputs.eks_security_group_id]
  }
}
```

### Better Alternative: Use Data Sources Instead of Remote State

```hcl
# Instead of remote state, query AWS directly
# This avoids tight coupling between state files

data "aws_vpc" "main" {
  tags = {
    Name        = "production-vpc"
    Environment = "production"
  }
}

data "aws_subnets" "private" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.main.id]
  }
  tags = {
    Tier = "private"
  }
}

resource "aws_eks_cluster" "main" {
  name     = "prod-cluster"
  role_arn = aws_iam_role.eks.arn

  vpc_config {
    subnet_ids = data.aws_subnets.private.ids
  }
}
```

---

## Remote Backends and State Locking

```
REMOTE BACKEND WITH LOCKING
════════════════════════════════════════════════════════════════

  Engineer A                    Engineer B
  terraform apply               terraform apply
       │                              │
       ▼                              ▼
  ┌────────────────┐           ┌────────────────┐
  │ Lock state     │           │ Lock state     │
  │ (DynamoDB)     │           │ (DynamoDB)     │
  │ SUCCESS        │           │ FAILED: locked │
  └────────┬───────┘           │ "State locked  │
           │                   │  by Engineer A" │
           ▼                   └────────────────┘
  ┌────────────────┐
  │ Read state     │
  │ (S3 bucket)    │
  │                │
  │ Apply changes  │
  │                │
  │ Write state    │
  │ (S3 bucket)    │
  │                │
  │ Release lock   │
  └────────────────┘
```

```hcl
# Backend configuration (per-state-file)
terraform {
  backend "s3" {
    bucket         = "company-terraform-state"
    key            = "prod/us-east-1/networking/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    kms_key_id     = "alias/terraform-state"
    dynamodb_table = "terraform-state-lock"
  }
}

# Create the DynamoDB lock table (one-time setup)
# aws dynamodb create-table \
#   --table-name terraform-state-lock \
#   --attribute-definitions AttributeName=LockID,AttributeType=S \
#   --key-schema AttributeName=LockID,KeyType=HASH \
#   --billing-mode PAY_PER_REQUEST
```

### State File Organization Pattern

```
S3 BUCKET STRUCTURE FOR TERRAFORM STATE
════════════════════════════════════════════════════════════════

s3://company-terraform-state/
├── global/
│   ├── iam/terraform.tfstate
│   ├── dns/terraform.tfstate
│   └── organizations/terraform.tfstate
│
├── prod/
│   ├── us-east-1/
│   │   ├── networking/terraform.tfstate
│   │   ├── eks-cluster/terraform.tfstate
│   │   ├── databases/terraform.tfstate
│   │   └── monitoring/terraform.tfstate
│   │
│   └── eu-west-1/
│       ├── networking/terraform.tfstate
│       ├── eks-cluster/terraform.tfstate
│       └── databases/terraform.tfstate
│
├── staging/
│   └── us-east-1/
│       ├── networking/terraform.tfstate
│       └── eks-cluster/terraform.tfstate
│
└── sandbox/
    └── terraform.tfstate

Key/path structure: {env}/{region}/{component}/terraform.tfstate
This matches your OU structure from Module 8.1.
```

---

## Terraform Modules for Kubernetes Clusters

Well-designed modules are the building blocks for managing Kubernetes infrastructure at scale. A good module encapsulates a logical unit of infrastructure with a clean interface.

### EKS Cluster Module

```hcl
# modules/eks-cluster/variables.tf
variable "cluster_name" {
  type        = string
  description = "Name of the EKS cluster"
}

variable "cluster_version" {
  type        = string
  description = "Kubernetes version"
  default     = "1.35"
}

variable "vpc_id" {
  type        = string
  description = "VPC ID where the cluster will be created"
}

variable "subnet_ids" {
  type        = list(string)
  description = "Subnet IDs for the cluster (private subnets)"
}

variable "node_groups" {
  type = map(object({
    instance_types = list(string)
    desired_size   = number
    min_size       = number
    max_size       = number
    capacity_type  = optional(string, "ON_DEMAND")
    labels         = optional(map(string), {})
    taints = optional(list(object({
      key    = string
      value  = string
      effect = string
    })), [])
  }))
  description = "Node group configurations"
}

variable "enable_karpenter" {
  type        = bool
  default     = true
  description = "Install Karpenter for autoscaling"
}

variable "cluster_addons" {
  type = map(object({
    version = optional(string)
  }))
  default = {
    vpc-cni            = {}
    coredns            = {}
    kube-proxy         = {}
    aws-ebs-csi-driver = {}
  }
}

variable "tags" {
  type    = map(string)
  default = {}
}
```

```hcl
# modules/eks-cluster/main.tf
resource "aws_eks_cluster" "this" {
  name     = var.cluster_name
  version  = var.cluster_version
  role_arn = aws_iam_role.cluster.arn

  vpc_config {
    subnet_ids              = var.subnet_ids
    endpoint_private_access = true
    endpoint_public_access  = false
    security_group_ids      = [aws_security_group.cluster.id]
  }

  access_config {
    authentication_mode                         = "API_AND_CONFIG_MAP"
    bootstrap_cluster_creator_admin_permissions = true
  }

  encryption_config {
    provider {
      key_arn = aws_kms_key.eks.arn
    }
    resources = ["secrets"]
  }

  tags = merge(var.tags, {
    "kubernetes.io/cluster/${var.cluster_name}" = "owned"
  })

  depends_on = [
    aws_iam_role_policy_attachment.cluster_policy,
    aws_iam_role_policy_attachment.cluster_vpc_policy,
  ]
}

resource "aws_eks_node_group" "this" {
  for_each = var.node_groups

  cluster_name    = aws_eks_cluster.this.name
  node_group_name = each.key
  node_role_arn   = aws_iam_role.node.arn
  subnet_ids      = var.subnet_ids
  instance_types  = each.value.instance_types
  capacity_type   = each.value.capacity_type

  scaling_config {
    desired_size = each.value.desired_size
    min_size     = each.value.min_size
    max_size     = each.value.max_size
  }

  labels = merge(each.value.labels, {
    "node-group" = each.key
  })

  dynamic "taint" {
    for_each = each.value.taints
    content {
      key    = taint.value.key
      value  = taint.value.value
      effect = taint.value.effect
    }
  }

  tags = var.tags
}

# EKS addons
resource "aws_eks_addon" "this" {
  for_each = var.cluster_addons

  cluster_name                = aws_eks_cluster.this.name
  addon_name                  = each.key
  addon_version               = each.value.version
  resolve_conflicts_on_create = "OVERWRITE"
  resolve_conflicts_on_update = "PRESERVE"
}
```

```hcl
# modules/eks-cluster/outputs.tf
output "cluster_name" {
  value = aws_eks_cluster.this.name
}

output "cluster_endpoint" {
  value = aws_eks_cluster.this.endpoint
}

output "cluster_ca_certificate" {
  value = aws_eks_cluster.this.certificate_authority[0].data
}

output "oidc_provider_arn" {
  value = aws_iam_openid_connect_provider.eks.arn
}

output "oidc_provider_url" {
  value = aws_eks_cluster.this.identity[0].oidc[0].issuer
}

output "node_security_group_id" {
  value = aws_eks_cluster.this.vpc_config[0].cluster_security_group_id
}
```

### Using the Module

```hcl
# environments/prod/us-east-1/eks-cluster/main.tf
module "eks" {
  source = "../../../../modules/eks-cluster"

  cluster_name    = "prod-us-east-1"
  cluster_version = "1.35"
  vpc_id          = data.aws_vpc.prod.id
  subnet_ids      = data.aws_subnets.private.ids

  node_groups = {
    general = {
      instance_types = ["m7i.xlarge"]
      desired_size   = 3
      min_size       = 3
      max_size       = 10
      capacity_type  = "ON_DEMAND"
      labels = {
        "workload-class" = "general"
      }
    }

    spot-workers = {
      instance_types = ["m7i.xlarge", "m6i.xlarge", "c7i.xlarge"]
      desired_size   = 5
      min_size       = 2
      max_size       = 20
      capacity_type  = "SPOT"
      labels = {
        "workload-class" = "batch"
        "node-type"      = "spot"
      }
      taints = [
        {
          key    = "spot"
          value  = "true"
          effect = "NO_SCHEDULE"
        }
      ]
    }
  }

  enable_karpenter = true

  tags = {
    Environment = "production"
    Team        = "platform"
    CostCenter  = "CC-1000"
  }
}
```

---

## IaC + GitOps: Crossplane vs. Terraform Operator

The traditional model is: Terraform manages cloud infrastructure, GitOps (ArgoCD/Flux) manages Kubernetes workloads. But there is a growing movement to manage cloud infrastructure through Kubernetes itself, using Crossplane or the Terraform Operator.

```
IAC + GITOPS MODELS
════════════════════════════════════════════════════════════════

MODEL 1: Traditional (Terraform + GitOps)
  Git Repo ──▶ CI Pipeline ──▶ terraform apply ──▶ Cloud Resources
  Git Repo ──▶ ArgoCD ──────▶ kubectl apply ──▶ K8s Resources

  Pros: Mature, well-understood, terraform plan in PR
  Cons: Two tools, two workflows, two state systems

MODEL 2: Crossplane (Everything is K8s)
  Git Repo ──▶ ArgoCD ──▶ Crossplane CRDs ──▶ Cloud + K8s Resources

  Pros: Single GitOps workflow, K8s-native, reconciliation loop
  Cons: Newer, fewer providers, debugging is harder

MODEL 3: Terraform Operator (Terraform inside K8s)
  Git Repo ──▶ ArgoCD ──▶ TF Operator CRD ──▶ terraform apply
                                                ──▶ Cloud Resources

  Pros: Uses existing TF modules, K8s-native workflow
  Cons: State management complexity, TF inside K8s adds a layer
```

### Crossplane Example

```yaml
# Create an RDS instance using Crossplane
apiVersion: rds.aws.upbound.io/v1beta2
kind: Instance
metadata:
  name: payments-db
  namespace: crossplane-system
spec:
  forProvider:
    region: us-east-1
    instanceClass: db.r7g.large
    engine: postgres
    engineVersion: "16"
    allocatedStorage: 100
    storageType: gp3
    dbName: payments
    masterUsername: admin
    masterPasswordSecretRef:
      name: rds-password
      namespace: crossplane-system
      key: password
    vpcSecurityGroupIds:
      - sg-abc123
    dbSubnetGroupName: prod-db-subnets
    publiclyAccessible: false
    backupRetentionPeriod: 14
    multiAz: true
    tags:
      Environment: production
      Team: payments
      CostCenter: CC-2000
  providerConfigRef:
    name: aws-provider
---
# The Crossplane controller continuously reconciles:
# If someone changes the RDS instance in the console,
# Crossplane will revert it to match this spec.
# This is drift detection + correction built in.
```

### When to Use Each Approach

| Factor | Terraform | Crossplane | TF Operator |
|---|---|---|---|
| Existing TF codebase | Keep Terraform | Consider migration | Use TF Operator |
| Team skill set | TF experts | K8s experts | TF experts |
| Cloud resource coverage | Excellent (all providers) | Good (growing) | Uses TF providers |
| Drift correction | Manual (`terraform apply`) | Automatic (reconciliation) | Periodic (`terraform apply`) |
| State management | S3 + DynamoDB | etcd (K8s) | S3 + DynamoDB |
| PR workflow | `terraform plan` in PR | `kubectl diff` in PR | `terraform plan` in PR |
| Multi-cloud | Excellent | Good | Excellent |

---

## Drift Detection

Configuration drift occurs when the actual state of infrastructure diverges from the desired state in code. Someone makes a manual change in the console. An automated process modifies a resource. A provider update changes a default value.

### Detecting Drift

```bash
# Terraform: Detect drift with refresh-only plan
terraform plan -refresh-only

# Expected output when drift exists:
# Note: Objects have changed outside of Terraform
#
# Terraform detected the following changes made outside of Terraform
# since the last "terraform apply":
#
#   # aws_security_group.eks has been changed
#   ~ resource "aws_security_group" "eks" {
#       ~ ingress {
#           + cidr_blocks = ["0.0.0.0/0"]  <-- SOMEONE OPENED THIS TO THE WORLD
#         }
#     }

# Run drift detection on a schedule (CI/CD)
# GitHub Actions example:
```

```yaml
# .github/workflows/drift-detection.yml
name: Terraform Drift Detection
on:
  schedule:
    - cron: '0 6 * * *'  # Daily at 6 AM UTC
  workflow_dispatch:

jobs:
  detect-drift:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        component:
          - networking
          - eks-cluster
          - databases
          - iam
    steps:
      - uses: actions/checkout@v4

      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.9.0

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::111111111111:role/terraform-drift-detector
          aws-region: us-east-1

      - name: Terraform Init
        working-directory: terraform/prod/us-east-1/${{ matrix.component }}
        run: terraform init -input=false

      - name: Detect Drift
        id: drift
        working-directory: terraform/prod/us-east-1/${{ matrix.component }}
        run: |
          terraform plan -refresh-only -detailed-exitcode -input=false 2>&1 | tee plan.txt
          EXIT_CODE=${PIPESTATUS[0]}
          if [ $EXIT_CODE -eq 2 ]; then
            echo "drift_detected=true" >> $GITHUB_OUTPUT
            echo "DRIFT DETECTED in ${{ matrix.component }}"
          elif [ $EXIT_CODE -eq 0 ]; then
            echo "drift_detected=false" >> $GITHUB_OUTPUT
            echo "No drift in ${{ matrix.component }}"
          else
            echo "Error running terraform plan"
            exit 1
          fi

      - name: Alert on Drift
        if: steps.drift.outputs.drift_detected == 'true'
        run: |
          curl -X POST "${{ secrets.SLACK_WEBHOOK }}" \
            -H 'Content-type: application/json' \
            --data "{
              \"text\": \"DRIFT DETECTED in terraform/prod/us-east-1/${{ matrix.component }}\nRun terraform plan to see details.\"
            }"
```

---

## Terratest: Testing Infrastructure Code

Terratest is a Go library that writes automated tests for Terraform modules. It deploys real infrastructure, validates it, and tears it down.

```go
// test/eks_cluster_test.go
package test

import (
    "testing"
    "time"

    "github.com/gruntwork-io/terratest/modules/aws"
    "github.com/gruntwork-io/terratest/modules/k8s"
    "github.com/gruntwork-io/terratest/modules/terraform"
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"
)

func TestEksCluster(t *testing.T) {
    t.Parallel()

    terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
        TerraformDir: "../modules/eks-cluster",
        Vars: map[string]interface{}{
            "cluster_name":    "test-cluster-" + time.Now().Format("20060102150405"),
            "cluster_version": "1.35",
            "vpc_id":          "vpc-test123",
            "subnet_ids":      []string{"subnet-a", "subnet-b"},
            "node_groups": map[string]interface{}{
                "test": map[string]interface{}{
                    "instance_types": []string{"t3.medium"},
                    "desired_size":   1,
                    "min_size":       1,
                    "max_size":       2,
                    "capacity_type":  "SPOT",
                },
            },
        },
    })

    // Clean up at the end
    defer terraform.Destroy(t, terraformOptions)

    // Deploy the module
    terraform.InitAndApply(t, terraformOptions)

    // Validate outputs
    clusterName := terraform.Output(t, terraformOptions, "cluster_name")
    assert.Contains(t, clusterName, "test-cluster-")

    clusterEndpoint := terraform.Output(t, terraformOptions, "cluster_endpoint")
    assert.NotEmpty(t, clusterEndpoint)

    // Validate the cluster is actually functional
    kubeconfig := aws.GetKubeConfigForEksCluster(t, clusterName, "us-east-1")

    options := k8s.NewKubectlOptions("", kubeconfig, "default")

    // Check that nodes are ready
    nodes := k8s.GetNodes(t, options)
    require.GreaterOrEqual(t, len(nodes), 1)

    for _, node := range nodes {
        for _, condition := range node.Status.Conditions {
            if condition.Type == "Ready" {
                assert.Equal(t, "True", string(condition.Status))
            }
        }
    }

    // Check that core addons are running
    k8s.WaitUntilDeploymentAvailable(t, options, "coredns", 5, 30*time.Second)
}
```

```bash
# Run Terratest
cd test/
go test -v -timeout 30m -run TestEksCluster
```

---

## Did You Know?

1. **Terraform state files have caused more production incidents than Terraform configurations** according to a 2024 survey by Spacelift. The most common state-related incidents are: state corruption from concurrent applies (31%), state lock not released after a failed apply (28%), sensitive data exposed in state files (22%), and state lost due to backend misconfiguration (19%). This is why state management is not an afterthought -- it is the most operationally critical aspect of Terraform.

2. **Crossplane has over 200 managed resource types for AWS alone** as of 2025, covering the most commonly used services (EKS, RDS, S3, IAM, VPC, Lambda, DynamoDB, and many more). However, it still has gaps compared to Terraform's AWS provider, which covers over 1,200 resource types. The gap is closing -- the Upbound Marketplace now generates Crossplane providers directly from Terraform providers using a tool called upjet.

3. **The average Terraform module in the public registry has 2.3 variables that are never used** according to an analysis by Bridgecrew/Prisma Cloud. Module bloat is a real problem: teams copy modules from the registry, add variables for every possible configuration, and end up with modules that are harder to understand than raw resources. The best modules have 5-10 input variables with sensible defaults, not 50+ variables that try to cover every edge case.

4. **HashiCorp changed Terraform's license from Mozilla Public License 2.0 to Business Source License (BSL) in August 2023**, which triggered the creation of OpenTofu -- a community-maintained fork under the Linux Foundation. As of 2025, both projects continue active development with diverging feature sets. OpenTofu added client-side state encryption (a long-requested feature) before HashiCorp, while Terraform added native testing and ephemeral values. Most organizations continue using Terraform, but the fork ensures that an open-source alternative exists.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---|---|---|
| One monolithic state file for everything | "It started small and grew" | Split by concern: networking, compute, databases, IAM. Each component in its own directory with its own state. Do this early -- splitting later is painful. |
| Not using state locking | "We'll coordinate manually" | Always use DynamoDB (AWS), GCS (GCP), or Blob Storage (Azure) for locking. Without locking, concurrent applies WILL corrupt state. |
| Storing secrets in state | "It's encrypted at rest" | Terraform state contains plaintext values of all managed resources, including passwords. Use separate secret management (Vault, AWS Secrets Manager) and reference secrets by ARN, not value. |
| Writing modules that are too generic | "We'll configure everything through variables" | Write modules for YOUR use case. A module with 50 variables is worse than raw resources. Start specific, generalize only when you have three proven use cases. |
| No automated drift detection | "We run terraform plan manually before changes" | Drift happens between planned changes. Schedule daily drift detection in CI. Alert on drift immediately -- it is often a security issue. |
| Using `terraform taint` to force recreation | "The resource is broken, just recreate it" | `terraform taint` is destructive and deprecated in favor of `-replace`. Understand why the resource is broken before recreating. Tainting a node group kills all pods on those nodes. |
| Not testing modules before use | "It works on my machine" | Use Terratest or `terraform test` (built-in since 1.6) to validate modules create functional infrastructure. Test in an isolated account to avoid production impact. |
| Manual state manipulation without backup | "I'll just terraform state rm this broken resource" | Always back up state before manipulation: `terraform state pull > backup.tfstate`. State operations are irreversible. One wrong `state rm` and you orphan real resources. |

---

## Quiz

<details>
<summary>1. Why does Terraform slow down as the state file grows?</summary>

Before every plan or apply, Terraform performs a "state refresh" -- it queries the cloud provider API for the current state of every resource in the state file. With 10 resources, this takes seconds. With 500 resources, each API call takes 50-200ms, totaling 25-100 seconds just for the refresh. Additionally, Terraform evaluates dependencies between all resources to build the execution graph, which grows in complexity with resource count. The state file itself (a JSON document) must be downloaded from the remote backend, parsed, and held in memory. A 50MB state file takes noticeable time to transfer and parse. State splitting reduces these costs by shrinking each state file to a manageable number of resources.
</details>

<details>
<summary>2. What is the difference between using terraform_remote_state and AWS data sources to share information between split state files?</summary>

`terraform_remote_state` reads outputs directly from another Terraform state file stored in a remote backend. This creates a tight coupling: the consuming module must know the exact backend configuration and state key. If the state file moves or the output name changes, the consuming module breaks. AWS data sources (like `data.aws_vpc`) query the cloud provider API directly, using tags or attributes to find resources. This is loosely coupled: the consuming module doesn't need to know where the resource was created or how. The trade-off is that data sources require consistent tagging, and they add API calls to every plan. For most cases, data sources are preferred because they survive state reorganization and are easier to understand.
</details>

<details>
<summary>3. When would you choose Crossplane over Terraform for managing cloud infrastructure?</summary>

Choose Crossplane when: (a) your team is Kubernetes-native and already uses ArgoCD/Flux for everything, (b) you want automatic drift correction (Crossplane's reconciliation loop continuously ensures the actual state matches the desired state), (c) you want developers to self-service cloud resources through Kubernetes CRDs without learning Terraform, (d) you're building an internal platform where K8s is the control plane for all infrastructure. Choose Terraform when: (a) you have existing Terraform modules and expertise, (b) you need broad resource coverage (Terraform has more providers and resource types), (c) you want `terraform plan` preview in pull requests, or (d) your infrastructure includes non-cloud resources that Crossplane doesn't cover.
</details>

<details>
<summary>4. How does Crossplane handle drift correction differently from Terraform?</summary>

Terraform detects drift only when you run `terraform plan` or `terraform apply` -- it is a point-in-time check, not continuous. If someone modifies a resource in the console at 2 AM, Terraform won't notice until the next plan runs. Crossplane runs a continuous reconciliation loop (like all Kubernetes controllers): every 60 seconds by default, it checks whether the actual cloud resource matches the desired state in the CRD spec. If it doesn't, Crossplane automatically corrects the drift. This means unauthorized manual changes are reverted within a minute, providing stronger guardrails but also less flexibility (you can't make emergency manual changes without also updating the CRD).
</details>

<details>
<summary>5. Why should Terraform state files never be committed to Git?</summary>

Terraform state files contain the plaintext values of all managed resources, including sensitive data: database passwords, API keys, TLS private keys, and IAM role ARNs. Even if the Git repo is private, state files in version control create a persistent audit trail of every secret ever used. They also grow large (10-100MB for real deployments), causing Git performance issues. Additionally, Git does not provide locking -- two engineers pushing state changes simultaneously would corrupt the state. Remote backends (S3, GCS, Azure Blob) solve all three problems: encryption at rest, no size issues, and DynamoDB/equivalent locking. The backend credentials are the only secret needed, and they can be provided through environment variables or IAM roles.
</details>

<details>
<summary>6. You have a Terraform module used by 10 teams. One team needs a feature that requires changing the module interface. How do you handle this?</summary>

Use semantic versioning for the module. Add the new feature as an optional variable with a default value that preserves the existing behavior. For example, if the new feature is Karpenter support, add `variable "enable_karpenter" { default = false }`. The 9 teams that don't need Karpenter continue using the module unchanged. The requesting team sets `enable_karpenter = true`. If the change is breaking (cannot be made backward-compatible), create a new major version of the module (v2). Pin existing consumers to v1 and let them migrate at their own pace. Never modify a shared module in a way that changes behavior for existing users without a version bump. Use Terratest to verify both the old and new behavior before releasing.
</details>

---

## Hands-On Exercise: Structure and Test Terraform for Multi-Account EKS

In this exercise, you will restructure a monolithic Terraform configuration into a modular, multi-state design.

### Scenario

You have a monolithic Terraform file that creates a VPC, EKS cluster, RDS database, and IAM roles. Split it into independent state files and create a basic module test.

### Task 1: Design the Directory Structure

<details>
<summary>Solution</summary>

```
terraform/
├── modules/
│   ├── networking/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── eks-cluster/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── database/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
│
├── environments/
│   ├── prod/
│   │   └── us-east-1/
│   │       ├── networking/
│   │       │   ├── main.tf        # Uses modules/networking
│   │       │   ├── backend.tf     # S3 state: prod/us-east-1/networking
│   │       │   └── terraform.tfvars
│   │       ├── eks-cluster/
│   │       │   ├── main.tf        # Uses modules/eks-cluster
│   │       │   ├── backend.tf     # S3 state: prod/us-east-1/eks-cluster
│   │       │   ├── data.tf        # Reads VPC from networking state
│   │       │   └── terraform.tfvars
│   │       └── database/
│   │           ├── main.tf        # Uses modules/database
│   │           ├── backend.tf     # S3 state: prod/us-east-1/database
│   │           ├── data.tf        # Reads VPC from networking state
│   │           └── terraform.tfvars
│   │
│   └── staging/
│       └── us-east-1/
│           └── ...                # Same structure, different values
│
└── test/
    ├── networking_test.go
    └── eks_cluster_test.go
```
</details>

### Task 2: Write the Networking Module

<details>
<summary>Solution</summary>

```hcl
# modules/networking/variables.tf
variable "environment" {
  type = string
}

variable "region" {
  type = string
}

variable "vpc_cidr" {
  type    = string
  default = "10.0.0.0/16"
}

variable "azs" {
  type    = list(string)
  default = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

# modules/networking/main.tf
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "${var.environment}-vpc"
    Environment = var.environment
  }
}

resource "aws_subnet" "private" {
  count             = length(var.azs)
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 4, count.index)
  availability_zone = var.azs[count.index]

  tags = {
    Name                              = "${var.environment}-private-${var.azs[count.index]}"
    "kubernetes.io/role/internal-elb" = "1"
    Tier                              = "private"
  }
}

resource "aws_subnet" "public" {
  count                   = length(var.azs)
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 4, count.index + length(var.azs))
  availability_zone       = var.azs[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name                     = "${var.environment}-public-${var.azs[count.index]}"
    "kubernetes.io/role/elb" = "1"
    Tier                     = "public"
  }
}

# modules/networking/outputs.tf
output "vpc_id" {
  value = aws_vpc.main.id
}

output "private_subnet_ids" {
  value = aws_subnet.private[*].id
}

output "public_subnet_ids" {
  value = aws_subnet.public[*].id
}

output "vpc_cidr" {
  value = aws_vpc.main.cidr_block
}
```
</details>

### Task 3: Write the Environment Configuration

<details>
<summary>Solution</summary>

```hcl
# environments/prod/us-east-1/networking/backend.tf
terraform {
  backend "s3" {
    bucket         = "company-terraform-state"
    key            = "prod/us-east-1/networking/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}

# environments/prod/us-east-1/networking/main.tf
module "networking" {
  source = "../../../../modules/networking"

  environment = "production"
  region      = "us-east-1"
  vpc_cidr    = "10.0.0.0/16"
  azs         = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

output "vpc_id" {
  value = module.networking.vpc_id
}

output "private_subnet_ids" {
  value = module.networking.private_subnet_ids
}

# environments/prod/us-east-1/eks-cluster/data.tf
# Read VPC info from the networking state
data "terraform_remote_state" "networking" {
  backend = "s3"
  config = {
    bucket = "company-terraform-state"
    key    = "prod/us-east-1/networking/terraform.tfstate"
    region = "us-east-1"
  }
}

# environments/prod/us-east-1/eks-cluster/main.tf
module "eks" {
  source = "../../../../modules/eks-cluster"

  cluster_name = "prod-us-east-1"
  vpc_id       = data.terraform_remote_state.networking.outputs.vpc_id
  subnet_ids   = data.terraform_remote_state.networking.outputs.private_subnet_ids

  node_groups = {
    general = {
      instance_types = ["m7i.xlarge"]
      desired_size   = 3
      min_size       = 3
      max_size       = 10
    }
  }

  tags = {
    Environment = "production"
    CostCenter  = "CC-1000"
  }
}
```
</details>

### Task 4: Write a Drift Detection Script

<details>
<summary>Solution</summary>

```bash
#!/bin/bash
# scripts/detect-drift.sh
set -e

COMPONENTS=("networking" "eks-cluster" "database")
ENVIRONMENT="prod"
REGION="us-east-1"
DRIFT_FOUND=0

echo "=== Terraform Drift Detection ==="
echo "Environment: $ENVIRONMENT"
echo "Region: $REGION"
echo "Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

for COMPONENT in "${COMPONENTS[@]}"; do
  DIR="terraform/environments/${ENVIRONMENT}/${REGION}/${COMPONENT}"

  if [ ! -d "$DIR" ]; then
    echo "SKIP: $COMPONENT (directory not found)"
    continue
  fi

  echo "--- Checking $COMPONENT ---"
  cd "$DIR"

  terraform init -input=false -no-color > /dev/null 2>&1

  # Run refresh-only plan with detailed exit code
  # Exit code 0 = no changes, 1 = error, 2 = changes detected
  set +e
  PLAN_OUTPUT=$(terraform plan -refresh-only -detailed-exitcode -input=false -no-color 2>&1)
  EXIT_CODE=$?
  set -e

  if [ $EXIT_CODE -eq 2 ]; then
    echo "DRIFT DETECTED in $COMPONENT"
    echo "$PLAN_OUTPUT" | grep -A 5 "has been changed"
    DRIFT_FOUND=1
  elif [ $EXIT_CODE -eq 0 ]; then
    echo "OK: No drift in $COMPONENT"
  else
    echo "ERROR: Failed to check $COMPONENT"
    echo "$PLAN_OUTPUT"
  fi

  cd - > /dev/null
  echo ""
done

if [ $DRIFT_FOUND -eq 1 ]; then
  echo "=== DRIFT DETECTED ==="
  echo "Run 'terraform plan' in the affected components for details."
  exit 2
else
  echo "=== ALL CLEAR ==="
  echo "No drift detected in any component."
  exit 0
fi
```
</details>

### Task 5: Write a Basic Terraform Test

<details>
<summary>Solution</summary>

```hcl
# modules/networking/tests/networking.tftest.hcl
# (Terraform native testing, available since v1.6)

variables {
  environment = "test"
  region      = "us-east-1"
  vpc_cidr    = "10.99.0.0/16"
  azs         = ["us-east-1a", "us-east-1b"]
}

run "vpc_is_created" {
  command = plan

  assert {
    condition     = aws_vpc.main.cidr_block == "10.99.0.0/16"
    error_message = "VPC CIDR should be 10.99.0.0/16"
  }

  assert {
    condition     = aws_vpc.main.enable_dns_hostnames == true
    error_message = "VPC should have DNS hostnames enabled"
  }

  assert {
    condition     = aws_vpc.main.tags["Environment"] == "test"
    error_message = "VPC should be tagged with Environment=test"
  }
}

run "subnets_are_created" {
  command = plan

  assert {
    condition     = length(aws_subnet.private) == 2
    error_message = "Should create 2 private subnets (one per AZ)"
  }

  assert {
    condition     = length(aws_subnet.public) == 2
    error_message = "Should create 2 public subnets (one per AZ)"
  }

  assert {
    condition     = aws_subnet.private[0].tags["Tier"] == "private"
    error_message = "Private subnets should be tagged Tier=private"
  }
}

run "subnets_have_unique_cidrs" {
  command = plan

  assert {
    condition     = aws_subnet.private[0].cidr_block != aws_subnet.private[1].cidr_block
    error_message = "Private subnets should have different CIDR blocks"
  }
}
```

```bash
# Run the tests
cd modules/networking
terraform test

# Expected output:
# tests/networking.tftest.hcl... in progress
#   run "vpc_is_created"... pass
#   run "subnets_are_created"... pass
#   run "subnets_have_unique_cidrs"... pass
# tests/networking.tftest.hcl... tearing down
# tests/networking.tftest.hcl... pass
#
# Success! 3 passed, 0 failed.
```
</details>

### Success Criteria

- [ ] Directory structure separates networking, EKS, and database into independent state files
- [ ] Each component has its own backend configuration with unique state key
- [ ] EKS component reads VPC info from networking state (via remote_state or data sources)
- [ ] Drift detection script checks all components and reports findings
- [ ] Terraform tests validate module behavior without deploying real resources

---

## Next Module

Return to the [Advanced Operations README]() for a summary of all modules in this phase and guidance on what to learn next. You have covered the full spectrum of advanced cloud operations: from multi-account architecture through transit networking, identity, disaster recovery, active-active deployments, migration, cost optimization, observability, and infrastructure as code at scale.

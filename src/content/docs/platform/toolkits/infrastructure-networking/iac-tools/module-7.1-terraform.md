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
- Enough cloud familiarity to recognize regions, accounts, IAM roles, virtual networks, and managed Kubernetes clusters
- Enough Git familiarity to review a pull request that changes infrastructure code before it reaches production

---

## Learning Outcomes

After completing this module, you will be able to:

- **Design** a Terraform project layout that separates reusable modules, environment stacks, and remote state boundaries for a multi-team platform.
- **Debug** Terraform plan output by connecting provider configuration, dependency graph behavior, lifecycle rules, and state contents to the proposed change.
- **Evaluate** when to use workspaces, directories, remote state, moved blocks, import blocks, modules, and provider aliases in production infrastructure.
- **Refactor** Terraform configuration without recreating live resources by using stable addresses, moved blocks, state inspection, and cautious migration steps.
- **Implement** input validation, outputs, tags, lifecycle controls, and repeatable verification steps for a small production-style module.

---

## Why This Module Matters

A platform team inherits a cloud estate after three years of fast delivery. The application teams move quickly, but no one is fully confident about the infrastructure anymore. One engineer remembers that the production cluster was created with Terraform, another remembers a manual subnet change during an incident, and the finance team has discovered orphaned load balancers that no dashboard explains. The next compliance audit asks a simple question: who approved the current shape of production?

That team does not need a prettier wrapper around cloud APIs. It needs an operating model that turns infrastructure into reviewed, repeatable, explainable change. Terraform can provide that model, but only when engineers treat it as a system with state, graph planning, provider boundaries, module contracts, and recovery procedures. Copying a resource block from a blog post is enough to create infrastructure; it is not enough to operate infrastructure safely with other people.

The beginner view of Terraform is comforting: write configuration, run `terraform plan`, run `terraform apply`, and the cloud matches the code. The senior view is more precise: Terraform compares desired configuration, provider-read reality, and previously recorded state, then proposes a graph of operations that may include replacements, deletes, imports, provider authentication, and cross-state dependencies. Most serious Terraform failures happen when one of those inputs is misunderstood or treated casually.

This module teaches Terraform as a production change engine rather than a syntax collection. We will start with the mental model, then build toward provider design, state management, module composition, refactoring, and operational review. The goal is not to memorize every HCL feature. The goal is to reason through a plan and decide whether it is safe, suspicious, or incomplete.

---

## Core Content

### 1. Terraform's Operating Model: Code, State, Reality, and the Graph

Terraform is easiest to understand when you separate the four things it compares during every serious operation. Configuration describes the desired shape, state records Terraform's last known mapping to real objects, provider reads describe current remote reality, and the dependency graph determines the order in which changes can safely happen. A weak mental model collapses those into "Terraform knows my infrastructure," which is the beginning of many incidents.

The configuration files are not the infrastructure and the state file is not the infrastructure either. Configuration is the intent, state is Terraform's memory, and the cloud provider remains the source of live behavior. When you run a plan, Terraform refreshes state by asking providers about real objects, compares the refreshed state to configuration, and then builds an action graph. That graph is why a subnet can be created before an instance, why some resources can update in parallel, and why one tiny address change can become a replacement.

```ascii
+-----------------------------------------------------------------------+
|                       TERRAFORM CHANGE MODEL                          |
+-----------------------------------------------------------------------+
|                                                                       |
|  Desired configuration              Terraform state                   |
|  *.tf files                         terraform.tfstate                 |
|       |                                      |                         |
|       | parse HCL                             | read known addresses    |
|       v                                      v                         |
|  +----------------+                   +----------------+               |
|  | Resource graph |<----------------->| Prior mapping  |               |
|  +--------+-------+                   +--------+-------+               |
|           |                                    |                       |
|           | provider refresh                   | resource IDs           |
|           v                                    v                       |
|  +-----------------------------------------------------------------+  |
|  | Provider plugins read live infrastructure through cloud APIs      |  |
|  +-----------------------------------------------------------------+  |
|           |                                                            |
|           | compare desired state, refreshed state, and dependencies   |
|           v                                                            |
|  +-----------------------------------------------------------------+  |
|  | Plan: create, update, replace, delete, import, or no-op actions   |  |
|  +-----------------------------------------------------------------+  |
|                                                                       |
+-----------------------------------------------------------------------+
```

This model explains why plans deserve careful review instead of blind approval. A plan that wants to replace a database may be logically correct from Terraform's perspective because an immutable argument changed, but still operationally unacceptable because the data migration has not been designed. Terraform can tell you what it intends to do; it cannot automatically know whether the business is ready for that action.

**Pause and predict:** Your teammate renames `aws_security_group.web` to `aws_security_group.frontend` without a moved block. The resource arguments are identical, and the remote security group still exists. Before reading further, predict what `terraform plan` will propose and explain which part of Terraform's operating model caused that result.

The likely plan is "destroy the old address and create a new address," even though the underlying settings look unchanged. Terraform tracks resources by address in state, not by human intent. The old address disappeared from configuration, and a new address appeared that has no state mapping. A senior review catches this before apply and asks for a `moved` block so Terraform updates its memory rather than replacing infrastructure.

```hcl
moved {
  from = aws_security_group.web
  to   = aws_security_group.frontend
}
```

There are two important lessons in that small example. First, Terraform resource addresses are part of the API of your infrastructure code, so renaming is a migration, not a harmless cleanup. Second, "no cloud diff" and "no Terraform replacement" are different claims. A reviewer must read the plan through the lens of state addresses, provider behavior, and lifecycle constraints.

Terraform's architecture supports that workflow by keeping the CLI small and delegating resource-specific logic to providers. The AWS provider knows which EC2 arguments require replacement, the Kubernetes provider knows how to talk to the API server, and the Helm provider knows how releases are represented. Terraform Core handles graph construction, expression evaluation, state operations, and the common planning lifecycle.

```ascii
+-----------------------------------------------------------------------+
|                    TERRAFORM ARCHITECTURE                             |
+-----------------------------------------------------------------------+
|                                                                       |
|                        +------------------+                           |
|                        |  Terraform CLI   |                           |
|                        |  Core Engine     |                           |
|                        +---------+--------+                           |
|                                  |                                    |
|              +-------------------+-------------------+                |
|              |                   |                   |                |
|              v                   v                   v                |
|       +--------------+    +--------------+    +--------------+        |
|       | Provider AWS |    | Provider K8s |    | Provider Helm |       |
|       | Cloud plugin |    | API plugin   |    | Release plugin|       |
|       +------+-------+    +------+-------+    +------+-------+        |
|              |                   |                   |                |
|              v                   v                   v                |
|       +--------------+    +--------------+    +--------------+        |
|       | AWS APIs     |    | Kubernetes   |    | Kubernetes   |        |
|       |              |    | API server   |    | API server   |        |
|       +--------------+    +--------------+    +--------------+        |
|                                                                       |
|  Flow inside Terraform Core:                                          |
|                                                                       |
|  *.tf files -> parse -> evaluate -> build graph -> plan -> apply      |
|                                      ^              |       |         |
|                                      |              v       v         |
|                                state addresses   diff   new state     |
|                                                                       |
+-----------------------------------------------------------------------+
```

A strong Terraform habit is to ask "which layer owns this fact?" If a value is environment-specific, it belongs in environment input. If a value is derived from other inputs, it belongs in locals. If a value must be consumed by another stack, it may belong in an output. If a value is sensitive, it should usually live in a secret manager and appear in Terraform only as a reference, not as plaintext.

A second strong habit is to read a Terraform plan like an incident timeline. Find replacements first, then deletes, then updates to risky resources, then newly created dependencies. Ask whether the graph order makes sense and whether lifecycle rules are masking a real change. When the plan is large, save it as a binary plan and inspect the JSON form in automation so policy checks can reason about it consistently.

```bash
terraform plan -out=tfplan
terraform show -json tfplan > tfplan.json
```

Those commands are runnable in any initialized Terraform directory. The JSON output is intentionally machine-readable, which is useful for policy engines and CI gates. Humans should still read the normal plan, because the text plan is optimized for review conversations and tends to make replacements and deletes more visible.

### 2. Provider Configuration: Authentication, Aliases, and Operational Boundaries

Provider configuration is where Terraform connects intent to a real control plane. A provider block answers questions that are operationally sensitive: which account, which region, which credentials, which Kubernetes cluster, and which default tags. When provider configuration is vague, plans become hard to trust because the same resource block may target the wrong account or region.

A production Terraform repository usually pins provider versions because provider schemas are part of the behavior of a plan. A new provider version can add defaults, change validation, fix a drift bug, or mark a field as requiring replacement. Version constraints and the `.terraform.lock.hcl` file do not remove the need for upgrades; they make upgrades visible, reviewable, and repeatable.

```hcl
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

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = var.environment
      ManagedBy   = "terraform"
      Project     = var.project_name
    }
  }

  assume_role {
    role_arn     = var.assume_role_arn
    session_name = "TerraformSession"
  }
}
```

This configuration teaches several production habits at once. The version constraints keep provider upgrades deliberate, default tags make ownership visible in cloud inventory, and `assume_role` separates the human or CI identity from the account role that changes infrastructure. Those details matter when the platform grows beyond one engineer and one sandbox account.

Provider aliases let one stack use multiple configurations of the same provider. The most common cases are multi-region networking, centralized DNS, shared identity accounts, and hub-spoke cloud organizations. Aliases are powerful because they make account and region selection explicit at the resource or module boundary, but they also increase review burden. A reviewer must confirm that each resource uses the intended provider alias, especially when production and non-production accounts live side by side.

```hcl
provider "aws" {
  alias  = "development"
  region = var.aws_region

  assume_role {
    role_arn = "arn:aws:iam::111111111111:role/TerraformRole"
  }
}

provider "aws" {
  alias  = "production"
  region = var.aws_region

  assume_role {
    role_arn = "arn:aws:iam::333333333333:role/TerraformRole"
  }
}

resource "aws_s3_bucket" "audit_logs" {
  provider = aws.production
  bucket   = "production-audit-logs-example"

  tags = {
    Environment = "production"
    DataClass   = "audit"
  }
}
```

Aliased providers become even more important when modules enter the design. A module should not silently choose the wrong account because the caller forgot to pass a provider. For shared modules that operate across accounts, define the provider expectation clearly in examples and require the root module to pass aliases. This keeps the module reusable while forcing environment ownership to remain outside the module.

```hcl
module "central_dns" {
  source = "../../modules/route53-zone"

  providers = {
    aws = aws.production
  }

  zone_name = "platform.example.com"
}
```

**Stop and think:** Your organization has separate AWS accounts for development, staging, and production. A single root module configures all three provider aliases in one directory. A pull request adds a new S3 bucket but omits the `provider = aws.production` line. What would you check in the plan before approving, and what repository design might reduce this risk?

The immediate check is which provider configuration Terraform selected for the new resource. If the unaliased default provider points at development, the bucket may be created in the wrong account. If the default provider points at production, a developer might accidentally create production infrastructure from a change that looked harmless. A safer design often uses directory-per-environment stacks, with one account target per stack, and reserves aliases for genuinely cross-account resources.

Kubernetes and Helm providers add another layer because they often depend on cloud resources created by the same Terraform stack. The provider needs an API endpoint, a cluster certificate, and an authentication method. That means a plan may involve both cloud control plane resources and Kubernetes resources, which can become fragile if the cluster is not reachable during planning or if authentication differs between CI and local machines.

```hcl
data "aws_eks_cluster" "main" {
  name = var.cluster_name
}

provider "kubernetes" {
  host                   = data.aws_eks_cluster.main.endpoint
  cluster_ca_certificate = base64decode(data.aws_eks_cluster.main.certificate_authority[0].data)

  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    args        = ["eks", "get-token", "--cluster-name", data.aws_eks_cluster.main.name]
  }
}

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

A senior platform engineer questions whether Terraform should manage everything in one root module. Creating an EKS cluster and installing in-cluster controllers through Helm in the same state can work, but it couples cloud provisioning with Kubernetes API availability. Many teams split cluster infrastructure, cluster add-ons, and application namespaces into separate states so failures are easier to isolate and permissions can be narrower.

The decision is not "always split" or "always combine." A small team may accept one root module for speed, while a regulated organization may require separate states for network, cluster, security add-ons, and workloads. The key is that the boundary should reflect operational ownership and recovery procedures, not only directory aesthetics.

| Provider Boundary | Good Fit | Risk to Watch | Review Question |
|-------------------|----------|---------------|-----------------|
| One provider per environment stack | Teams want simple account targeting and clear blast radius | Some shared services require cross-stack references | Does this stack target only one account unless aliases are explicit? |
| Aliases inside one stack | Central DNS, shared transit gateways, or multi-region failover | Resources can land in the wrong account if provider selection is implicit | Is every aliased resource visibly tied to the correct provider? |
| Cloud and Kubernetes in one state | Small clusters with simple add-ons and one owner | Cluster API downtime can block unrelated cloud changes | Can we recover if the Kubernetes API is unavailable during plan? |
| Separate cloud and Kubernetes states | Larger platforms with different owners and permissions | More remote-state outputs and dependency contracts to maintain | Are the cross-state outputs stable and intentionally minimal? |

### 3. State Management: Remote Backends, Drift, Locks, and Recovery

Terraform state is the most misunderstood part of the tool because it feels like an implementation detail until it becomes the incident. State maps Terraform addresses to real resource IDs and stores attributes that providers need for planning. It may also contain sensitive values. Losing it, corrupting it, or letting multiple writers modify it concurrently can turn a normal change into a recovery exercise.

Local state is acceptable for learning and throwaway experiments, but teams need remote state with locking for shared infrastructure. A remote backend gives everyone the same source of Terraform memory, while locking prevents two applies from racing. Encryption and access control matter because state can include secrets, generated passwords, private endpoints, and other operationally sensitive information.

```hcl
terraform {
  backend "s3" {
    bucket         = "company-terraform-state"
    key            = "environments/production/networking/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    kms_key_id     = "alias/terraform-state"
    dynamodb_table = "terraform-state-lock"

    role_arn = "arn:aws:iam::123456789012:role/TerraformStateAccess"
  }
}
```

Backend configuration is intentionally static in Terraform. You cannot use normal variables inside the backend block because Terraform must initialize the backend before it evaluates the rest of the configuration. Teams usually handle this with one directory per environment, backend configuration files passed to `terraform init`, or a higher-level wrapper. The important principle is that the state path should be obvious during review.

State commands are powerful, but they are operational tools rather than everyday formatting commands. Use them when importing existing resources, renaming addresses, splitting states, or recovering from drift. Always take a backup before state surgery, and prefer declarative `moved` and `import` blocks when they fit the change because they create reviewable history inside configuration.

```bash
terraform state list
terraform state show aws_instance.web
terraform state pull > terraform.tfstate.backup
terraform state mv aws_instance.web aws_instance.application
terraform state rm aws_instance.web
terraform import aws_instance.web i-1234567890abcdef0
terraform force-unlock LOCK_ID
```

The dangerous command in that list is not only `force-unlock`, although that one deserves caution. `terraform state rm` is also risky because it tells Terraform to forget a resource without deleting it. That can be useful when moving ownership to another stack, but it can also create unmanaged infrastructure that no future plan controls. Every state command should answer three questions: what address changes, what remote object remains, and how will the next plan prove success?

```json
{
  "version": 4,
  "terraform_version": "1.6.0",
  "serial": 42,
  "lineage": "unique-id-for-this-state",
  "outputs": {
    "cluster_name": {
      "value": "production",
      "type": "string"
    }
  },
  "resources": [
    {
      "mode": "managed",
      "type": "aws_eks_cluster",
      "name": "main",
      "provider": "provider[\"registry.terraform.io/hashicorp/aws\"]",
      "instances": [
        {
          "schema_version": 1,
          "attributes": {
            "name": "production",
            "version": "1.35",
            "tags": {
              "ManagedBy": "terraform"
            }
          },
          "sensitive_attributes": [],
          "private": "base64-encoded-provider-data"
        }
      ]
    }
  ]
}
```

You should understand the shape of state, but you should not manually edit it as normal practice. Terraform includes state commands because the state file has provider-specific internals and consistency metadata. Manual edits bypass those safeguards and can produce subtle failures later. When someone proposes opening a state file in an editor, ask which supported command or declarative block would express the same migration.

Drift occurs when live infrastructure no longer matches Terraform's recorded and desired view. Some drift is accidental, such as a console edit during an outage. Some drift is intentional, such as an autoscaling group changing desired capacity at runtime. Terraform's job is not to shame every drift event; its job is to make drift visible so the team can decide whether to reconcile code, revert the manual change, or ignore a field deliberately.

```bash
terraform plan -refresh-only
```

A refresh-only plan is useful when you want to detect and record drift without proposing configuration-driven changes. It can show whether a manual change exists before you combine that investigation with a feature change. In production workflows, drift checks are often scheduled separately from normal delivery so teams can investigate surprises before they become part of a larger deployment.

**Pause and predict:** An operator changes a database instance class in the cloud console during an urgent capacity incident. The Terraform configuration still says the smaller class. The next pull request changes only tags. What do you expect Terraform to propose, and what should the reviewer do before approving?

Terraform will refresh the database attributes, notice that live reality differs from configuration, and likely propose changing the instance class back to the configured value along with the tag update. The reviewer should separate the tag change from the drift decision. If the emergency size should remain, update Terraform configuration in a dedicated change and include the incident context. If the larger size was temporary, schedule the downsizing deliberately instead of hiding it inside a tag change.

Cross-state references are useful when one stack needs outputs from another, but they create contracts between state files. A networking stack might expose subnet IDs to an application stack, or a cluster stack might expose an OIDC provider ARN to an identity stack. Keep those outputs stable, small, and intentionally named. Do not expose entire resource objects just because Terraform allows it.

```hcl
data "terraform_remote_state" "networking" {
  backend = "s3"

  config = {
    bucket   = "company-terraform-state"
    key      = "environments/production/networking/terraform.tfstate"
    region   = "us-east-1"
    role_arn = "arn:aws:iam::123456789012:role/TerraformStateAccess"
  }
}

resource "aws_instance" "web" {
  ami           = var.ami_id
  instance_type = "t3.medium"
  subnet_id     = data.terraform_remote_state.networking.outputs.private_subnet_ids[0]

  vpc_security_group_ids = [
    data.terraform_remote_state.networking.outputs.app_security_group_id
  ]
}
```

A remote-state output is a coupling point. If the networking team renames `private_subnet_ids`, the application stack breaks even though no cloud object changed. For that reason, outputs should be treated like module interfaces: documented, reviewed, versioned through communication, and changed with consumers in mind.

### 4. Module Design: Contracts Before Cleverness

A Terraform module is a contract, not only a folder. The caller provides inputs, the module creates or reads resources, and the module returns outputs that other code may depend on. Good modules hide implementation details without hiding operational choices. Bad modules accept every possible option, expose internal resource shapes, and become harder to understand than the raw provider resources they wrap.

Start module design by deciding the job of the module in one sentence. A VPC module may own address space, subnets, route tables, and gateways. It probably should not also install Kubernetes controllers, create application DNS records, and manage database passwords. Clear module boundaries keep plans readable and make it easier to reason about blast radius.

```ascii
+-----------------------------------------------------------------------+
|                         MODULE CONTRACT                               |
+-----------------------------------------------------------------------+
|                                                                       |
|  Caller stack                                                         |
|  +-----------------------------------------------------------------+  |
|  | Inputs: name, cidr, zones, tags, feature flags                  |  |
|  |                                                                 |  |
|  | module "vpc" {                                                  |  |
|  |   source = "../../modules/vpc"                                  |  |
|  | }                                                               |  |
|  +-------------------------------+---------------------------------+  |
|                                  |                                    |
|                                  v                                    |
|  Reusable module                                                       |
|  +-----------------------------------------------------------------+  |
|  | Validation -> locals -> resources -> lifecycle -> outputs        |  |
|  +-------------------------------+---------------------------------+  |
|                                  |                                    |
|                                  v                                    |
|  Outputs: vpc_id, private_subnet_ids, public_subnet_ids, route IDs     |
|                                                                       |
+-----------------------------------------------------------------------+
```

A module's directory structure should help a reader find decisions quickly. `variables.tf` defines the contract, `locals.tf` explains derived decisions, `main.tf` contains primary resources, and `outputs.tf` defines what callers may depend on. Tests and examples belong near the module because the module should be usable without reading a production environment directory first.

```ascii
modules/
└── vpc/
    ├── main.tf
    ├── variables.tf
    ├── outputs.tf
    ├── versions.tf
    ├── locals.tf
    ├── data.tf
    ├── README.md
    ├── examples/
    │   └── complete/
    │       └── main.tf
    └── tests/
        └── vpc_test.tftest.hcl
```

The most important part of a module is often its variables. Input validation moves failure earlier, closer to the person making the change. A clear validation error is cheaper than a failed apply after Terraform has already created half the graph. Validation also teaches callers what the module considers safe or supported.

```hcl
variable "name" {
  description = "Lowercase name prefix used for resources created by this module."
  type        = string

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]*$", var.name))
    error_message = "Name must start with a letter and contain only lowercase letters, numbers, and hyphens."
  }
}

variable "cidr_block" {
  description = "CIDR block assigned to the VPC."
  type        = string

  validation {
    condition     = can(cidrhost(var.cidr_block, 0))
    error_message = "cidr_block must be a valid CIDR range such as 10.0.0.0/16."
  }
}

variable "availability_zones" {
  description = "Availability zones where subnets should be created."
  type        = list(string)

  validation {
    condition     = length(var.availability_zones) >= 2
    error_message = "At least two availability zones are required for this module."
  }
}

variable "tags" {
  description = "Tags applied to all taggable resources."
  type        = map(string)
  default     = {}
}
```

A worked example makes the contract concrete. Imagine a team needs a VPC module for development and production, but production requires three private subnets while development can use two. Instead of hardcoding separate resources for each environment, the module accepts a list of private CIDRs and creates one subnet per entry. The caller owns the environment decision, and the module owns the repeatable subnet pattern.

```hcl
resource "aws_vpc" "main" {
  cidr_block           = var.cidr_block
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(var.tags, {
    Name = "${var.name}-vpc"
  })
}

resource "aws_subnet" "private" {
  for_each = {
    for index, cidr in var.private_subnet_cidrs :
    var.availability_zones[index] => cidr
  }

  vpc_id            = aws_vpc.main.id
  cidr_block        = each.value
  availability_zone = each.key

  tags = merge(var.tags, {
    Name = "${var.name}-private-${each.key}"
    Tier = "private"
  })
}

output "private_subnet_ids" {
  description = "Private subnet IDs keyed by availability zone."
  value       = { for zone, subnet in aws_subnet.private : zone => subnet.id }
}
```

This example uses `for_each` rather than `count` because availability zones make stable keys. If the team later removes one zone, Terraform can identify the specific subnet keyed by that zone instead of shifting numeric indexes. Stable keys are one of the simplest ways to prevent accidental replacements during list edits.

**Stop and think:** A module creates three subnets with `count` from a list of CIDR blocks. A pull request removes the first CIDR from the list because that zone is being retired. Before running a plan, predict what might happen to the remaining subnet addresses and why `for_each` with stable keys changes the risk.

With `count`, Terraform addresses the subnets as `aws_subnet.private[0]`, `aws_subnet.private[1]`, and `aws_subnet.private[2]`. Removing the first list element can cause later elements to shift indexes, which may make Terraform update or replace resources that were not intended to change. With `for_each`, Terraform addresses each subnet by a stable key such as the availability zone, so removing one key does not rename every later resource.

Module outputs should be minimal and intentional. Expose values that callers need to connect systems, such as IDs, ARNs, endpoints, and names. Avoid exposing full resource objects unless callers truly need them, because full objects leak provider implementation details and create fragile dependencies. A good output is a promise you are willing to maintain.

```hcl
output "vpc_id" {
  description = "ID of the VPC created by this module."
  value       = aws_vpc.main.id
}

output "private_subnet_ids" {
  description = "Private subnet IDs keyed by availability zone."
  value       = { for zone, subnet in aws_subnet.private : zone => subnet.id }
}

output "vpc_cidr_block" {
  description = "CIDR block assigned to the VPC."
  value       = aws_vpc.main.cidr_block
}
```

Module composition should read like architecture. A production environment stack can create a VPC module first, then pass its private subnets into an EKS module, then pass the cluster identity into an add-ons module. The direction of dependencies should match the real architecture. If the module graph feels tangled, the platform architecture may be tangled too.

```hcl
module "vpc" {
  source = "../../modules/vpc"

  name               = "production"
  cidr_block         = "10.0.0.0/16"
  availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]
  private_subnet_cidrs = [
    "10.0.11.0/24",
    "10.0.12.0/24",
    "10.0.13.0/24"
  ]

  tags = local.common_tags
}

module "eks" {
  source = "../../modules/eks"

  cluster_name = "production"
  vpc_id       = module.vpc.vpc_id
  subnet_ids   = values(module.vpc.private_subnet_ids)

  tags = local.common_tags
}
```

Do not confuse module reuse with module abstraction. A reusable module should make common safe behavior easy while still allowing the caller to make meaningful environment decisions. If every module variable is an escape hatch for raw provider arguments, the module has become a pass-through layer. If the module hides too much, callers cannot evaluate risk. The best modules are opinionated at the right level.

### 5. HCL Patterns: Expressions, Dynamic Blocks, and Lifecycle Controls

HCL is a configuration language with expressions, not a general-purpose programming language. That distinction matters. Use expressions to model infrastructure shape clearly, but avoid building a second application inside Terraform. When a local value takes several minutes to understand, it may be a sign that the data model or module boundary needs simplification.

For expressions are often the most readable way to transform caller-friendly input into provider-friendly structures. In the example below, callers provide a list of users, and Terraform creates a map keyed by name. The stable key is then used by `for_each`, which makes future additions and removals predictable.

```hcl
variable "users" {
  type = list(object({
    name  = string
    email = string
    role  = string
  }))
}

locals {
  users_by_name = { for user in var.users : user.name => user }
  admin_emails  = [for user in var.users : user.email if user.role == "admin"]
  user_roles    = { for user in var.users : user.email => user.role }
}

resource "aws_iam_user" "users" {
  for_each = local.users_by_name

  name = each.key

  tags = {
    Email = each.value.email
    Role  = each.value.role
  }
}
```

Dynamic blocks are useful when a provider has repeated nested blocks rather than a separate resource type. Security group ingress rules are a common example. Dynamic blocks should remove repetition without hiding security decisions. If a reader cannot tell which ports are open and why, the abstraction has gone too far.

```hcl
variable "ingress_rules" {
  description = "Ingress rules for the security group."
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
```

Lifecycle rules change how Terraform handles resource changes, so they deserve the same review attention as IAM policies or networking rules. `create_before_destroy` can reduce downtime for replaceable resources, but it may fail if names must be unique. `prevent_destroy` can protect critical resources, but it can also block legitimate migration unless the team has a documented procedure. `ignore_changes` can quiet expected runtime drift, but it can also hide configuration drift that should be fixed.

```hcl
resource "aws_instance" "web" {
  ami           = var.ami_id
  instance_type = var.instance_type

  lifecycle {
    create_before_destroy = true

    ignore_changes = [
      tags["LastModified"]
    ]
  }
}

resource "aws_db_instance" "main" {
  identifier          = var.db_identifier
  engine              = "postgres"
  instance_class      = var.instance_class
  deletion_protection = true

  lifecycle {
    prevent_destroy = true
    ignore_changes  = [password]
  }
}
```

A mature review asks why each lifecycle rule exists. Ignoring a tag maintained by automation is reasonable. Ignoring an AMI might be reasonable if another system owns image rollout, but dangerous if Terraform is supposed to own patching. Preventing database destroy is usually wise, but the team still needs a tested migration path for replacements. Lifecycle rules are not substitutes for operational design.

Moved blocks and import blocks are Terraform's safer answer to common state migrations. A moved block records an address refactor inside code, so every collaborator and CI run sees the same migration. An import block records that an existing remote object should become managed at a specific address. Both features make infrastructure history easier to review than one-off local state commands.

```hcl
moved {
  from = aws_instance.web
  to   = aws_instance.application
}

moved {
  from = aws_vpc.main
  to   = module.networking.aws_vpc.main
}

import {
  to = aws_s3_bucket.audit_logs
  id = "production-audit-logs-example"
}
```

The senior habit is to combine these blocks with a plan that shows no unintended infrastructure action. If a moved block is correct, Terraform should report that the address moved without destroying and recreating the object. If an import block is correct, the next step is usually to align configuration until the plan is empty or only contains intended normalization.

Terraform functions help you keep configuration declarative. `cidrsubnet` can generate subnet ranges, `merge` can build tags, `jsonencode` can produce valid IAM policies, and `templatefile` can render structured user data. Functions are best when they encode deterministic transformations. They are less helpful when they become a puzzle that future reviewers cannot safely change.

```hcl
locals {
  common_tags = merge(
    var.default_tags,
    {
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  )

  subnet_cidrs = {
    public = [
      for index in range(length(var.availability_zones)) :
      cidrsubnet(var.vpc_cidr, 8, index)
    ]

    private = [
      for index in range(length(var.availability_zones)) :
      cidrsubnet(var.vpc_cidr, 8, index + 10)
    ]
  }

  policy_json = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:GetObject"]
      Resource = "${aws_s3_bucket.main.arn}/*"
    }]
  })
}
```

**Pause and predict:** The production environment has three availability zones and the development environment has two. The module derives subnet CIDRs with `range(length(var.availability_zones))`. What happens when production adds a fourth zone, and which review questions should you ask before approving?

Terraform will calculate an additional CIDR for the new zone and likely propose one new subnet per derived subnet tier. That may be exactly what the team wants, but a reviewer should check route tables, NAT gateway capacity, load balancer subnet selection, IP address planning, and whether downstream stacks assume exactly three subnets. Derived values reduce typing, but they do not eliminate architectural decisions.

### 6. Worked Scenario: Migrating from Workspaces to Directory-Based State

Workspaces are frequently misunderstood because they look like environment separation. They can be useful for small, nearly identical copies of a stack, but they are not a strong boundary for different environments with different ownership, policies, or resource shapes. A workspace shares configuration and changes only the selected state. That can be elegant for simple duplication and risky for production platforms that evolve differently over time.

A team starts with one Terraform directory and three workspaces: `dev`, `staging`, and `production`. At first, all environments are identical except instance sizes. After two years, production has extra monitoring, staging has test integrations, and development uses a cheaper network layout. The shared configuration now contains many conditionals. Plans are harder to review because every change requires asking which workspace is selected.

```ascii
+-----------------------------------------------------------------------+
|                    BEFORE: WORKSPACE-BASED LAYOUT                     |
+-----------------------------------------------------------------------+
|                                                                       |
|  infrastructure/terraform/                                            |
|  +-----------------------------------------------------------------+  |
|  | main.tf                                                         |  |
|  | variables.tf                                                    |  |
|  | outputs.tf                                                      |  |
|  | backend.tf                                                      |  |
|  +-----------------------------------------------------------------+  |
|        |                 |                    |                      |
|        v                 v                    v                      |
|  workspace dev     workspace staging    workspace production          |
|  state key dev     state key staging     state key production         |
|                                                                       |
|  Risk: one configuration accumulates conditionals for environments     |
|  that are no longer operationally identical.                          |
|                                                                       |
+-----------------------------------------------------------------------+
```

The target layout separates reusable modules from environment stacks. Each environment has its own root module, backend key, variables, and plan review path. Shared behavior moves into modules, while environment differences become explicit at the stack level. This layout is not automatically better, but it is usually easier to review when production differs materially from non-production.

```ascii
+-----------------------------------------------------------------------+
|                    AFTER: DIRECTORY-BASED LAYOUT                      |
+-----------------------------------------------------------------------+
|                                                                       |
|  infrastructure/terraform/                                            |
|  +-----------------------------------------------------------------+  |
|  | modules/                                                        |  |
|  |   vpc/                                                          |  |
|  |   eks/                                                          |  |
|  |   rds/                                                          |  |
|  | dev/                                                            |  |
|  |   main.tf                                                       |  |
|  |   backend.tf                                                    |  |
|  | staging/                                                        |  |
|  |   main.tf                                                       |  |
|  |   backend.tf                                                    |  |
|  | production/                                                     |  |
|  |   main.tf                                                       |  |
|  |   backend.tf                                                    |  |
|  +-----------------------------------------------------------------+  |
|                                                                       |
|  Benefit: each environment has an explicit state boundary and review   |
|  surface while modules carry shared implementation patterns.           |
|                                                                       |
+-----------------------------------------------------------------------+
```

The migration should be treated like a production change, even if no infrastructure is supposed to change. The desired outcome is that Terraform's memory moves and every post-migration plan is empty or intentionally small. The danger is accidentally creating a second copy of infrastructure, forgetting resources in the old state, or selecting the wrong workspace during migration.

First, document the current state from each workspace. Save the resource address list and state backup before editing anything. These commands are runnable in the existing Terraform directory after backend initialization. They do not change infrastructure; they capture the baseline you will use for verification and rollback.

```bash
for workspace in dev staging production; do
  terraform workspace select "$workspace"
  terraform state list > "resources_${workspace}.txt"
  terraform state pull > "state_${workspace}.json"
done
```

Next, create the target directory structure and copy only the configuration that belongs in each environment. This is where many teams discover that their "shared" configuration contains environment-specific behavior. Resist the urge to preserve every conditional. Move reusable patterns into modules and make environment decisions visible in each root module.

```bash
mkdir -p modules/vpc modules/eks dev staging production
cp variables.tf outputs.tf dev/
cp variables.tf outputs.tf staging/
cp variables.tf outputs.tf production/
```

Then configure each new backend key deliberately. The exact backend values depend on your organization, but the key should identify the environment and stack clearly. A backend key such as `terraform.tfstate` is too vague in a shared state bucket. A key such as `environments/production/networking/terraform.tfstate` is easier to audit and recover.

```hcl
terraform {
  backend "s3" {
    bucket         = "company-terraform-state"
    key            = "environments/production/networking/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}
```

Finally, initialize the new directory and verify the plan. Depending on the existing backend layout, you may use backend migration, state pull and push procedures, or controlled state moves. The verification target is simple: Terraform should not propose replacing live resources merely because you reorganized files.

```bash
cd production
terraform init -migrate-state
terraform plan
```

If the plan is not empty, do not automatically fix it by editing state until the output is quiet. Read the differences. Some may be real drift that the old layout hid. Some may be address changes that need moved blocks. Some may be provider default changes caused by version updates during migration. A careful migration separates those causes so the pull request tells a coherent story.

**Worked decision example:** Suppose `terraform plan` after the production migration shows that `aws_vpc.main` will be destroyed and `module.vpc.aws_vpc.main` will be created. The VPC ID is the same real object you intended to keep, but the Terraform address changed because the resource moved into a module. The right fix is a moved block, not an apply.

```hcl
moved {
  from = aws_vpc.main
  to   = module.vpc.aws_vpc.main
}
```

After adding the moved block, run the plan again. A successful refactor plan should show Terraform recognizing the address move and not replacing the VPC. If other resources moved into the module, add explicit moved blocks for each address. This can feel tedious, but it is much safer than hoping Terraform infers human intent from similar arguments.

The rollback plan should be written before the migration starts. At minimum, you need the original state backups, a record of the original backend keys, and a decision about who can pause applies during the migration window. Remote state migration is less dramatic than database migration, but it controls infrastructure ownership. Treat it with the same respect.

| Migration Step | Evidence to Capture | Failure Signal | Recovery Action |
|----------------|--------------------|----------------|-----------------|
| Workspace inventory | `resources_ENV.txt` and `state_ENV.json` files | Missing resources or wrong selected workspace | Stop and repeat inventory before changing layout |
| Backend creation | Backend key and lock table confirmed | New state key collides with another stack | Choose a unique key before initialization |
| Address refactor | Plan shows moved addresses rather than replacements | Destroy/create for existing critical resources | Add moved blocks or correct module address mapping |
| Drift review | Drift documented separately from refactor | Tag-only change includes resizing or deletes | Split drift remediation into its own review |
| Final verification | Empty or intentionally small plan | Unknown deletes remain in the plan | Do not apply until ownership is understood |

### 7. Review Discipline: Reading Plans Like a Senior Engineer

Terraform review is a skill that improves with a consistent checklist. The first pass should identify blast radius: which accounts, regions, providers, states, and resource types are touched. The second pass should identify operation types: creates, updates, replacements, deletes, imports, and moves. The third pass should connect the plan back to the intent of the pull request. If the title says "add tags" and the plan replaces a database, the plan is telling you the story is incomplete.

A good plan review distinguishes scary-looking output from risky behavior. A large tag update across many resources may be noisy but safe. A one-line replacement of a stateful resource may be small but dangerous. A new IAM policy may not affect infrastructure shape at all, yet it can expand privilege in ways that matter more than a subnet creation. Review effort should follow operational risk, not line count.

```ascii
+-----------------------------------------------------------------------+
|                       PLAN REVIEW TRIAGE                              |
+-----------------------------------------------------------------------+
|                                                                       |
|  Start with intent from PR title and description                       |
|                  |                                                    |
|                  v                                                    |
|  +-------------------------------+                                    |
|  | Which state and provider?     |                                    |
|  +---------------+---------------+                                    |
|                  |                                                    |
|                  v                                                    |
|  +-------------------------------+                                    |
|  | Any deletes or replacements?  |---- yes ----> demand explanation   |
|  +---------------+---------------+                                    |
|                  | no                                                 |
|                  v                                                    |
|  +-------------------------------+                                    |
|  | Any IAM, network, or data?    |---- yes ----> review deeply        |
|  +---------------+---------------+                                    |
|                  | no                                                 |
|                  v                                                    |
|  +-------------------------------+                                    |
|  | Do outputs and dependencies   |                                    |
|  | still match consumers?        |                                    |
|  +-------------------------------+                                    |
|                                                                       |
+-----------------------------------------------------------------------+
```

One practical technique is to require plan summaries in pull requests. The summary should say which backend key was planned, which command ran, whether the plan was saved, and which high-risk resources changed. This prevents reviewers from approving code without knowing whether the plan came from the right environment.

```bash
terraform fmt -check -recursive
terraform validate
terraform plan -out=tfplan
terraform show -no-color tfplan > tfplan.txt
```

Those commands do not replace human judgment, but they make the review reproducible. `fmt` catches formatting drift, `validate` catches static configuration errors, `plan` evaluates provider schemas and state, and the saved plan output gives reviewers a stable artifact. In CI, you can also generate JSON for policy checks that block deletes in protected states or require explicit approval labels.

Security review deserves special attention. State access is often more sensitive than engineers expect, because state may include generated passwords, private IPs, kubeconfig data, and provider-specific secrets. Marking an output as `sensitive = true` prevents casual display in CLI output, but it does not remove the value from state. The real controls are secret design, state encryption, backend IAM, and minimizing secret material in Terraform-managed values.

```hcl
variable "db_password" {
  description = "Database password supplied from a secure runtime source."
  type        = string
  sensitive   = true
}

output "database_endpoint" {
  description = "Database endpoint for application connection configuration."
  value       = aws_db_instance.main.endpoint
}

output "database_password" {
  description = "Do not expose passwords as outputs in normal module design."
  value       = var.db_password
  sensitive   = true
}
```

The second output is intentionally a warning example. Even though it is marked sensitive, it still encourages downstream consumers to pull secrets from Terraform state. A better design stores the password in a secret manager and outputs a secret reference or ARN. Terraform can create the secret container, but runtime secret retrieval should usually happen through workload identity and secret management controls.

Senior Terraform practice is mostly disciplined restraint. Use modules, but keep their contracts small. Use lifecycle rules, but explain why. Use remote state, but expose stable outputs. Use dynamic expressions, but keep reviewability high. Terraform can scale to large infrastructure estates, but only if the team treats plans as operational evidence rather than ceremonial output.

---

## Did You Know?

- **Terraform's graph is not just documentation**: Terraform uses the dependency graph to decide execution order and parallelism, so references between resources directly influence apply behavior.

- **Sensitive values can still live in state**: Marking variables and outputs as sensitive changes display behavior, but backend encryption and access control remain essential.

- **Provider upgrades are behavior changes**: A provider version bump can change defaults, validation, drift detection, or replacement rules, which is why lock files and reviewable upgrades matter.

- **A moved block is a migration record**: It tells Terraform and future reviewers that an address changed intentionally while the remote object should remain the same.

---

## Common Mistakes

| Mistake | Problem | Better Approach |
|---------|---------|-----------------|
| Treating state as an implementation detail | Engineers make renames or imports without understanding address mappings, which can cause unexpected replacements | Review state addresses during refactors and prefer `moved` or `import` blocks when possible |
| Using one workspace layout for diverging environments | Configuration fills with conditionals and reviewers cannot easily see what production really does | Use directory-based environment stacks when environments differ materially |
| Leaving provider aliases implicit | Resources can land in the wrong account or region when the default provider is not the intended target | Pass provider aliases explicitly and keep account boundaries visible in code review |
| Exposing too many module outputs | Callers become coupled to provider internals and module implementation details | Output stable IDs, ARNs, names, and endpoints that form a deliberate contract |
| Hiding drift with broad `ignore_changes` | Terraform stops reporting changes that may represent security or reliability problems | Ignore only specific fields with documented external ownership |
| Using `count` for identity-sensitive resources | Removing or reordering list entries can shift numeric addresses and create avoidable replacements | Use `for_each` with stable keys such as names, zones, or IDs |
| Running applies without saved plans or review notes | Reviewers cannot prove which state, provider, or change set was approved | Save plan artifacts and summarize backend, provider, and high-risk actions in the pull request |
| Storing secrets as normal outputs | Sensitive data remains available through state and may spread to downstream logs or tooling | Store secrets in a secret manager and output references rather than secret values |

---

## Quiz

<details>
<summary>1. Your team renames `aws_lb.frontend` to `aws_lb.public` during a cleanup. The arguments are unchanged, but the plan shows one load balancer destroyed and another created. What should you do before approving?</summary>

Use a `moved` block that maps the old Terraform address to the new address, then run the plan again. The issue is not that the load balancer settings changed; it is that Terraform tracks the object by state address. Approval should wait until the plan shows an address move rather than a destroy and create. If the load balancer is stateful for traffic, DNS, or certificates, also verify dependent resources and outputs after the move.
</details>

<details>
<summary>2. A production tag update plan also proposes changing an RDS instance class back to a smaller size. The pull request does not mention capacity. How do you handle the review?</summary>

Treat the instance class change as drift, not as part of the tag update. Ask whether the larger instance class was an emergency console change, an intentional capacity adjustment, or an accidental edit. If the larger size should remain, update Terraform configuration in a separate or clearly expanded change. If it should be reverted, schedule that as an explicit operational action. Do not approve a tag-only story that silently changes database capacity.
</details>

<details>
<summary>3. A module creates subnets with `count` from a list of CIDRs. A pull request removes the first CIDR because one zone is retired, and the plan wants to update or replace later subnet indexes. What design change reduces the risk?</summary>

Use `for_each` with stable keys, such as availability zone names, instead of numeric indexes. With `count`, removing the first list element shifts later addresses like `aws_subnet.private[1]` to `aws_subnet.private[0]`. With `for_each`, removing `us-east-1a` does not rename `us-east-1b` and `us-east-1c`. The migration may need moved blocks so existing subnets are remapped safely to the new keyed addresses.
</details>

<details>
<summary>4. Your CI job for a Kubernetes add-ons stack fails planning whenever the EKS API server is temporarily unreachable. The same state also manages the EKS cluster itself. What architecture change would you evaluate?</summary>

Evaluate splitting the cloud cluster infrastructure and the in-cluster add-ons into separate states. The cluster state can manage VPC, IAM, and EKS resources, while the add-ons state uses the Kubernetes and Helm providers after the cluster is available. This reduces coupling between cloud provisioning and Kubernetes API availability. Before splitting, define stable outputs such as cluster name, endpoint, certificate data, and OIDC provider ARN, and document recovery procedures for both states.
</details>

<details>
<summary>5. A teammate wants to use `terraform state rm` to make Terraform forget an S3 bucket that another team will manage. What checks should happen first?</summary>

Confirm the bucket will remain live and that another clearly identified Terraform state or operational process will manage it. Take a state backup, record the current address and remote bucket ID, and verify that no outputs or dependent resources still expect the bucket from this state. After `state rm`, run a plan to confirm Terraform does not try to recreate or destroy related resources. The review should explain the ownership transfer, because forgetting a resource can create unmanaged infrastructure.
</details>

<details>
<summary>6. A module output exposes an entire `aws_vpc.main` object so callers can choose any attribute later. A consumer breaks after a provider upgrade changes an attribute shape. What would you change in the module contract?</summary>

Replace the broad object output with intentional outputs such as `vpc_id`, `vpc_cidr_block`, and `private_subnet_ids`. Full resource outputs couple consumers to provider internals and make module implementation changes harder. Stable, narrow outputs describe the contract the module is willing to support. If consumers need a new value, add it as a named output with a description and review the dependency explicitly.
</details>

<details>
<summary>7. A production plan shows no resource deletes, but it adds a broad IAM policy to a role used by Terraform CI. Why is this still a high-risk review item?</summary>

IAM changes can increase blast radius without changing visible infrastructure shape. A policy that grants broader permissions may let future applies, compromised credentials, or misconfigured jobs change resources outside the intended boundary. Review the exact actions, resources, conditions, and trust relationship. The absence of deletes in the plan does not make the change safe; privilege expansion must be evaluated against the platform's ownership and threat model.
</details>

<details>
<summary>8. Your team is migrating from workspaces to environment directories. After copying files into `production/`, the plan shows resources being created even though they already exist. What is your first debugging path?</summary>

First verify that the backend key and selected source workspace are correct, because an empty or wrong state makes existing objects look unmanaged. Then compare resource addresses from the old `terraform state list` output with the new configuration addresses. If resources moved into modules or were renamed, add `moved` blocks for each address. Do not apply the create plan until Terraform's state mapping reflects the existing infrastructure.
</details>

---

## Hands-On Exercise

**Objective**: Build and review a small Terraform module that demonstrates module contracts, stable `for_each` keys, validation, outputs, lifecycle rules, and plan inspection. The exercise uses local files so you can practice Terraform mechanics without cloud credentials. The same review habits transfer to AWS, Kubernetes, and Helm providers.

### Part 1: Create the exercise repository

Create a working directory with one reusable module and one environment stack. This shape mirrors a production repository, but the provider writes local files so the exercise is safe to run on a laptop. The `local` provider may be downloaded during `terraform init`, so run this in an environment with normal Terraform provider registry access.

```bash
mkdir -p terraform-deep-dive/modules/service-manifest
mkdir -p terraform-deep-dive/environments/dev
cd terraform-deep-dive
```

### Part 2: Write the module contract

Create the module variable definitions. The module accepts an application name, environment, port map, and tags. Notice that ports are keyed by service name, which gives Terraform stable addresses when services are added or removed.

```bash
cat > modules/service-manifest/variables.tf << 'EOF'
variable "app_name" {
  description = "Lowercase application name used in generated manifest files."
  type        = string

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]*$", var.app_name))
    error_message = "app_name must start with a lowercase letter and contain only lowercase letters, numbers, and hyphens."
  }
}

variable "environment" {
  description = "Deployment environment."
  type        = string

  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "environment must be dev, staging, or production."
  }
}

variable "service_ports" {
  description = "Map of service names to TCP ports."
  type        = map(number)

  validation {
    condition = alltrue([
      for port in values(var.service_ports) : port > 0 && port < 65536
    ])
    error_message = "Every service port must be between 1 and 65535."
  }
}

variable "tags" {
  description = "Tags included in each generated manifest."
  type        = map(string)
  default     = {}
}
EOF
```

### Part 3: Add module logic and lifecycle behavior

Create the module implementation. The local files stand in for cloud resources, but the Terraform patterns are real: derived locals, `for_each`, stable keys, generated content, and lifecycle protection.

```bash
cat > modules/service-manifest/main.tf << 'EOF'
locals {
  common_tags = merge(var.tags, {
    Application = var.app_name
    Environment = var.environment
    ManagedBy   = "terraform"
  })

  manifests = {
    for service_name, port in var.service_ports :
    service_name => {
      filename = "${var.app_name}-${var.environment}-${service_name}.json"
      content = jsonencode({
        app         = var.app_name
        environment = var.environment
        service     = service_name
        port        = port
        tags        = local.common_tags
      })
    }
  }
}

resource "local_file" "manifest" {
  for_each = local.manifests

  filename = "${path.module}/../../generated/${each.value.filename}"
  content  = each.value.content

  lifecycle {
    create_before_destroy = true
  }
}
EOF

cat > modules/service-manifest/outputs.tf << 'EOF'
output "manifest_files" {
  description = "Generated manifest file paths keyed by service name."
  value       = { for name, file in local_file.manifest : name => file.filename }
}

output "service_names" {
  description = "Sorted service names managed by this module."
  value       = sort(keys(var.service_ports))
}
EOF

cat > modules/service-manifest/versions.tf << 'EOF'
terraform {
  required_version = ">= 1.6.0"

  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
}
EOF
```

### Part 4: Create the development environment stack

Create a root module that calls the reusable module. This is the layer where environment choices belong. The reusable module owns the pattern, while the environment stack owns the specific application name, service set, and tags.

```bash
cat > environments/dev/main.tf << 'EOF'
terraform {
  required_version = ">= 1.6.0"

  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
}

module "service_manifest" {
  source = "../../modules/service-manifest"

  app_name    = "checkout"
  environment = "dev"

  service_ports = {
    api     = 8080
    metrics = 9090
  }

  tags = {
    Team       = "platform"
    CostCenter = "cc-1234"
  }
}

output "manifest_files" {
  value = module.service_manifest.manifest_files
}
EOF
```

### Part 5: Initialize, validate, and review the first plan

Run the same basic gates you would expect in a production Terraform review. The first plan should propose two generated files, one for `api` and one for `metrics`. Read the addresses carefully and notice that they are keyed by service name rather than numeric index.

```bash
cd environments/dev
terraform init
terraform fmt -check -recursive ../..
terraform validate
terraform plan -out=tfplan
terraform show -no-color tfplan > tfplan.txt
```

### Part 6: Apply, then simulate a safe change

Apply the plan, then add a new service to the map. The important observation is that adding `worker` should create one new addressed object without renaming `api` or `metrics`.

```bash
terraform apply tfplan
```

Edit `environments/dev/main.tf` so the `service_ports` map becomes:

```hcl
  service_ports = {
    api     = 8080
    metrics = 9090
    worker  = 7070
  }
```

Run another plan and inspect the result.

```bash
terraform fmt -recursive ../..
terraform validate
terraform plan
```

### Part 7: Simulate a refactor with a moved block

Now rename the module from `service_manifest` to `service_files` in the root module. Before adding a moved block, run a plan and observe that Terraform sees the old module address disappear and a new one appear. Then add a moved block to teach Terraform the refactor.

```hcl
moved {
  from = module.service_manifest
  to   = module.service_files
}
```

After adding the moved block and updating the module block name, run the plan again. The plan should show address movement rather than destroy and create behavior. This is the same technique you use when moving real cloud resources into modules or renaming resources in production states.

```bash
terraform fmt -recursive ../..
terraform validate
terraform plan
```

### Part 8: Success Criteria

- [ ] The module has `variables.tf`, `main.tf`, `outputs.tf`, and `versions.tf`.
- [ ] Variables include descriptions and validation rules that fail early for bad input.
- [ ] The module uses `for_each` with stable service-name keys rather than `count`.
- [ ] The root environment stack owns environment-specific values instead of hardcoding them inside the module.
- [ ] `terraform fmt -check -recursive ../..` passes before intentional edits and `terraform fmt -recursive ../..` fixes formatting after edits.
- [ ] `terraform validate` passes in the environment directory.
- [ ] The first plan proposes generated files keyed by `api` and `metrics`.
- [ ] Adding `worker` proposes one new object without renaming the existing services.
- [ ] The module rename is handled with a `moved` block rather than replacement.
- [ ] You can explain which part of the plan proves the refactor is safe.

### Part 9: Reflection Questions

After completing the exercise, write short answers for yourself or your team review. Which values belonged in the module and which belonged in the environment stack? Which address would have been unstable if the module had used `count`? What evidence in the plan told you the moved block worked? If this had been an AWS module instead of local files, which resources would require deeper review before apply?

---

## Next Module

Continue to [Module 7.2: OpenTofu](../module-7.2-opentofu/) to learn about the open-source fork of Terraform and its unique features.

## Sources

- [HashiCorp Terraform Announcement](https://www.hashicorp.com/blog/terraform-announcement) — Primary-source background on Terraform's original 2014 release and early goals.
- [Terraform v1.1.0 Release Notes](https://github.com/hashicorp/terraform/releases/tag/v1.1.0) — Documents moved blocks and other refactoring-related language features.
- [Terraform v1.5.0 Release Notes](https://github.com/hashicorp/terraform/releases/tag/v1.5.0) — Documents declarative import blocks and generated configuration support.

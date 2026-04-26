---
title: "Module 7.2: OpenTofu - The Open Source Fork"
slug: platform/toolkits/infrastructure-networking/iac-tools/module-7.2-opentofu
sidebar:
  order: 3
---

# Module 7.2: OpenTofu - The Open Source Fork

## Complexity: [MEDIUM]

## Time to Complete: 50 minutes

## Prerequisites

Before starting this module, you should have completed [Module 7.1: Terraform Deep Dive](../module-7.1-terraform/) and should be comfortable reading HCL, running `init`, `plan`, and `apply`, and explaining why remote state and state locking matter in team environments.

You do not need to be an OpenTofu expert before beginning, but you should already understand that infrastructure as code tools keep a desired configuration, compare it to real infrastructure, and record mappings between configuration and remote objects in state.

You should also have basic awareness of open-source licensing because OpenTofu is not only a technical fork; it is also a governance and risk-management choice that affects procurement, platform strategy, and long-term maintainability.

---

## Learning Outcomes

After completing this module, you will be able to:

- **Evaluate** whether OpenTofu or Terraform is the better fit for a platform team based on licensing, support, workflow, and feature requirements.
- **Migrate** a small Terraform-style project to OpenTofu while preserving state, provider constraints, and CI behavior.
- **Design** an OpenTofu state-protection strategy using backend controls, native state encryption, and disciplined key rollover.
- **Debug** migration and planning failures caused by registry assumptions, remote backend usage, encrypted state configuration, or partial targeting.
- **Compare** OpenTofu-specific features such as provider-defined functions, provider iteration, import blocks, and `-exclude` against their operational trade-offs.

---

## Why This Module Matters

A platform team is asked to standardize infrastructure delivery across dozens of application squads after a licensing change creates procurement uncertainty. The team already has hundreds of modules, a remote state pattern, CI jobs that run plans on pull requests, and security reviewers who care deeply about secrets leaking into state. Rewriting everything would be wasteful, but doing nothing may leave the organization tied to a licensing and support model it no longer understands.

The lead engineer does not start by asking, "What command replaces Terraform?" That is the easy part. She asks which state files can be touched safely, which CI jobs assume Terraform Cloud behavior, which modules rely on provider installation details, and whether the organization needs a fully open-source toolchain for commercial or policy reasons. OpenTofu becomes valuable when it solves those operational problems without forcing a full rewrite of the infrastructure estate.

This module treats OpenTofu as a real platform-engineering decision, not as a branding swap. You will learn where it is intentionally compatible, where it adds new features, where migration risk hides, and how to run a disciplined evaluation before changing the tool used to manage production infrastructure.

---

## 1. The Mental Model: Fork, Compatibility, and Control

OpenTofu is a community-governed infrastructure as code tool that continues the Terraform-style workflow under an open-source license. It uses the same broad model you learned in the Terraform module: write HCL, install providers, build a dependency graph, compare desired configuration with observed infrastructure, and apply the resulting plan. The binary changes from `terraform` to `tofu`, but the engineering decision is larger than a command rename.

The fork matters because infrastructure tooling is unusually sticky. Once a platform team standardizes modules, provider versions, policy checks, state backends, CI templates, and runbooks, the chosen tool becomes part of the organization's operating system. A license or governance change can therefore become a platform risk even when day-to-day syntax still works.

OpenTofu preserves familiar HCL structure so that teams can evaluate it without rewriting their entire estate. The root block is still named `terraform`, providers still use `required_providers`, resources still use provider-specific resource types, and state still tracks the binding between HCL resource addresses and real infrastructure objects. This compatibility is what makes migration plausible rather than heroic.

OpenTofu is not identical to Terraform in every possible behavior, and treating it as perfectly identical is a common source of sloppy migrations. Provider installation, remote execution platforms, encryption configuration, feature availability, and CLI flags can differ by version. Senior engineers treat "mostly compatible" as a starting hypothesis that must be validated against their own modules and state.

```ascii
┌──────────────────────────────────────────────────────────────────────┐
│                  Terraform-Style IaC Mental Model                    │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  HCL files             Providers             State                   │
│  ┌──────────┐          ┌──────────┐          ┌──────────────┐        │
│  │ desired  │─────────▶│ cloud or │─────────▶│ resource map │        │
│  │ config   │          │ API code │          │ and outputs  │        │
│  └──────────┘          └──────────┘          └──────────────┘        │
│       │                      │                       │               │
│       │                      │                       │               │
│       ▼                      ▼                       ▼               │
│  tofu plan            provider reads          diff between           │
│  builds graph         real objects            config and state       │
│                                                                      │
│       ┌──────────────────────────────────────────────────────┐       │
│       │ tofu apply updates remote infrastructure and state   │       │
│       └──────────────────────────────────────────────────────┘       │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

The practical difference is control. OpenTofu gives teams an open-source governance path and has added features such as native state and plan encryption, provider-defined functions, provider iteration, and negative targeting with `-exclude`. These features can be useful, but only when you connect each one to a real operational problem rather than adopting them because they are new.

Pause and predict: if a team replaces the binary in CI but leaves Terraform Cloud remote backend configuration untouched, what part of the workflow is most likely to fail first? Think about where state is stored, where plans are executed, and which service owns authentication before reading the next paragraph.

The most likely failure is not HCL syntax. It is the execution and state-management boundary. A local `tofu plan` may parse configuration successfully, while CI fails because it assumes a remote platform, remote workspace variables, Sentinel policy checks, or backend behavior that OpenTofu does not provide through the same commercial service. Migration work therefore begins at the platform boundary, not inside the easiest resource blocks.

A beginner should remember the simple rule: OpenTofu can often run Terraform-style configuration with minimal code changes. A senior engineer should add the harder rule: compatibility must be proven for the exact providers, backends, workflow integrations, and state protections used by the organization.

| Decision Area | Beginner Question | Senior Platform Question |
|---|---|---|
| CLI usage | Can I run `tofu plan` instead of `terraform plan`? | Which CI jobs, wrappers, policy checks, and automation contracts assume the old binary or platform? |
| Configuration | Does my HCL parse? | Which modules rely on version-specific behavior, provider mirrors, or remote workspace variables? |
| State | Can OpenTofu read my state? | How will state locking, encryption, access control, backup, and rollback work during migration? |
| Governance | Is it open source? | Does the license, foundation model, support path, and roadmap match procurement and risk requirements? |
| Features | What can OpenTofu do that Terraform cannot? | Which new features reduce real operational risk, and which ones increase coupling to OpenTofu? |

The command surface is intentionally familiar. The following commands are not special magic; they are the same workflow steps you already know, executed by OpenTofu.

```bash
tofu fmt -recursive
tofu init
tofu validate
tofu plan -out=tfplan
tofu apply tfplan
```

Do not hide the binary change behind a global shell alias during a migration review. An alias such as `alias terraform=tofu` may help a developer explore locally, but it makes CI logs, runbooks, and incident timelines ambiguous. During evaluation, explicit commands make it clear which engine produced which plan.

```bash
# Acceptable for a temporary local shell while experimenting.
alias terraform=tofu

# Better for committed automation because the engine is visible in logs.
tofu init
tofu plan -out=tfplan
```

The OpenTofu configuration language still uses `terraform` for the top-level settings block because that block name is part of the HCL language lineage. This can surprise learners who expect an `opentofu` block. Do not rename it; OpenTofu expects `terraform { ... }` for required versions, providers, backends, and encryption configuration.

```hcl
terraform {
  required_version = ">= 1.9.0"

  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
}
```

The key takeaway for this first section is that OpenTofu is easiest to understand as a compatible engine with different governance and some divergent capabilities. That framing keeps the module practical: you will migrate safely, protect state deliberately, and evaluate features through operational scenarios.

---

## 2. Migration Readiness: Prove the Boundary Before You Touch Production

A safe OpenTofu migration starts with discovery, not installation. The first job is to identify the pieces of your current Terraform-style workflow that are merely local CLI behavior and the pieces that depend on a hosted platform, special backend, provider mirror, or policy engine. Most migrations fail when teams confuse those categories.

Imagine a team that manages network, Kubernetes, and database infrastructure through three repositories. The network repository uses an S3-compatible backend, the Kubernetes repository reads network outputs through remote state, and the database repository runs plans in a commercial remote platform. The same binary swap has three different risk profiles because state and execution are handled differently in each repository.

A practical readiness review has defined inputs and outputs. The inputs are the current HCL files, lock files, backend configuration, CI workflow definitions, provider mirrors, state locations, and any run logs from recent plans. The output is a migration decision that says "safe to pilot," "needs backend redesign," or "defer until platform dependency is replaced."

```ascii
┌──────────────────────────────────────────────────────────────────────┐
│                    Migration Readiness Flow                          │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Repository scan                                                     │
│       │                                                              │
│       ▼                                                              │
│  Backend classification ── remote service? ── yes ──▶ redesign path  │
│       │                                  │                           │
│       │                                  no                          │
│       ▼                                                              │
│  Provider and lock check                                             │
│       │                                                              │
│       ▼                                                              │
│  Local OpenTofu init and plan                                        │
│       │                                                              │
│       ▼                                                              │
│  CI pilot with explicit tofu binary                                  │
│       │                                                              │
│       ▼                                                              │
│  Production migration only after no-op plan is proven                │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

The first check is the current Terraform version and provider lock state. You want to know which engine created the lock file, which provider versions are pinned, and whether the repository depends on behavior from a newer Terraform release that OpenTofu may not mirror exactly. A small scriptable inventory is better than a verbal assumption.

```bash
terraform version || true
test -f .terraform.lock.hcl && sed -n '1,80p' .terraform.lock.hcl
find . -maxdepth 3 -name "*.tf" -print
```

The second check is backend usage. Local state is easy to test but rarely appropriate for teams. Object storage backends with locking can usually be piloted in a controlled branch. Hosted remote execution or commercial workspace configuration requires a design decision because it may include variables, policy, notifications, state history, and approval workflows that are not represented in HCL alone.

```bash
grep -R 'backend "' -n . --include='*.tf' || true
grep -R 'cloud {' -n . --include='*.tf' || true
grep -R 'remote' -n . --include='*.tf' || true
```

The third check is provider installation. Most common providers can be used through OpenTofu-compatible registry resolution, but regulated environments often use local mirrors, network mirrors, or allowlists. If the old workflow depended on a Terraform CLI configuration file, reproduce that configuration deliberately for OpenTofu rather than assuming direct internet installation will be allowed in CI.

```hcl
provider_installation {
  filesystem_mirror {
    path    = "providers"
    include = ["registry.opentofu.org/hashicorp/*"]
  }

  direct {
    exclude = ["registry.opentofu.org/hashicorp/*"]
  }
}
```

The fourth check is execution environment. A CI job that installs Terraform, runs `terraform init`, and comments a plan on a pull request is straightforward to adapt. A CI job that delegates execution to a hosted platform, relies on workspace variables, or enforces policies through a proprietary policy engine needs a replacement architecture, not just a setup action change.

Pause and predict: your local `tofu plan` returns "No changes," but the CI job fails during `init` with a provider installation error. Which file or setting would you inspect first, and why would checking resource HCL be a slower path?

The best first place to inspect is provider installation configuration and the lock file, not the resource declarations. A no-op local plan proves that the resource graph can be built on one machine, but CI may use different credentials, provider mirrors, network access, and cache paths. HCL resource syntax is less likely to be the problem if the failure happens before planning.

### Worked Example: Migrating a Small Service Repository

The problem: a team owns a small service repository that creates a generated configuration file during development and uses a local backend in a sandbox. The team wants a low-risk OpenTofu pilot before migrating the production network repository. The inputs are one HCL file, no remote backend, a provider lock file, and a CI workflow that currently runs Terraform commands.

The expected outcome is a no-op OpenTofu plan after initialization, followed by a CI workflow that uses the explicit `tofu` command. Because this is a sandbox with local resources, the migration can be proven without touching cloud infrastructure or production state.

Create a minimal Terraform-style project that OpenTofu can run locally. This example uses the `random` and `local` providers so the learner can test the engine without cloud credentials.

```bash
mkdir -p opentofu-pilot
cd opentofu-pilot
```

```bash
cat > main.tf <<'EOF'
terraform {
  required_version = ">= 1.9.0"

  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }

    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

resource "random_pet" "service" {
  length = 2
}

resource "local_file" "service_config" {
  filename = "${path.module}/service.conf"
  content  = "service_name=${random_pet.service.id}\nmanaged_by=opentofu\n"
}

output "service_name" {
  value = random_pet.service.id
}
EOF
```

Run the standard OpenTofu workflow and save the plan before applying. Saving the plan matters because it separates review from execution, and that habit becomes important when the same workflow moves from a sandbox to production.

```bash
tofu fmt
tofu init
tofu validate
tofu plan -out=tfplan
tofu apply tfplan
```

Verify the output through both the managed file and OpenTofu state. The file proves the local provider created the expected artifact; the state list proves OpenTofu is tracking the declared resources.

```bash
cat service.conf
tofu state list
tofu output service_name
```

Now imagine this repository already existed and had been applied by Terraform. The migration test would not be "does `tofu apply` create something?" The better test would be "does `tofu plan` show no unintended changes after reading the existing state?" In production, a clean no-op plan is usually the migration gate.

```bash
tofu init
tofu plan -detailed-exitcode
```

A detailed exit code gives CI a stronger signal than reading text. Exit code zero means no changes, exit code two means a non-empty diff exists, and exit code one means an error occurred. That distinction lets your pipeline fail only on errors or unexpected changes, depending on the migration phase.

```bash
tofu plan -detailed-exitcode
status=$?

if [ "$status" -eq 0 ]; then
  echo "OpenTofu produced a no-op plan."
elif [ "$status" -eq 2 ]; then
  echo "OpenTofu produced changes; review before applying."
else
  echo "OpenTofu planning failed."
  exit "$status"
fi
```

A CI migration should make the binary explicit. The following GitHub Actions example avoids global aliases, uses a pinned OpenTofu setup step, and keeps the plan as the reviewed artifact. In production, you would also configure remote state credentials and policy checks appropriate to your platform.

```yaml
name: OpenTofu Pilot

on:
  pull_request:
    paths:
      - "**/*.tf"
      - ".github/workflows/opentofu.yml"

jobs:
  plan:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup OpenTofu
        uses: opentofu/setup-opentofu@v1
        with:
          tofu_version: "1.10.0"

      - name: Format check
        run: tofu fmt -check -recursive

      - name: Init
        run: tofu init

      - name: Validate
        run: tofu validate

      - name: Plan
        run: tofu plan -out=tfplan
```

Stop and think: if this workflow passes for a local-provider sandbox, what has it not proven yet? Name at least three production risks that remain outside the worked example.

It has not proven remote state locking, cloud credentials, provider mirror policy, secrets handling, remote-state data dependencies, drift behavior, cost impact, or human approval flow. A sandbox pilot validates the engine and basic CI shape, but production migration still needs a state and governance design. That is why the next section focuses on state rather than new syntax.

Migration should be staged by blast radius. Start with a sandbox or development stack, then move to an internal non-critical service, then to shared foundational infrastructure only after the plan behavior is understood. The worst candidate for a first migration is a global networking stack that many teams depend on and few people understand.

| Migration Stage | Appropriate Target | Required Evidence Before Moving On |
|---|---|---|
| Sandbox | Local resources or disposable cloud account | Init, validate, plan, apply, destroy, and CI all work with explicit `tofu` commands |
| Development | Non-critical stack with remote backend | OpenTofu reads state, locking works, and no-op plans are reproducible |
| Shared service | Internal stack consumed by a few teams | Remote-state consumers still work and rollback procedure is documented |
| Production foundation | Network, identity, or cluster baseline | Cross-team approval, backup, encryption, and incident runbooks are complete |

The senior-level habit is to write down the rollback point before changing state. If OpenTofu only reads existing state and produces a plan, rollback is simply returning to the previous binary. Once you apply with OpenTofu-specific features such as native state encryption, rollback may require intentionally removing or migrating those features first.

---

## 3. State Protection: Encryption, Backends, and Rollover

State is the most important artifact in Terraform-style infrastructure as code because it stores resource identities, outputs, dependency metadata, and sometimes sensitive values. Platform teams often protect cloud resources carefully while treating state as a boring implementation file. That is a mistake. Anyone who can read state may learn database endpoints, generated passwords, service account identifiers, or enough topology detail to plan an attack.

OpenTofu's native state and plan encryption is one of its most important differentiators. Backend encryption such as object-store server-side encryption protects the object at rest inside the storage service, but native OpenTofu encryption protects the serialized state payload itself. Those controls can complement each other rather than compete.

A good state-protection design has layers. The backend controls who can read and write the state object, the lock prevents concurrent writes, the encryption method protects the state payload, the key provider determines how encryption keys are derived or retrieved, and operational procedures define rotation, backup, and emergency recovery.

```ascii
┌──────────────────────────────────────────────────────────────────────┐
│                    State Protection Layers                           │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Human and CI identity                                               │
│       │                                                              │
│       ▼                                                              │
│  Backend access control                                              │
│       │                                                              │
│       ▼                                                              │
│  State locking                                                       │
│       │                                                              │
│       ▼                                                              │
│  OpenTofu state and plan encryption                                  │
│       │                                                              │
│       ▼                                                              │
│  Key provider and rotation policy                                    │
│       │                                                              │
│       ▼                                                              │
│  Backup, restore, and break-glass procedure                          │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

For a simple learning environment, PBKDF2 passphrase-based encryption is easy to demonstrate because it does not require cloud KMS credentials. For production, a managed KMS is usually preferable because it centralizes key lifecycle, audit logging, access policy, and rotation. The right key provider depends on your organization, but the design question is always the same: who can decrypt state, under what conditions, and how would you rotate the secret without losing access?

When encrypting a pre-existing unencrypted state file, OpenTofu needs an explicit migration path. That path uses an `unencrypted` method as a fallback so OpenTofu can read the old state once and then write the new encrypted state. After the state has been rewritten, remove the fallback and consider enforcing encryption so future operations fail rather than silently reading unencrypted state.

```hcl
variable "state_passphrase" {
  description = "Passphrase used only for the local learning example."
  type        = string
  sensitive   = true
}

terraform {
  encryption {
    method "unencrypted" "migration" {}

    key_provider "pbkdf2" "main" {
      passphrase = var.state_passphrase
    }

    method "aes_gcm" "state_method" {
      keys = key_provider.pbkdf2.main
    }

    state {
      method = method.aes_gcm.state_method

      fallback {
        method = method.unencrypted.migration
      }
    }

    plan {
      method = method.aes_gcm.state_method

      fallback {
        method = method.unencrypted.migration
      }
    }
  }
}
```

The workflow for introducing encryption is deliberately cautious. First, back up the state through the backend's normal mechanism. Second, add the encryption configuration with a fallback for unencrypted state. Third, run `tofu plan` and `tofu apply` with the passphrase or KMS credentials available. Fourth, confirm the state can be read by a fresh `tofu plan`. Fifth, remove the fallback and enforce the encrypted method.

```bash
export TF_VAR_state_passphrase="use-a-long-learning-passphrase-only-for-this-lab"
tofu init
tofu plan -out=tfplan
tofu apply tfplan
tofu plan
```

After migration, tighten the configuration. The fallback was useful during the transition, but keeping it forever weakens the signal you expect from encrypted state. When `enforced = true` is appropriate for your version and backend combination, use it to make accidental unencrypted reads or writes fail visibly.

```hcl
variable "state_passphrase" {
  description = "Passphrase used only for the local learning example."
  type        = string
  sensitive   = true
}

terraform {
  encryption {
    key_provider "pbkdf2" "main" {
      passphrase = var.state_passphrase
    }

    method "aes_gcm" "state_method" {
      keys = key_provider.pbkdf2.main
    }

    state {
      method   = method.aes_gcm.state_method
      enforced = true
    }

    plan {
      method   = method.aes_gcm.state_method
      enforced = true
    }
  }
}
```

What would happen if you removed the fallback before the first encrypted apply on an existing unencrypted state file? The plan may fail because OpenTofu refuses to read state using only the new encrypted method when the current state is still unencrypted. This is a useful failure because it prevents accidental trust in an unprotected state file, but it can surprise teams that skip the migration sequence.

Key rollover is the senior version of the same problem. You need OpenTofu to read data encrypted with the old method and write data with the new method. That is exactly what a fallback block is for: it lets old state be read during the transition while new state is written with the current method.

```hcl
variable "old_state_passphrase" {
  description = "Previous state passphrase used during rollover."
  type        = string
  sensitive   = true
}

variable "new_state_passphrase" {
  description = "New state passphrase used after rollover."
  type        = string
  sensitive   = true
}

terraform {
  encryption {
    key_provider "pbkdf2" "old" {
      passphrase = var.old_state_passphrase
    }

    key_provider "pbkdf2" "new" {
      passphrase = var.new_state_passphrase
    }

    method "aes_gcm" "old_method" {
      keys = key_provider.pbkdf2.old
    }

    method "aes_gcm" "new_method" {
      keys = key_provider.pbkdf2.new
    }

    state {
      method = method.aes_gcm.new_method

      fallback {
        method = method.aes_gcm.old_method
      }
    }
  }
}
```

State encryption does not replace access control. If every engineer and every CI job can retrieve the passphrase or use the KMS decrypt permission, encryption becomes mostly a storage hardening feature rather than a meaningful authorization boundary. The principle of least privilege still applies: plan jobs may need read access, apply jobs may need write access, and break-glass access should be logged.

State encryption also does not remove sensitive values from state. A value can be encrypted at rest and still appear in plaintext to an authorized plan process, provider process, or local console command. Marking outputs as sensitive reduces accidental display, but the underlying state may still contain sensitive data. The strongest pattern is to avoid placing long-lived secrets in state whenever the provider and architecture allow it.

| Protection Layer | What It Helps With | What It Does Not Solve |
|---|---|---|
| Backend access policy | Limits who can read or write the state object | Does not hide sensitive values from authorized readers |
| Backend locking | Prevents concurrent writes from corrupting state | Does not prevent a bad plan from being applied |
| Native state encryption | Protects serialized state payload and plan files | Does not replace IAM, KMS policy, or secret minimization |
| Sensitive outputs | Reduces accidental terminal and log exposure | Does not guarantee absence from state |
| State backups | Allows recovery after corruption or operator error | Does not prove the restored state matches real infrastructure |

A safe production pattern uses object storage with versioning, lock support appropriate to the backend, restricted identity permissions, native encryption, and a tested restore procedure. The restore procedure matters because encrypted state adds another dependency during incidents: the team must be able to retrieve both the correct state version and the correct decryption material.

Debugging encrypted state requires discipline. If a fresh clone cannot run `tofu plan`, ask whether the encryption configuration is present, whether the key provider can resolve during `init`, whether environment variables are set, whether the backend points to the expected object, and whether the state was written with an older method. Do not start by editing resources to "see if it works"; that changes the wrong variable.

---

## 4. OpenTofu Features Through Operational Scenarios

OpenTofu-specific features are most useful when you frame them as answers to real infrastructure problems. A list of features is easy to forget. A problem-to-solution mapping is easier to apply during design review, migration planning, or an incident.

The first scenario is state confidentiality. A security review finds that plan artifacts and state snapshots can include values that should not appear in unencrypted build storage. OpenTofu's native state and plan encryption can reduce that risk when paired with backend access controls and short-lived CI credentials.

The second scenario is multi-region provider duplication. A platform team manages similar resources across several regions and maintains nearly identical provider blocks. Provider iteration lets the root module create multiple instances of an aliased provider configuration from a collection, reducing duplicated HCL while preserving explicit provider selection.

```hcl
variable "aws_regions" {
  description = "Regions where the platform baseline is enabled."
  type = map(object({
    cidr_block = string
  }))
}

provider "aws" {
  alias    = "by_region"
  for_each = var.aws_regions

  region = each.key
}

resource "aws_vpc" "regional" {
  for_each = var.aws_regions

  provider   = aws.by_region[each.key]
  cidr_block = each.value.cidr_block

  tags = {
    Name   = "platform-${each.key}"
    Source = "opentofu"
  }
}
```

Provider iteration is powerful, but it changes the lifecycle of provider instances. If you remove a region from the provider collection before destroying resources that still depend on that provider instance, OpenTofu may not have the provider configuration needed to destroy those resources cleanly. A careful design separates "regions where provider exists" from "regions where resources are enabled" so provider instances outlive the resources they manage.

```hcl
variable "provider_regions" {
  description = "Regions that still need provider instances, including regions being decommissioned."
  type        = set(string)
}

variable "enabled_regions" {
  description = "Regions where resources should currently exist."
  type        = set(string)
}

provider "aws" {
  alias    = "by_region"
  for_each = var.provider_regions

  region = each.key
}

resource "aws_s3_bucket" "logs" {
  for_each = var.enabled_regions

  provider = aws.by_region[each.key]
  bucket   = "platform-logs-${each.key}"

  tags = {
    ManagedBy = "OpenTofu"
  }
}
```

Pause and predict: if `enabled_regions` removes `eu-west-1` but `provider_regions` still includes it, what can OpenTofu do during the next apply? What risk appears if both variables remove the region at the same time?

With the provider still present, OpenTofu can use that regional provider instance to destroy resources that are no longer desired. If both variables remove the region at the same time, the graph may no longer contain the provider instance needed to destroy the remote objects. This is why provider lifecycle sometimes needs a superset variable rather than matching the resource loop exactly.

The third scenario is importing existing infrastructure. Teams often inherit manually created resources and need to bring them under code without writing one import command per object. OpenTofu supports import blocks, and looped import patterns can reduce repetitive import declarations when the existing resources follow a predictable map.

```hcl
locals {
  existing_files = {
    app_config = "app.conf"
    db_config  = "db.conf"
    ops_config = "ops.conf"
  }
}

import {
  for_each = local.existing_files
  to       = local_file.imported[each.key]
  id       = each.value
}

resource "local_file" "imported" {
  for_each = local.existing_files

  filename = each.value
  content  = "managed_by=opentofu\nname=${each.key}\n"
}
```

For cloud resources, import needs more care because configuration must match the real object closely enough to avoid unintended changes after import. The import block only establishes the state mapping; it does not magically infer every desired argument. Senior practitioners import in small batches, run plans after each batch, and adjust configuration until the planned diff matches the intended ownership change.

The fourth scenario is feature-specific expression logic. Provider-defined functions allow providers to expose functions under names such as `provider::<provider_name>::<function_name>`. This can remove awkward string parsing or external data wrappers when a provider has domain-specific parsing logic. The trade-off is portability: a module that depends on provider-defined functions is tied more tightly to OpenTofu and to providers that expose those functions.

```hcl
terraform {
  required_providers {
    terraform = {
      source  = "terraform.io/builtin/terraform"
      version = "1.0.0"
    }
  }
}

locals {
  generated_tfvars = provider::terraform::encode_tfvars({
    environment = "dev"
    replicas    = 2
    managed_by  = "opentofu"
  })
}
```

Use provider-defined functions when they simplify a real maintenance problem and the dependency is acceptable. Avoid them when a built-in function or clearer input variable would do the same job. The goal is not to use every advanced feature; the goal is to keep infrastructure code understandable during reviews and incidents.

The fifth scenario is negative targeting. Sometimes a plan contains one resource that must be held back temporarily while the rest of the stack proceeds. OpenTofu's `-exclude` flag lets you plan or apply everything except a specified resource or module. That can be useful during recovery or phased deployments, but it should not become the normal way to split large stacks.

```bash
tofu plan -exclude=local_file.canary -out=tfplan
tofu apply tfplan
```

Negative targeting has dependency consequences. If another resource depends on the excluded resource, OpenTofu must also avoid operations that require that dependency. This behavior protects graph correctness, but it can surprise operators who expected only one address to be skipped. Always inspect the plan after using `-exclude`; never assume the rest of the graph is unchanged.

For larger operations, OpenTofu versions that support exclude files let teams store excluded addresses in a file. That makes emergency targeting more reviewable in CI than a long command line, but it still remains an exceptional operation. If a stack regularly needs exclude files, the better design may be smaller stacks with clearer ownership boundaries.

```bash
cat > excludes.txt <<'EOF'
# Hold back the canary file while validating the rest of the stack.
local_file.canary
EOF

tofu plan -exclude-file=excludes.txt -out=tfplan
```

| Feature | Scenario It Solves | Senior-Level Caution |
|---|---|---|
| State and plan encryption | State contains sensitive topology or generated values | Encryption must be paired with IAM, key policy, backups, and tested recovery |
| Provider iteration | Multi-region provider blocks are duplicated and error-prone | Provider instances must outlive resources during decommissioning |
| Looped imports | Existing resources need to be brought under code in batches | Imported configuration still needs careful drift review |
| Provider-defined functions | Provider-specific parsing is clearer as a function than manual string logic | Modules become less portable and depend on provider support |
| `-exclude` | One resource must be held back during an exceptional operation | Routine use can hide drift and signal the stack should be split |
| `-exclude-file` | CI needs a reviewable list of temporary exclusions | A persistent exclude file is usually an architecture smell |

The operating principle is simple: advanced features should reduce operational risk or repeated maintenance cost. If a feature only makes the module look clever, it is probably the wrong feature. OpenTofu gives senior engineers more control, but control without review discipline becomes another source of incidents.

---

## 5. Choosing OpenTofu, Terraform, or a Mixed Transition

The choice between OpenTofu and Terraform is not a moral quiz; it is a platform decision with technical, legal, financial, and operational dimensions. A team that already depends heavily on Terraform Cloud, Sentinel, private registries, and vendor support may choose to stay with Terraform for a while. Another team that needs open-source governance, native encryption, and vendor-neutral execution may choose OpenTofu. Both decisions can be defensible when they are explicit.

A weak decision says, "OpenTofu is open source, so we should switch." A stronger decision says, "Our platform strategy requires an open-source IaC engine, our backends are already object-storage based, our policy checks are independent of Terraform Cloud, and our pilot produced no-op plans across these representative stacks." The second statement connects values to evidence.

```ascii
┌──────────────────────────────────────────────────────────────────────┐
│                    IaC Engine Decision Matrix                        │
├───────────────────────────────┬──────────────────┬───────────────────┤
│ Factor                        │ OpenTofu Fit     │ Terraform Fit     │
├───────────────────────────────┼──────────────────┼───────────────────┤
│ Open-source governance        │ Strong           │ Weaker under BSL  │
│ Existing hosted platform use  │ Depends          │ Strong            │
│ Native state encryption       │ Strong           │ Platform-specific │
│ Vendor commercial support     │ Third-party path │ First-party path  │
│ Provider ecosystem            │ Broadly familiar │ Broadly familiar  │
│ CI portability                │ Strong           │ Depends on setup  │
│ Policy-as-code integration    │ External tools   │ Sentinel option   │
│ Migration complexity          │ Low to medium    │ None if staying   │
└───────────────────────────────┴──────────────────┴───────────────────┘
```

Licensing is a real engineering concern because it affects what vendors, internal platform teams, and commercial service providers are allowed to do. Engineers do not need to become lawyers, but they do need to identify when a licensing model conflicts with a business model or procurement policy. When in doubt, involve legal and procurement early rather than burying the issue in a technical spike.

Support is another real concern. Some organizations require first-party vendor support for critical infrastructure tools. Others are comfortable with community support plus third-party vendors. OpenTofu's Linux Foundation governance may satisfy open-source policy, but governance does not automatically answer every enterprise support requirement. Treat support as a requirement to design around, not a footnote.

Feature velocity cuts both ways. OpenTofu has added capabilities that platform engineers requested for years, but using new features can create a one-way door for modules that must remain compatible with Terraform. The more OpenTofu-specific your modules become, the more you should document that choice and stop pretending the codebase is engine-neutral.

A mixed transition is often the most realistic path. One repository may move to OpenTofu quickly because it uses object-storage state and generic CI. Another repository may stay on Terraform until remote execution, policy, and workspace variables are replaced. The dangerous pattern is silent inconsistency where engineers cannot tell which engine owns which state.

```ascii
┌──────────────────────────────────────────────────────────────────────┐
│                    Mixed Transition Operating Model                  │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Repository label: engine = opentofu                                 │
│       │                                                              │
│       ├── CI installs tofu explicitly                                │
│       ├── README documents backend and encryption                    │
│       ├── State owner approves engine-specific features              │
│       └── Runbook says Terraform must not write this state           │
│                                                                      │
│  Repository label: engine = terraform                                │
│       │                                                              │
│       ├── CI installs terraform explicitly                           │
│       ├── Remote platform dependency is tracked                      │
│       ├── Migration blockers are visible                             │
│       └── OpenTofu experiments use copied state only                 │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

Never let both engines write the same state as a casual habit. While state formats may be compatible for many workflows, the moment one engine writes feature-specific metadata or encrypted payloads, the other engine may not understand it. Choose one owner per state file, document it, and make CI enforce that choice.

A senior platform team also defines module compatibility policy. Shared modules can be written in a lowest-common-denominator style if they must support both engines. Product-specific stacks can adopt OpenTofu features more freely if the organization has committed to OpenTofu ownership. The important part is to make compatibility an explicit contract instead of an accidental property.

| Organizational Situation | Recommended Direction | Reasoning |
|---|---|---|
| Object-storage state, generic CI, open-source requirement | Pilot OpenTofu first | The workflow has fewer hosted-platform dependencies and OpenTofu aligns with governance goals |
| Heavy Terraform Cloud usage with Sentinel and workspaces | Design replacement before migration | Execution, policy, and variables are part of the platform, not just the CLI |
| Regulated environment with strict state confidentiality | Evaluate OpenTofu encryption carefully | Native encryption may reduce risk, but key management and audit design are still required |
| Multi-region modules with duplicated providers | Consider OpenTofu provider iteration | It can reduce duplicated HCL when lifecycle rules are documented |
| Shared public module intended for both engines | Avoid engine-specific features by default | Portability may matter more than feature adoption |
| Internal platform committed to OpenTofu | Use OpenTofu-specific features selectively | Document one-way choices and update runbooks accordingly |

The decision is successful when a new engineer can answer four questions without guessing: which binary owns this state, where is the state stored, how is it protected, and what platform features would break if we changed engines again? If those answers are missing, the migration is not done even if `tofu apply` succeeded once.

---

## Did You Know?

- **Open governance changes risk ownership.** OpenTofu's Linux Foundation governance gives organizations a community-driven path for the IaC engine, but teams still need their own support, upgrade, and incident-response model.
- **The top-level block still says `terraform`.** OpenTofu keeps the existing language shape for compatibility, so `terraform { required_providers { ... } }` remains correct OpenTofu configuration.
- **Encrypted state still requires secret discipline.** Native encryption protects state and plan payloads, but authorized readers and CI jobs can still expose sensitive values if logs, outputs, and credentials are poorly managed.
- **Negative targeting is an emergency tool.** The `-exclude` family of flags can help during recovery or phased rollout, but persistent targeting usually means the stack boundaries need redesign.

---

## Common Mistakes

| Mistake | Why It Hurts | Better Practice |
|---|---|---|
| Treating OpenTofu as only a command rename | It misses backend, provider, state, CI, policy, and support dependencies that decide whether migration is safe | Inventory the full workflow before changing production automation |
| Letting Terraform and OpenTofu both write the same state | Engine-specific features, encrypted state, or version differences can make rollback confusing or impossible | Declare one engine owner per state file and enforce it in CI |
| Adding state encryption without a migration fallback | OpenTofu may refuse to read the existing unencrypted state, blocking the first encrypted apply | Use an explicit unencrypted fallback for the transition, then remove it after state is rewritten |
| Using `-exclude` as a routine deployment strategy | Regular partial applies can hide drift and make the real state harder to reason about | Split large stacks into smaller ownership boundaries and reserve targeting for exceptional cases |
| Adopting provider iteration without decommission planning | Removing provider instances too early can prevent clean destruction of resources in that region | Keep provider collections as a superset during decommissioning workflows |
| Assuming local success proves CI success | CI may use different provider mirrors, credentials, cache paths, environment variables, and network access | Run a representative CI pilot with explicit `tofu` commands and pinned versions |
| Forgetting hosted-platform features during migration | Remote variables, policy checks, private registries, and approvals may disappear if only the CLI is replaced | Map each hosted-platform capability to an OpenTofu-compatible replacement before production rollout |
| Using advanced features in shared modules without policy | Modules may stop working for teams that still need Terraform compatibility | Mark modules as OpenTofu-only when they use OpenTofu-specific language or CLI behavior |

---

## Quiz

<details>
<summary>1. Your team runs `tofu plan` locally against a migrated repository and gets a no-op plan, but CI fails during `init` before any resources are planned. What should you inspect first, and why?</summary>

Inspect provider installation configuration, the lock file, CI credentials, provider cache settings, and network access before editing resource HCL. A failure during `init` usually means OpenTofu cannot install providers or configure the backend in that environment. The local no-op plan proves the configuration can work on one machine, but it does not prove CI has the same registry, mirror, credential, or backend access.
</details>

<details>
<summary>2. A production repository uses Terraform Cloud workspaces, workspace variables, policy checks, and remote execution. A manager asks you to "just switch the binary to OpenTofu" this week. How would you evaluate that request?</summary>

You should reject the idea as an unscoped binary swap and turn it into a platform migration plan. The hosted platform is providing state, execution, variables, policy, approval flow, and audit behavior, so replacing only the CLI would remove or bypass important controls. The correct next step is to map each hosted feature to a replacement, pilot a lower-risk stack, and require a no-op plan plus policy-equivalent checks before production migration.
</details>

<details>
<summary>3. Your team adds native state encryption to an existing unencrypted OpenTofu state file, then planning fails because the state cannot be read. What likely went wrong, and what sequence should fix it?</summary>

The team likely configured only the new encrypted method and did not provide an `unencrypted` fallback for the first migration apply. Add a temporary unencrypted fallback, provide the key provider inputs, run `tofu plan` and `tofu apply` so OpenTofu can read the old state and write encrypted state, then remove the fallback and enforce encryption after a successful fresh plan. Back up the state before the migration.
</details>

<details>
<summary>4. A multi-region module uses provider iteration and a product team removes a retired region from both the provider collection and the resource collection in the same pull request. The destroy plan cannot proceed cleanly. What design change would you recommend?</summary>

Separate provider lifecycle from resource lifecycle by keeping a provider collection that can include regions being decommissioned and a resource collection that represents regions where resources should still exist. Remove the region from the resource collection first so OpenTofu can destroy resources using the still-present provider instance. Remove the provider instance only after the state no longer contains resources that depend on it.
</details>

<details>
<summary>5. During an incident, a database parameter resource is producing a provider error, but unrelated resources must still be updated. An engineer proposes `tofu apply -exclude=module.database`. What should you check before approving?</summary>

Review the plan produced with `-exclude`, verify which dependent resources are also excluded, confirm the operation is truly exceptional, and document the follow-up plan to reconcile the database module. You should also check whether excluding the entire module is too broad and whether a smaller stack boundary would have avoided this problem. `-exclude` can help during recovery, but it must not become normal deployment policy.
</details>

<details>
<summary>6. A shared module used by several teams adds a provider-defined function to parse provider-specific identifiers. One team still runs Terraform and reports that the module no longer works. How should the platform team respond?</summary>

The platform team should treat this as a compatibility contract failure. Provider-defined functions are OpenTofu-specific behavior from the consuming team's perspective, so the module should either avoid that feature, provide a Terraform-compatible implementation, or be marked as OpenTofu-only with a versioned release. Shared module policy should state when OpenTofu-specific features are allowed and how consumers are notified.
</details>

<details>
<summary>7. A security reviewer says native OpenTofu encryption means state access no longer needs strict IAM controls. How would you correct that conclusion?</summary>

Native encryption protects the serialized state and plan payloads, but it does not remove the need for backend access controls, least-privilege CI identities, KMS policy, secret minimization, and log hygiene. Authorized users or jobs that can decrypt state can still read sensitive values. Encryption is one layer in the state-protection design, not a replacement for authorization and operational discipline.
</details>

<details>
<summary>8. A migration pilot succeeds on a sandbox stack that uses only local resources. The team wants to migrate the production network stack next. What evidence should you require before allowing that jump?</summary>

Require evidence from a representative remote-backend stack first, including state backup, locking behavior, provider installation in CI, a reproducible no-op plan, encryption or access-control review, rollback procedure, and confirmation that downstream remote-state consumers still work. A local sandbox proves basic engine behavior, but it does not validate the production network stack's shared-state and dependency risks.
</details>

---

## Hands-On Exercise

**Objective**: Migrate a Terraform-style local project to OpenTofu, introduce state encryption safely, and practice a controlled `-exclude` operation.

This exercise uses local files and generated names so you can focus on OpenTofu behavior without cloud credentials. The workflow mirrors production habits: explicit binary use, saved plans, state inspection, encryption migration, and review of a targeted plan before applying.

### Part 1: Create a Small Terraform-Style Project

- [ ] Create a new working directory for the lab and enter it.
- [ ] Write a minimal HCL configuration using the `random` and `local` providers.
- [ ] Run `tofu fmt`, `tofu init`, `tofu validate`, and a saved plan.
- [ ] Apply the saved plan and verify that OpenTofu created the expected file.

```bash
mkdir -p opentofu-module-7-2-lab
cd opentofu-module-7-2-lab
```

```bash
cat > main.tf <<'EOF'
terraform {
  required_version = ">= 1.9.0"

  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }

    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

resource "random_pet" "service" {
  length = 2
}

resource "local_file" "primary" {
  filename = "${path.module}/primary.conf"
  content  = "service=${random_pet.service.id}\nrole=primary\nmanaged_by=opentofu\n"
}

output "service_name" {
  value = random_pet.service.id
}
EOF
```

```bash
tofu fmt
tofu init
tofu validate
tofu plan -out=tfplan
tofu apply tfplan
```

```bash
cat primary.conf
tofu state list
tofu output service_name
```

Before moving on, inspect `terraform.tfstate` enough to understand why state needs protection. You should see resource identity and output information. In real infrastructure, this file often contains more sensitive details than learners expect.

```bash
sed -n '1,80p' terraform.tfstate
```

### Part 2: Add State and Plan Encryption With a Migration Fallback

- [ ] Add an encryption configuration that can read the existing unencrypted state.
- [ ] Provide the passphrase through an environment variable rather than committing it.
- [ ] Apply once so OpenTofu rewrites the state using the encrypted method.
- [ ] Confirm that a fresh plan can still read the state.

```bash
cat > encryption.tf <<'EOF'
variable "state_passphrase" {
  description = "Passphrase for the local OpenTofu encryption exercise."
  type        = string
  sensitive   = true
}

terraform {
  encryption {
    method "unencrypted" "migration" {}

    key_provider "pbkdf2" "main" {
      passphrase = var.state_passphrase
    }

    method "aes_gcm" "state_method" {
      keys = key_provider.pbkdf2.main
    }

    state {
      method = method.aes_gcm.state_method

      fallback {
        method = method.unencrypted.migration
      }
    }

    plan {
      method = method.aes_gcm.state_method

      fallback {
        method = method.unencrypted.migration
      }
    }
  }
}
EOF
```

```bash
export TF_VAR_state_passphrase="learning-passphrase-change-this-before-real-use"
tofu fmt
tofu init
tofu plan -out=tfplan
tofu apply tfplan
tofu plan
```

```bash
sed -n '1,40p' terraform.tfstate
```

The state should no longer look like ordinary readable JSON. If your plan fails, debug the encryption input first: confirm that `TF_VAR_state_passphrase` is set in the same shell, that the encryption file is present, and that you used the migration fallback before trying to enforce encryption.

### Part 3: Remove the Migration Fallback After Encryption Works

- [ ] Replace the temporary encryption configuration with an enforced configuration.
- [ ] Run a fresh plan to prove OpenTofu can read the encrypted state without fallback.
- [ ] Explain why keeping the fallback permanently would weaken the migration signal.

```bash
cat > encryption.tf <<'EOF'
variable "state_passphrase" {
  description = "Passphrase for the local OpenTofu encryption exercise."
  type        = string
  sensitive   = true
}

terraform {
  encryption {
    key_provider "pbkdf2" "main" {
      passphrase = var.state_passphrase
    }

    method "aes_gcm" "state_method" {
      keys = key_provider.pbkdf2.main
    }

    state {
      method   = method.aes_gcm.state_method
      enforced = true
    }

    plan {
      method   = method.aes_gcm.state_method
      enforced = true
    }
  }
}
EOF
```

```bash
tofu fmt
tofu init
tofu plan
```

### Part 4: Practice a Controlled `-exclude` Operation

- [ ] Add two new managed files, one stable and one canary.
- [ ] Produce a plan that excludes the canary file.
- [ ] Apply the saved plan and verify that only the stable file was created.
- [ ] Run a normal plan afterward and explain the remaining change.

```bash
cat >> main.tf <<'EOF'

resource "local_file" "stable" {
  filename = "${path.module}/stable.conf"
  content  = "role=stable\nmanaged_by=opentofu\n"
}

resource "local_file" "canary" {
  filename = "${path.module}/canary.conf"
  content  = "role=canary\nmanaged_by=opentofu\n"
}
EOF
```

```bash
tofu fmt
tofu plan -exclude=local_file.canary -out=tfplan
tofu apply tfplan
ls -1 *.conf
```

```bash
tofu plan
```

The follow-up plan should still include the canary file because your configuration declares it and the previous apply intentionally excluded it. This is the lesson: `-exclude` is not a permanent configuration decision. It creates an exceptional operation that you must reconcile later.

### Part 5: Document the Migration Decision

- [ ] Write a short note named `MIGRATION-NOTE.md` that states which engine owns this state.
- [ ] Include where the state is stored in this lab and how encryption is provided.
- [ ] Include one rollback warning about OpenTofu-specific encryption.
- [ ] Include one sentence explaining when `-exclude` may be used.

```bash
cat > MIGRATION-NOTE.md <<'EOF'
# OpenTofu Migration Note

This lab state is owned by OpenTofu, and future operations should use the `tofu` binary explicitly.

The state is stored locally in `terraform.tfstate` for learning purposes, and native OpenTofu encryption is configured through `encryption.tf` with the passphrase supplied by `TF_VAR_state_passphrase`.

Rollback to another engine is not safe after enabling OpenTofu-specific state encryption unless the state is intentionally migrated back to a compatible unencrypted or supported format.

The `-exclude` flag may be used for exceptional recovery or phased rollout, but normal changes should use full plans or smaller stack boundaries.
EOF
```

### Success Criteria

- [ ] You can explain why OpenTofu migration requires backend and CI review, not only a command replacement.
- [ ] `tofu init`, `tofu validate`, `tofu plan`, and `tofu apply` all ran successfully in the lab.
- [ ] The project created `primary.conf` and tracked it in OpenTofu state.
- [ ] You migrated from unencrypted local state to native encrypted state using a temporary fallback.
- [ ] A fresh plan succeeded after removing the migration fallback and enforcing encryption.
- [ ] You used `-exclude` to hold back `local_file.canary` and verified the remaining planned change afterward.
- [ ] Your migration note identifies the engine owner, state location, encryption mechanism, rollback warning, and `-exclude` policy.

### Cleanup

Run cleanup only after you have inspected the state and answered the success criteria. The destroy command uses OpenTofu so the same engine that owns the encrypted state performs the cleanup.

```bash
tofu destroy -auto-approve
cd ..
rm -rf opentofu-module-7-2-lab
```

---

## Next Module

Continue to [Module 7.3: Pulumi](../module-7.3-pulumi/) to compare OpenTofu's declarative HCL workflow with infrastructure as code written in general-purpose programming languages.

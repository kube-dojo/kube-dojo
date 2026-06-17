---
revision_pending: false
title: "Module 7.6: Azure Bicep"
slug: platform/toolkits/infrastructure-networking/iac-tools/module-7.6-bicep
sidebar:
  order: 7
---
## Complexity: [MEDIUM]
## Time to Complete: 75 minutes

---

## Prerequisites

Before starting this module, you should have completed:
- [Module 6.1: IaC Fundamentals](/platform/disciplines/delivery-automation/iac/module-6.1-iac-fundamentals/)
- Azure subscription with Contributor access
- Azure CLI installed (`az --version`)
- Basic understanding of Azure Resource Manager (ARM)

---

## Learning Outcomes

After completing this module, you will be able to:

- **Deploy Azure infrastructure using Bicep templates with modules and parameter files**
- **Implement Bicep deployment stacks for multi-resource-group and subscription-level deployments**
- **Configure Bicep with Azure DevOps and GitHub Actions for automated infrastructure pipelines**
- **Compare Bicep's Azure-native approach against Terraform for Azure-centric infrastructure teams**
- **Understand where Bicep sits on the IaC evolution spectrum and when its tradeoffs make sense**

> **Landscape snapshot — as of 2026-06. This changes fast; verify against upstream docs before relying on specifics.**
>
> Bicep is a **Microsoft first-party project** under the Azure organization on GitHub (`Azure/bicep`), licensed under the **MIT License**. The latest release as of June 2026 is **v0.44.1**, with active development and frequent releases (typically 1–3 per month). It is **generally available (GA)** and fully supported for production use. Bicep integrates into the core Azure toolchain: it ships inside the Azure CLI, has a first-party VS Code extension, and is documented on Microsoft Learn. The module registry ecosystem includes the **Azure Verified Modules (AVM)** initiative — Microsoft-maintained, production-grade Bicep modules published through the Bicep public registry (`br/public:avm/…`). Bicep is Azure-only by design; there is no roadmap for multi-cloud support. The `bicepparam` file format (`.bicepparam`) is GA, and the Bicep linter, `what-if` preview, and deployment stacks are all production-ready features.

---

## Why This Module Matters

Infrastructure as Code sits on a spectrum. On one end you have imperative scripts — Bash loops calling `az vm create`, PowerShell sprinkling `New-AzResourceGroup` — that tell Azure *how* to build, step by step, with all the fragility of procedural programming baked into your infrastructure. On the other end, you have infrastructure-from-application-code — tools like Pulumi and Wing that let you write Go or TypeScript and have the tool infer what cloud resources your program needs, synthesizing infrastructure from the same language your application uses. Between these poles lies the declarative template layer: Terraform HCL, AWS CloudFormation, and Azure ARM JSON templates. These tools let you describe *what* you want, not *how* to build it, and let the engine reconcile the desired state with reality.

Bicep lives in the declarative layer — but it solves a very specific pain point that anyone who has wrestled with ARM templates knows intimately. ARM JSON templates are the canonical deployment format for Azure Resource Manager, the control-plane engine that provisions every resource in Azure. They are verbose JSON documents with no comments, string-based expression syntax (`[parameters('foo')]`) that no linter can type-check, and no module system beyond linked templates that reference external JSON files by URI. A production ARM template routinely runs 2,000 to 5,000 lines of dense, unreadable JSON. Debugging a missing bracket at line 1,847 on December 23rd is a real experience people have had — and it is the reason Bicep exists.

Bicep is a domain-specific language (DSL) that compiles — or more precisely, transpiles — to ARM JSON templates. It is not a new deployment engine. When you run `az deployment group create --template-file main.bicep`, the Bicep CLI first translates your `.bicep` file into the same JSON that ARM has always consumed, then hands it to Azure's deployment machinery. This architecture gives Bicep a unique property among IaC tools: **it gets day-zero support for every new Azure feature** because it speaks ARM's native protocol. There is no provider plugin to update, no intermediary that needs to add support for a new API version. When Azure ships a new resource type or API version, you can use it in Bicep the same day.

The tradeoff is scope. Bicep is Azure-only — deliberately and permanently. It is not trying to be a multi-cloud tool. If your infrastructure spans AWS, GCP, and Azure, Bicep handles one slice of that puzzle. But for teams whose infrastructure lives entirely or primarily in Azure, Bicep eliminates an entire class of problems: no state file to corrupt or lose, no provider lag behind Azure API releases, no impedance mismatch between the tool's abstraction and Azure's own resource model. You write Azure resources the way Azure understands them, with full IntelliSense, type checking, and the ability to reference any property on any resource type without consulting an intermediary schema.

This module grounds you in the Bicep mental model — the transpilation pipeline, the syntax, the module system, the deployment lifecycle — so you can decide whether its tradeoffs match your team's reality. You will walk through real code, understand how Bicep maps to ARM concepts you may already know, and see how it fits into CI/CD pipelines. By the end, you will be able to read, write, and deploy Bicep templates with the same fluency you bring to any IaC tool in your toolkit.

---

## Did You Know?

1. **Bicep grew out of the Azure team's frustration with ARM template JSON.** Anthony Martin — now Engineering Manager for Bicep & ARM Deployments at Microsoft and a top contributor on `Azure/bicep` — is among the engineers most associated with its creation. Microsoft announced Project Bicep publicly in late 2020, and it shows how a well-targeted developer-experience improvement can reshape an ecosystem's tooling defaults.

2. **The name "Bicep"** is a playful reference to ARM (Azure Resource Manager) — biceps are part of your arm. The `az bicep` CLI command continues the theme, and the name has become a recognizable brand in the Azure infrastructure community.

3. **Azure Verified Modules (AVM)** is Microsoft's official repository of production-ready Bicep modules maintained by Microsoft product groups. These follow strict quality gates, semantic versioning, and are published to the Bicep public registry — check AVM before writing your own modules for common Azure patterns.

4. **Bicep has no separate state file.** ARM manages deployment state through its own deployment history in Azure. You never need to store, back up, lock, or recover a `terraform.tfstate` — Azure itself is the source of truth for what was deployed and when. The Bicep linter also runs by default on every build, catching unused parameters, missing secure decorators, and outdated API versions before they reach Azure.

---

## Bicep vs. ARM Templates: The Evolution

### Why Bicep Exists — The Declarative DSL Layer on the IaC Spectrum

To understand Bicep's design decisions, you need to understand what ARM templates are and why they were painful enough to justify building an entirely new language that compiles to the same target.

ARM (Azure Resource Manager) is the deployment and management layer for Azure. Every resource you create — storage accounts, virtual networks, VMs, Key Vaults — flows through ARM's REST API. ARM templates are the JSON format for describing desired state to that API: you specify a list of resources, their properties, and their dependencies, and ARM resolves the dependency graph and provisions them in the correct order. This model is powerful. It is declarative, idempotent (ARM uses incremental mode by default — it merges changes rather than replacing everything), and deeply integrated with Azure's resource provider model.

The problem is strictly ergonomic. The ARM template JSON format emerged in 2014, when JSON was the universal API language and "infrastructure as code" mostly meant "we committed our CloudFormation templates to git." The expression language is embedded in strings: `"[parameters('storageAccountName')]"` is how you reference a parameter. There are no comments, no type checking beyond what ARM validates at deployment time, and no module system beyond linked templates — separate JSON files referenced by URI that ARM fetches at deployment time. As teams grew their Azure footprints, template files grew to thousands of lines of uncommented, untyped JSON. Copy-paste became the dominant code reuse strategy because linked templates required managing a separate deployment artifact.

Bicep addresses every one of these ergonomic failures without replacing the deployment engine:

1. **Readability**: The syntax is designed for humans, not machines. No brackets, no quote escaping, no string-based expressions — you write `storageAccountName` not `"[parameters('storageAccountName')]"`.

2. **Type safety and IntelliSense**: The Bicep compiler has a full type system that understands Azure resource schemas. VS Code (with the Bicep extension) can autocomplete resource property names, flag type mismatches, and show you the valid API versions for any resource type — all before deployment.

3. **Real modules**: Bicep's `module` keyword lets you compose infrastructure from reusable, parameterized components. Modules reference local files or registry-published artifacts, and you pass typed parameters between them with the same syntax you use for resource properties.

4. **Language features that ARM JSON never had**: loops (`for`), conditionals (`if`), ternary expressions, string interpolation (`${variable}-suffix`), decorators for validation rules, and the `existing` keyword for referencing resources created outside the current template.

5. **Same deployment engine**: This is the key insight. Because Bicep transpiles to ARM JSON, every Bicep deployment is an ARM deployment. You get all the ergonomic improvements with none of the architectural risk of adopting a new deployment system.

The following illustration captures this evolution from raw ARM JSON to the Bicep DSL:

```
┌─────────────────────────────────────────────────────────────────┐
│                    ARM TEMPLATE EVOLUTION                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  2014: ARM Templates (JSON)                                      │
│  ════════════════════════                                        │
│                                                                  │
│  {                                                               │
│    "resources": [{                                               │
│      "type": "Microsoft.Storage/storageAccounts",               │
│      "apiVersion": "2021-09-01",                                │
│      "name": "[parameters('storageAccountName')]",              │
│      "location": "[resourceGroup().location]",                  │
│      "sku": {                                                   │
│        "name": "[parameters('storageSKU')]"                     │
│      },                                                          │
│      "kind": "StorageV2"                                        │
│    }]                                                            │
│  }                                                               │
│                                                                  │
│                    ↓ 7 years of pain ↓                          │
│                                                                  │
│  2020: Bicep (Domain-Specific Language)                         │
│  ═══════════════════════════════════════                        │
│                                                                  │
│  resource storage 'Microsoft.Storage/storageAccounts@2021-09-01'│
│    = {                                                          │
│    name: storageAccountName                                     │
│    location: resourceGroup().location                           │
│    sku: { name: storageSKU }                                    │
│    kind: 'StorageV2'                                            │
│  }                                                               │
│                                                                  │
│  ✅ Same deployment engine (ARM)                                │
│  ✅ Transpiles to ARM JSON                                       │
│  ✅ Day-0 Azure feature support                                  │
│  ✅ Type-safe, IntelliSense                                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### The Transpilation Pipeline

When you run `az bicep build --file main.bicep`, Bicep parses your file, resolves all module references, validates types and decorator constraints, performs scope resolution, and emits a single ARM JSON template. You can inspect this output with `az bicep build --stdout` to see exactly what ARM receives. This transparency is deliberate — Microsoft wants you to trust that Bicep is not doing anything ARM doesn't understand, because you can audit the output yourself. The deployment command (`az deployment group create --template-file main.bicep`) performs the transpilation inline, so you never need to check in the generated JSON; treat the `.bicep` files as the source of truth, just as you would `.tf` files with Terraform.

### Hypothetical scenario: The ARM Template That Ate Christmas

This story illustrates the real-world cost of the ergonomic failures Bicep addresses. While anonymized, the pattern — a team losing hours to ARM JSON's opacity during an urgent change — is representative of experiences Azure practitioners have described across the community.

**Characters:** Diego (Azure Cloud Architect, 7 years experience), a team of 4 engineers managing 200+ Azure resources across 3 environments, and an inherited 2,847-line ARM template that nobody fully understood.

**Timeline:**

```
10:00 AM: Simple task - update VM SKU parameter
          Opens main.json (ARM template)
          2,847 lines of JSON

10:30 AM: Finds the parameter definition
          Nested inside... something
          JSON brackets everywhere

11:00 AM: Makes the change
          ARM template validation fails
          "Expected ',' at line 1,847"

11:30 AM: Hunting the missing comma
          JSON has no comments
          Can't tell where it broke

12:00 PM: Lunch skipped
          Found it - a bracket, not a comma

12:30 PM: Deploys to dev
          Different error: "Resource not found"
          Template references resources via copy index
          Copy index math is wrong somewhere

2:00 PM:  Realizes the copy loop was modified last month
          By someone who's now on vacation
          No documentation

3:00 PM:  Diego: "What if we just... rewrote this in Bicep?"
          Team: "We don't have time"
          Diego: "The ARM template IS the time sink"

3:30 PM:  Starts converting to Bicep
          ARM JSON: 2,847 lines
          Bicep: 412 lines (same resources!)

5:00 PM:  Bicep template complete
          Clear variable names
          Actual comments
          Type checking catches 3 errors

5:30 PM:  Deploys to dev - SUCCESS
          Deploys to staging - SUCCESS
          Deploys to prod - SUCCESS

6:00 PM:  Holiday freeze begins
          Team goes home on time

January:  All new infrastructure is Bicep
          ARM templates converted over Q1
          Deployment incidents drop 73%
```

**What Bicep Fixed:** 1) Readability — 60% less code with actual syntax highlighting; 2) Type safety — catches errors before deployment; 3) IntelliSense — VS Code knows Azure resource properties; 4) No string interpolation hell — clean variable references; 5) Modules — reusable, parameterized components.

**Lessons Learned:** 1) JSON is not a programming language; 2) Readability equals maintainability equals reliability; 3) "We don't have time to rewrite" is often false when the current tool is the bottleneck; 4) Native tools get Azure features first, eliminating the provider-update waiting period.

### Cross-Tool Rosetta: Bicep on the IaC Spectrum

Every Infrastructure as Code tool makes different bets on abstraction, state management, and scope. Understanding these tradeoffs lets you choose the right tool for your context rather than defaulting to whatever your team already knows. The table below compares Bicep against Terraform/OpenTofu (the declarative-template baseline) and Pulumi (the infrastructure-from-code approach), using durable capability axes that outlive any version number:

| Capability | Bicep | Terraform / OpenTofu | Pulumi |
|---|---|---|---|
| **Abstraction model** | DSL transpiling to ARM JSON | HCL translated via provider plugins to cloud APIs | General-purpose languages (TypeScript, Python, Go, C#) with cloud SDK bindings |
| **What it compiles to** | ARM JSON template — consumed by Azure Resource Manager | Cloud API calls — Terraform Core resolves the resource graph and calls provider APIs | Cloud API calls — Pulumi engine tracks resource registrations and calls cloud APIs |
| **State management** | ARM deployment history in Azure (no separate state file) | State file (local or remote backend) — must be stored, locked, and backed up | State managed by Pulumi Cloud or self-hosted backend (`pulumi state`) |
| **Target clouds** | Azure only (by design) | Multi-cloud — 3,000+ providers across AWS, Azure, GCP, and hundreds of SaaS services | Multi-cloud — native providers for AWS, Azure, GCP, plus Kubernetes and SaaS |
| **Azure feature support latency** | Day-0 — uses ARM API versions directly, no intermediary | Days to weeks — the `azurerm` provider must be updated to support new API versions | Days to weeks — the `azure-native` provider must be updated (though it tracks ARM more closely than Terraform) |
| **Language / syntax** | Bicep DSL — concise, purpose-built, with IntelliSense | HCL — declarative, block-structured, with expression support | General-purpose languages — full power of TypeScript, Python, Go, or C# |
| **Module / package ecosystem** | Bicep Registry (ACR-based), Azure Verified Modules (AVM), growing community | Terraform Registry — 16,000+ modules, mature ecosystem | Pulumi Registry — component packages and native providers |
| **Drift detection** | `what-if` preview compares desired state against current Azure state | `terraform plan` compares state file against desired configuration | `pulumi preview` compares Pulumi state against desired program output |
| **Primary use case** | Azure-native teams that want first-party tooling, day-zero feature access, and no state-file management | Multi-cloud teams, teams with established Terraform workflows, and organizations that value provider ecosystem breadth | Teams that want infrastructure expressed in application languages, with full programming constructs (classes, loops, unit tests) |
| **License / governance** | MIT License, Microsoft-maintained, part of Azure toolchain | Terraform: BSL (since 2023); OpenTofu: MPL-2.0, Linux Foundation | Apache 2.0, Pulumi Corporation |

**How to read this table:** The rows are durable capabilities — the primitives any IaC tool must address. The cells describe how each tool implements that capability today. A new version of Bicep won't change the abstraction model or the target-cloud row; a new Terraform provider won't change the state-management model. The durable spine stays stable; the volatile facts (specific API versions, exact module counts, license changes) belong in the dated snapshot section within Learning Outcomes above.

---

## Bicep Fundamentals

### Installation and Setup

Bicep ships inside the Azure CLI — you do not install it separately. When you run `az bicep version`, the CLI downloads and caches the Bicep compiler binary automatically. This bundling decision means that every Azure CLI installation is also a Bicep installation, and updates follow the same rhythm as your CLI updates. The VS Code extension adds IntelliSense, syntax highlighting, and inline validation, but it delegates compilation to the same `az bicep` binary. The installation commands below cover the three essential pieces: the Azure CLI itself, the Bicep compiler upgrade, and the VS Code extension:

```bash
# Install Azure CLI (includes Bicep)
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Verify Bicep installation
az bicep version

# Upgrade Bicep to latest
az bicep upgrade

# Install VS Code extension
code --install-extension ms-azuretools.vscode-bicep
```

### Understanding the Bicep Type System

Before you write your first resource declaration, it is worth understanding what the Bicep compiler does with your code. Bicep is **strongly typed** — every parameter, variable, and output has a concrete type that the compiler enforces before deployment. The type system is not academic; it directly prevents the most common ARM deployment failures: mismatched property types, missing required fields, and invalid enum values. When VS Code underlines a property in red, it is because the Bicep type checker has consulted the Azure resource provider's schema and found a mismatch — a fundamentally different experience from ARM JSON, where every value is a string until ARM parses it at deployment time.

The basic Bicep types map directly to JSON Schema types: `string`, `int`, `bool`, `object`, and `array`. Beyond these primitives, Bicep adds three features that change how you write infrastructure code. First, **decorators** like `@minLength(3)`, `@maxLength(24)`, and `@allowed([...])` add validation constraints that the compiler checks at build time, catching invalid values before they reach Azure. Second, the `@secure()` decorator marks a parameter as sensitive — its value is masked in deployment logs and never appears in ARM deployment history. Third, **union types** let you express "this parameter accepts either a string or an object" without resorting to `any`, which would prevent the type checker from catching property access errors. These type system features together mean that a significant fraction of deployment failures — the kind that used to surface as cryptic ARM API errors 20 minutes into a deployment — are now caught in your editor before you even commit.

### Basic Syntax Walkthrough

The following complete Bicep template demonstrates every foundational concept: parameters with validation decorators, computed variables, resource declarations with parent-child relationships, and outputs. Read through it line by line, then we will walk through each section and explain the design decisions behind each construct:

```bicep
// main.bicep

// ============================================
// PARAMETERS - Input values
// ============================================
@description('The Azure region for resources')
param location string = resourceGroup().location

@description('Environment name')
@allowed([
  'dev'
  'staging'
  'prod'
])
param environment string = 'dev'

@description('Storage account name')
@minLength(3)
@maxLength(24)
param storageAccountName string

@secure()
@description('Administrator password')
param adminPassword string

// ============================================
// VARIABLES - Computed values
// ============================================
var tags = {
  Environment: environment
  ManagedBy: 'Bicep'
  CostCenter: environment == 'prod' ? 'PROD-001' : 'DEV-001'
}

var storageSkuName = environment == 'prod' ? 'Standard_GRS' : 'Standard_LRS'

// ============================================
// RESOURCES - Azure resources to deploy
// ============================================
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  tags: tags
  sku: {
    name: storageSkuName
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    networkAcls: {
      defaultAction: 'Deny'
      bypass: 'AzureServices'
    }
  }
}

resource blobServices 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' = {
  parent: storageAccount
  name: 'default'
  properties: {
    deleteRetentionPolicy: {
      enabled: true
      days: environment == 'prod' ? 30 : 7
    }
  }
}

resource container 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobServices
  name: 'data'
  properties: {
    publicAccess: 'None'
  }
}

// ============================================
// OUTPUTS - Values to expose
// ============================================
output storageAccountId string = storageAccount.id
output blobEndpoint string = storageAccount.properties.primaryEndpoints.blob
output storageAccountName string = storageAccount.name
```

Let us walk through each block and understand the design decisions.

**Parameters** are the inputs your template accepts. Every parameter has a name, a type, and optionally a default value. The `location` parameter defaults to the resource group's location — a common pattern that lets you deploy the same template to any region without changing the parameter file. The `environment` parameter uses the `@allowed` decorator to restrict values to a known set, preventing a typo like "prdo" from creating confusingly-named resources. The `@minLength` and `@maxLength` decorators on `storageAccountName` enforce Azure's naming constraints at compile time rather than waiting for the ARM API to reject the deployment, and the `@secure()` decorator on `adminPassword` tells Bicep to mask this value in logs and deployment history — critical for secrets, even though you should prefer Key Vault references over plaintext passwords in production.

**Variables** are computed values, not inputs. They let you derive configuration from parameters without duplication. The `tags` variable uses a ternary expression (`environment == 'prod' ? 'PROD-001' : 'DEV-001'`) to assign different cost-center tags per environment, and `storageSkuName` applies the same pattern to SKU selection — GRS for production, LRS for everything else. These computed values make the template self-documenting: you can read the variable definition and understand the business rule without tracing it through parameter combinations.

**Resources** are the core of any Bicep template. Each resource declaration names a symbolic reference (like `storageAccount`), specifies a resource type with an API version (`'Microsoft.Storage/storageAccounts@2023-01-01'`), and provides property values. The symbolic name is only used within the Bicep file — it is not the Azure resource name — and you reference it to access the resource's properties (`storageAccount.id`) or to establish parent-child relationships. The child resources `blobServices` and `container` use the `parent:` property to indicate hierarchy rather than embedding the full type path in each declaration, which is both more readable and safer because Bicep automatically infers the dependency order: storage account first, then blob services, then container. Notice the security-by-default posture in the properties: HTTPS-only traffic, minimum TLS 1.2, public blob access disabled, and network ACLs defaulting to deny with Azure service bypass. Infrastructure as Code is a security control — templates that default to open and require manual hardening are anti-patterns. Every property you do not explicitly set inherits Azure's default, which may or may not match your security requirements.

**Outputs** expose values that other templates or deployment scripts need. The `storageAccount.id` output lets a downstream module reference this storage account without hardcoding its resource ID, and the `blobEndpoint` output provides the actual URI that an application would use. In the ARM resource model, resource properties are accessed through the symbolic name using dot notation — `storageAccount.properties.primaryEndpoints.blob` navigates the ARM response schema exactly as Azure returns it, giving you compile-time safety on property paths that ARM JSON's string expressions could never provide.

### Deploying Bicep Templates

Once your template is written, deploying it involves authenticating to Azure, targeting the right scope, and providing parameter values. The deployment commands below cover the standard workflow: resource-group-scoped deployment, parameter file usage, preview with `what-if`, and output extraction:

```bash
# Login to Azure
az login

# Set subscription
az account set --subscription "My Subscription"

# Create resource group
az group create --name myapp-rg --location eastus

# Deploy Bicep file
az deployment group create \
  --resource-group myapp-rg \
  --template-file main.bicep \
  --parameters storageAccountName=myappstg123 \
               environment=dev

# Deploy with parameter file
az deployment group create \
  --resource-group myapp-rg \
  --template-file main.bicep \
  --parameters @params/dev.bicepparam

# What-if deployment (preview changes)
az deployment group what-if \
  --resource-group myapp-rg \
  --template-file main.bicep \
  --parameters @params/dev.bicepparam

# Export outputs
az deployment group show \
  --resource-group myapp-rg \
  --name main \
  --query properties.outputs
```

The `what-if` command deserves special attention because it is Bicep's equivalent of `terraform plan` — but with an important architectural difference. Terraform's plan works by comparing the desired configuration against the state file, which can drift from reality if someone made a change in the portal. Bicep's `what-if` queries ARM directly for the current state of every resource in the template, so the results show exactly what Azure would create, modify, or delete if the deployment ran. There is no stale state file to worry about; the Azure control plane is the authoritative source of truth. Always run `what-if` before a production deployment — the output explicitly lists every resource change, and you should review it for unexpected modifications or deletions before proceeding. Beyond the preview itself, what-if is also a valuable debugging tool: when a deployment fails with an opaque ARM error, running what-if against the same parameters can surface the specific resource and property that would change, narrowing the investigation from thousands of lines to a single resource.

---

## Bicep Modules

### Why Modules Matter in Infrastructure Code

Every infrastructure codebase that grows beyond a single file hits the same wall: the template becomes too large to understand, too coupled to change safely, and too repetitive to maintain. The solution in general-purpose programming is functions, classes, and packages. In Bicep, it is modules — separate `.bicep` files that accept typed parameters and return typed outputs, exactly like a function. The caller does not need to know how the module provisions its resources, only what parameters it requires and what outputs it exposes.

This encapsulation has three concrete benefits. First, **reuse**: you write a VNet module once and invoke it for dev, staging, and production with different CIDR ranges and subnet configurations, eliminating the copy-paste that made ARM templates unmaintainable. Second, **separation of concerns**: the networking team owns `vnet.bicep`, the database team owns `sql.bicep`, and neither needs to read the other's implementation — each module becomes a contract with a well-defined interface. Third, **testability**: you can validate, lint, and deploy a module independently before integrating it into the main template, catching errors in isolation rather than during a full environment deployment.

### Typical Module Structure

A well-organized Bicep project separates concerns into a directory tree that mirrors the Azure resource hierarchy. Modules that represent self-contained Azure services live in their own files, and parameter files for each environment live alongside, letting you version-control environment-specific configuration separately from the infrastructure logic:

```
infrastructure/
├── main.bicep              # Entry point
├── modules/
│   ├── networking/
│   │   ├── vnet.bicep
│   │   └── nsg.bicep
│   ├── compute/
│   │   ├── vm.bicep
│   │   └── vmss.bicep
│   ├── storage/
│   │   └── storage.bicep
│   └── database/
│       └── sql.bicep
└── params/
    ├── dev.bicepparam
    ├── staging.bicepparam
    └── prod.bicepparam
```

### Creating a Module

A module file looks nearly identical to a main template. The difference is conceptual: a module is designed to be consumed by another template, so its parameters represent the knobs the caller can turn and its outputs represent the values the caller needs to wire modules together. The following VNet module demonstrates this contract — it accepts configuration parameters and returns the resource IDs that downstream modules need to place resources in the network:

```bicep
// modules/networking/vnet.bicep

@description('VNet name')
param vnetName string

@description('VNet address space')
param addressPrefix string = '10.0.0.0/16'

@description('Location')
param location string = resourceGroup().location

@description('Subnets configuration')
param subnets array = [
  {
    name: 'web'
    addressPrefix: '10.0.1.0/24'
  }
  {
    name: 'app'
    addressPrefix: '10.0.2.0/24'
  }
  {
    name: 'data'
    addressPrefix: '10.0.3.0/24'
  }
]

@description('Tags')
param tags object = {}

// Virtual Network
resource vnet 'Microsoft.Network/virtualNetworks@2023-05-01' = {
  name: vnetName
  location: location
  tags: tags
  properties: {
    addressSpace: {
      addressPrefixes: [
        addressPrefix
      ]
    }
    subnets: [for subnet in subnets: {
      name: subnet.name
      properties: {
        addressPrefix: subnet.addressPrefix
        privateEndpointNetworkPolicies: 'Disabled'
        privateLinkServiceNetworkPolicies: 'Enabled'
      }
    }]
  }
}

// Outputs
output vnetId string = vnet.id
output vnetName string = vnet.name
output subnetIds array = [for (subnet, i) in subnets: vnet.properties.subnets[i].id]
```

The `param subnets array = [...]` is worth examining closely. Bicep accepts structured arrays as parameter values, which means you can pass a list of subnet configurations — each with a name and address prefix — as a single parameter. The `for` loop inside the resource declaration iterates over this array and generates the corresponding ARM subnet objects, replacing what would be dozens of copy-pasted subnet definitions in an ARM JSON template with a single loop that scales to any number of subnets. The output `subnetIds` similarly uses a loop with index to return the ARM-generated resource IDs that callers can index by position.

### Using Modules in a Main Template

Calling a module is syntactically similar to declaring a resource. You specify a symbolic name, the module source (local file path or registry reference), a deployment name, and the parameter values. The `scope` property controls which resource group or subscription receives the module's resources:

```bicep
// main.bicep
targetScope = 'subscription'

param location string = 'eastus'
param environment string = 'dev'

// Create Resource Group
resource rg 'Microsoft.Resources/resourceGroups@2023-07-01' = {
  name: 'myapp-${environment}-rg'
  location: location
  tags: {
    Environment: environment
  }
}

// Deploy networking module
module networking 'modules/networking/vnet.bicep' = {
  scope: rg
  name: 'networking-deployment'
  params: {
    vnetName: 'myapp-${environment}-vnet'
    location: location
    addressPrefix: '10.0.0.0/16'
    subnets: [
      { name: 'web', addressPrefix: '10.0.1.0/24' }
      { name: 'app', addressPrefix: '10.0.2.0/24' }
      { name: 'data', addressPrefix: '10.0.3.0/24' }
    ]
    tags: {
      Environment: environment
    }
  }
}

// Deploy storage module
module storage 'modules/storage/storage.bicep' = {
  scope: rg
  name: 'storage-deployment'
  params: {
    storageAccountName: 'myapp${environment}stg${uniqueString(rg.id)}'
    location: location
    subnetId: networking.outputs.subnetIds[2] // data subnet
  }
}

// Deploy compute module (depends on networking)
module compute 'modules/compute/vm.bicep' = {
  scope: rg
  name: 'compute-deployment'
  params: {
    vmName: 'myapp-${environment}-vm'
    location: location
    subnetId: networking.outputs.subnetIds[1] // app subnet
    adminUsername: 'azureuser'
    adminPassword: keyVaultSecret.getSecret('vm-admin-password')
  }
  dependsOn: [
    networking
  ]
}

// Reference existing Key Vault for secrets
resource keyVaultSecret 'Microsoft.KeyVault/vaults@2023-02-01' existing = {
  name: 'myapp-kv'
  scope: resourceGroup('myapp-shared-rg')
}

output vnetId string = networking.outputs.vnetId
output storageEndpoint string = storage.outputs.blobEndpoint
```

Notice the dependency model. The `storage` module references `networking.outputs.subnetIds[2]` — the data subnet. Because it accesses a property of the networking module's output, Bicep infers an implicit dependency: `storage` will not deploy until `networking` completes. The `compute` module uses `dependsOn` explicitly because its dependency is not captured by a property reference — it needs the VNet to exist before placing a VM, but the subnet ID alone is sufficient, and the explicit dependency documents that relationship for anyone reading the code. Prefer implicit dependencies through property references when possible; use `dependsOn` only when the dependency relationship is not visible through the parameter values. The `uniqueString(rg.id)` pattern in the storage account name solves a common Azure problem: storage accounts must have DNS-unique names, and `uniqueString()` generates a deterministic hash based on the resource group ID, ensuring the same template deployed to different resource groups produces different names without requiring the caller to provide a unique suffix.

---

## Bicep Registry and Versioning

### The Module Distribution Problem

Once you have written a module that works, you face a distribution problem: how do other teams discover and consume it without copying the file into every repository? The answer in most programming ecosystems is a package registry. Bicep uses Azure Container Registry (ACR) as its module registry — the same ACR you already use for Docker images, Helm charts, and OCI artifacts. This unification is deliberate: your Bicep modules live alongside your container images in the same registry, governed by the same RBAC and network policies that your security team has already configured. When you publish a module with `az bicep publish`, the Bicep CLI packages the module and its metadata as an OCI artifact and pushes it to the specified ACR repository. Consumers reference the module with the `br:` (Bicep Registry) protocol scheme: `br:myregistry.azurecr.io/bicep/modules/networking/vnet:v1.0.0`. Semantic version tags give you the same promotion workflow as container images — `v1.0.0` for immutable releases, `latest` for the current development head. For organizations using private ACR instances behind a virtual network, the deploying principal must have network line-of-sight to the registry at deployment time, which is an important consideration when running Bicep deployments from CI/CD runners that may not have direct ACR connectivity.

### Publishing and Consuming Modules

The publish workflow is straightforward: build the module to validate it, then push it to ACR with a version tag. Always use explicit version tags for production deployments; `latest` is a moving target that breaks reproducibility:

```bash
# Create Azure Container Registry for Bicep modules
az acr create \
  --name mycompanybicep \
  --resource-group shared-rg \
  --sku Basic

# Publish module to registry
az bicep publish \
  --file modules/networking/vnet.bicep \
  --target br:mycompanybicep.azurecr.io/bicep/modules/networking/vnet:v1.0.0

# Publish with latest tag
az bicep publish \
  --file modules/networking/vnet.bicep \
  --target br:mycompanybicep.azurecr.io/bicep/modules/networking/vnet:latest
```

Because Bicep modules are OCI artifacts, consuming them requires that the deployment principal (your user account or service principal) has `acrpull` permissions on the registry. Once authorized, you reference modules by their registry path — either the full `br:` URL or an alias configured in `bicepconfig.json`:

```bicep
// main.bicep

// Using module from private registry
module networking 'br:mycompanybicep.azurecr.io/bicep/modules/networking/vnet:v1.0.0' = {
  name: 'networking'
  params: {
    vnetName: 'myapp-vnet'
    // ...
  }
}

// Using module from public registry (Microsoft)
module appService 'br/public:avm/res/web/site:0.3.0' = {
  name: 'appService'
  params: {
    name: 'myapp-web'
    // ...
  }
}
```

### Configuring Module Aliases and Linting Rules

The `bicepconfig.json` file at your repository root controls two independent concerns: module registry aliases (so you write `br/mymodules:vnet:v1.0.0` instead of the full ACR URL) and linter rule severity (so your CI pipeline can block deployments on specific issues). The linter configuration is not cosmetic — it directly affects deployment safety, with the `secure-secrets-in-params` rule at `error` level blocking any deployment where a parameter is not marked `@secure()` but could contain a secret, and `use-recent-api-versions` flagging resources pinned to outdated API versions:

```json
{
  "moduleAliases": {
    "br": {
      "myregistry": {
        "registry": "mycompanybicep.azurecr.io"
      },
      "public": {
        "registry": "mcr.microsoft.com",
        "modulePath": "bicep"
      }
    }
  },
  "analyzers": {
    "core": {
      "enabled": true,
      "rules": {
        "no-unused-params": {
          "level": "warning"
        },
        "no-unused-vars": {
          "level": "warning"
        },
        "prefer-interpolation": {
          "level": "warning"
        },
        "secure-secrets-in-params": {
          "level": "error"
        },
        "use-recent-api-versions": {
          "level": "warning"
        }
      }
    }
  }
}
```

During local development, warnings are informational nudges. In CI/CD, you can promote specific rules to `error` to enforce them as deployment gates, ensuring that every pull request that touches infrastructure code is held to the same standards regardless of which engineer authored it.

---

## Parameter Files

### Separating Configuration from Infrastructure Logic

A Bicep template describes what resources to create. A parameter file describes *for which environment* to create them — the specific names, SKUs, regions, and secrets that differ between dev, staging, and production. Keeping these concerns in separate files is not just good organization; it is a deployment safety boundary. You can review and approve a parameter file change (upgrading a VM SKU in production) without touching the infrastructure logic, and you can refactor the template (adding a new parameter) without accidentally changing production values.

Bicep supports two parameter file formats: the modern `.bicepparam` format (type-safe, with Key Vault secret references) and the legacy JSON format (familiar to ARM template users). For new projects, prefer `.bicepparam` — it uses the same Bicep syntax you already know, supports the full type system, and is checked by the compiler. The JSON format works but loses type safety (all values are JSON values, not Bicep-typed expressions), requires escaped JSON for complex objects, and uses a different Key Vault reference syntax that is harder to read. The Bicep compiler accepts both formats, so migrating incrementally is straightforward.

### The .bicepparam Format

A `.bicepparam` file declares which template it extends with `using '../main.bicep'`, then assigns values to each parameter using the same expression syntax as the main template. Complex values like arrays of subnet configurations are expressed inline, not as escaped JSON strings:

```bicep
// params/prod.bicepparam
using '../main.bicep'

param location = 'eastus'
param environment = 'prod'
param storageAccountName = 'myappprodstg'

// Complex objects
param subnets = [
  {
    name: 'web'
    addressPrefix: '10.0.1.0/24'
    nsgRules: [
      {
        name: 'AllowHTTPS'
        priority: 100
        direction: 'Inbound'
        access: 'Allow'
        protocol: 'Tcp'
        destinationPortRange: '443'
      }
    ]
  }
  {
    name: 'app'
    addressPrefix: '10.0.2.0/24'
  }
]

// Reference Key Vault secrets
param adminPassword = az.getSecret('<subscription-id>', 'myapp-kv-rg', 'myapp-kv', 'admin-password')
```

The `az.getSecret()` function is the Bicep-native way to reference Key Vault secrets at deployment time. The secret value is never stored in the parameter file, never appears in deployment logs, and never enters ARM deployment history. At deployment time, the Azure CLI retrieves the secret from Key Vault (using the deploying principal's credentials) and passes it to ARM as a secure parameter — you need `get` permission on the secret, the same RBAC model as any other Key Vault access.

### JSON Parameter Files (Legacy)

If you are migrating from ARM templates or working with tooling that expects the JSON format, Bicep still supports it. The JSON format uses ARM's parameter structure, with `reference` objects for Key Vault secrets rather than the `az.getSecret()` function. You might encounter this format in brownfield environments where existing deployment pipelines already consume JSON parameter files and converting them to `.bicepparam` is not yet prioritized. The key practical difference during migration is that JSON parameter files cannot reference Bicep-specific functions like `az.getSecret()`, so secrets are referenced through ARM's native Key Vault reference syntax shown below. When you are ready to modernize, converting a JSON parameter file to `.bicepparam` is mostly mechanical — replace the JSON structure with Bicep expressions, swap Key Vault references to `az.getSecret()`, and add the `using` directive to link to your template:

```json
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "location": {
      "value": "eastus"
    },
    "environment": {
      "value": "prod"
    },
    "storageAccountName": {
      "value": "myappprodstg"
    },
    "adminPassword": {
      "reference": {
        "keyVault": {
          "id": "/subscriptions/.../resourceGroups/myapp-kv-rg/providers/Microsoft.KeyVault/vaults/myapp-kv"
        },
        "secretName": "admin-password"
      }
    }
  }
}
```

---

## Advanced Bicep Patterns

### Conditional Resources — Infrastructure That Adapts

Not every environment needs every resource. Your production environment might need Log Analytics for long-term audit retention, while your dev environment can skip it to save cost. Rather than maintaining separate templates for each environment, use Bicep's conditional resource syntax to include or exclude resources based on a parameter value. The `if` keyword after the resource type tells Bicep to provision the resource only when the condition evaluates to `true`; when the condition is `false`, the resource declaration is effectively removed from the compiled ARM template — no empty resource, no cost, no deployment attempt:

```bicep
param deployDiagnostics bool = true
param environment string

// Conditional resource
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = if (deployDiagnostics) {
  name: 'myapp-logs'
  location: resourceGroup().location
  properties: {
    retentionInDays: environment == 'prod' ? 90 : 30
    sku: {
      name: 'PerGB2018'
    }
  }
}

// Use conditional output
output logAnalyticsId string = deployDiagnostics ? logAnalytics.id : ''
```

The conditional output pattern (`deployDiagnostics ? logAnalytics.id : ''`) is necessary because Bicep cannot resolve a symbol that does not exist. If `deployDiagnostics` is `false`, `logAnalytics` does not exist at deployment time, and any unconditional reference to `logAnalytics.id` would be a compile error. The ternary expression provides a fallback value that downstream modules can check.

### Loops — DRY Infrastructure at Scale

The most repetitive pattern in ARM JSON templates is copy-pasting resource definitions with small variations — a storage account per region, a subnet per tier, a diagnostic setting per resource. Bicep's `for` loops eliminate this copy-paste by generating resource declarations from arrays and objects. The syntax mirrors functional programming: `[for item in collection: { ... }]` creates one resource per element, with the loop variable bound to each element in sequence. When you need the index as well as the value, `[for (item, i) in collection: { ... }]` provides both:

```bicep
param locations array = [
  'eastus'
  'westus2'
  'westeurope'
]

param storageAccounts array = [
  { name: 'data', sku: 'Standard_LRS' }
  { name: 'logs', sku: 'Standard_GRS' }
  { name: 'backup', sku: 'Standard_RAGRS' }
]

// Loop with index
resource storageLoop 'Microsoft.Storage/storageAccounts@2023-01-01' = [for (account, i) in storageAccounts: {
  name: '${account.name}${uniqueString(resourceGroup().id)}${i}'
  location: resourceGroup().location
  sku: {
    name: account.sku
  }
  kind: 'StorageV2'
}]

// Loop for array output
output storageIds array = [for (account, i) in storageAccounts: storageLoop[i].id]

// Nested loops
resource multiRegionStorage 'Microsoft.Storage/storageAccounts@2023-01-01' = [for location in locations: {
  name: 'stg${uniqueString(location)}'
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
}]
```

The loop index (`i`) is critical for output expressions. `storageLoop[i].id` references the i-th resource created by the loop, because Bicep treats the loop result as an array indexed by iteration order. Without the index, you would need to reconstruct the resource ID from the parameters, which duplicates logic and creates drift risk when the naming formula changes.

### Existing Resources and Dependencies

Not every resource in your Azure environment was created by your Bicep template. Shared infrastructure — a central Key Vault, a hub VNet managed by the networking team, a Log Analytics workspace provisioned by the monitoring team — exists independently and should be referenced, not recreated. The `existing` keyword tells Bicep that the resource already exists; it looks it up at deployment time, makes its properties available to your template's expressions, but does not attempt to create, modify, or delete the resource:

```bicep
// Reference existing resource in same resource group
resource existingVnet 'Microsoft.Network/virtualNetworks@2023-05-01' existing = {
  name: 'myapp-vnet'
}

// Reference existing resource in different resource group
resource existingKeyVault 'Microsoft.KeyVault/vaults@2023-02-01' existing = {
  name: 'myapp-kv'
  scope: resourceGroup('myapp-shared-rg')
}

// Reference existing resource in different subscription
resource existingLogAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' existing = {
  name: 'central-logs'
  scope: resourceGroup('xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx', 'central-monitoring-rg')
}

// Use existing resource properties
resource vm 'Microsoft.Compute/virtualMachines@2023-07-01' = {
  name: 'myapp-vm'
  location: resourceGroup().location
  properties: {
    networkProfile: {
      networkInterfaces: [
        {
          id: existingNic.id
        }
      ]
    }
  }
}
```

The `existing` keyword has access control implications: the deploying principal needs read access to the existing resource (to resolve its properties) but does not need write access (since the template does not modify it). This separation lets a platform team manage shared infrastructure while application teams reference it — the same RBAC model that Azure itself enforces.

ARM resolves the dependency graph between resources automatically when you reference one resource's properties from another. But when the dependency is logical rather than syntactic — a VM extension that needs a storage account to exist even though it does not reference the storage account's ID — you use `dependsOn` to make the relationship explicit:

```bicep
// Implicit dependency (using resource reference)
resource nic 'Microsoft.Network/networkInterfaces@2023-05-01' = {
  name: 'myapp-nic'
  location: resourceGroup().location
  properties: {
    ipConfigurations: [
      {
        name: 'ipconfig1'
        properties: {
          subnet: {
            id: vnet.properties.subnets[0].id  // Implicit dependency
          }
        }
      }
    ]
  }
}

// Explicit dependency
resource vm 'Microsoft.Compute/virtualMachines@2023-07-01' = {
  name: 'myapp-vm'
  location: resourceGroup().location
  dependsOn: [
    nic
    diagnosticsExtension  // Must wait for extension
  ]
  // ...
}
```

Prefer implicit dependencies — they are self-documenting and cannot be accidentally removed during refactoring. Explicit `dependsOn` should be reserved for cases where the dependency is invisible in the property assignments, and you should always comment why the dependency exists so the next engineer does not remove it as "unnecessary."

---

## Deployment Scopes

ARM operates at four distinct scopes, each controlling a different level of the Azure resource hierarchy. Bicep's `targetScope` directive tells the deployment which scope to operate at, and the `scope` property on individual modules lets you deploy resources across scopes in a single template — a subscription-scoped `main.bicep` can create resource groups and then deploy resources into those groups, all in one deployment.

**Resource Group scope** is the default and the layer where most day-to-day infrastructure work happens. Every resource you deploy — VMs, storage accounts, VNets, databases — lives inside a resource group. Unless you set `targetScope` explicitly, this is what you get, and it is the right choice for single-service or single-environment deployments:

```bicep
// Resource Group scope (default)
// targetScope = 'resourceGroup'  // implicit

resource storage 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  // ...
}
```

**Subscription scope** is the entry point for environment provisioning. Here you deploy resource groups themselves, along with subscription-level resources like role assignments and policy assignments. A subscription-scoped template typically creates the resource groups that will host your workloads and then delegates to modules scoped to each group, keeping the provisioning logic centralized:

```bicep
// Subscription scope
targetScope = 'subscription'

resource rg 'Microsoft.Resources/resourceGroups@2023-07-01' = {
  name: 'myapp-rg'
  location: 'eastus'
}

// Deploy to the new resource group
module storage 'modules/storage.bicep' = {
  scope: rg
  name: 'storage'
  params: {
    // ...
  }
}
```

**Management Group scope** operates at the governance layer. It deploys Azure Policy definitions and assignments that inherit down to every subscription under the management group, letting you enforce tagging, region restrictions, and SKU allowlists across your entire organization from a single template:

```bicep
// Management Group scope
targetScope = 'managementGroup'

resource policyDefinition 'Microsoft.Authorization/policyDefinitions@2021-06-01' = {
  name: 'require-tags'
  properties: {
    policyType: 'Custom'
    mode: 'Indexed'
    // ...
  }
}
```

**Tenant scope** is the root of the hierarchy, used for creating management groups and tenant-level role assignments. Most teams will not author templates at this scope directly — it is typically managed by a central platform or identity team that controls the organizational structure itself:

```bicep
// Tenant scope
targetScope = 'tenant'

resource managementGroup 'Microsoft.Management/managementGroups@2021-04-01' = {
  name: 'mycompany-mg'
  properties: {
    displayName: 'My Company Management Group'
  }
}
```

---

## CI/CD with Bicep

### Integrating Infrastructure Deployment into Software Delivery

Infrastructure as Code earns its name when it flows through the same pipeline as application code: validate on pull request, preview with what-if, deploy on merge to main. This three-stage pattern — validate, preview, deploy — catches syntax errors and type mismatches in the cheapest possible environment (your CI runner), surfaces unexpected resource changes for human review before they reach production, and gates the actual deployment behind branch protection and environment approval rules. The pipeline below demonstrates this workflow using GitHub Actions with federated (OIDC) authentication, which eliminates the need to store Azure credentials as long-lived secrets by exchanging a GitHub-issued OIDC token for a short-lived Azure access token. The validate stage costs minutes of CI time and zero cloud resources; the what-if stage queries ARM for the actual current state of your resources, not a potentially-stale state file; and the deploy stage only executes on main after branch protection and review.

```yaml
# .github/workflows/bicep-deploy.yml
name: Deploy Bicep

on:
  push:
    branches: [main]
    paths:
      - 'infrastructure/**'
  pull_request:
    branches: [main]
    paths:
      - 'infrastructure/**'

permissions:
  id-token: write
  contents: read
  pull-requests: write

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Azure Login
        uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}

      - name: Bicep Build
        run: az bicep build --file infrastructure/main.bicep

      - name: Run Bicep Linter
        run: |
          az bicep lint --file infrastructure/main.bicep

      - name: Validate Template
        run: |
          az deployment sub validate \
            --location eastus \
            --template-file infrastructure/main.bicep \
            --parameters @infrastructure/params/dev.bicepparam

  what-if:
    needs: validate
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Azure Login
        uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}

      - name: What-If
        id: whatif
        run: |
          az deployment sub what-if \
            --location eastus \
            --template-file infrastructure/main.bicep \
            --parameters @infrastructure/params/dev.bicepparam \
            --no-pretty-print > whatif.txt

      - name: Comment PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const whatif = fs.readFileSync('whatif.txt', 'utf8');

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## Bicep What-If Results\n\`\`\`\n${whatif}\n\`\`\``
            });

  deploy:
    needs: what-if
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Azure Login
        uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}

      - name: Deploy
        run: |
          az deployment sub create \
            --location eastus \
            --template-file infrastructure/main.bicep \
            --parameters @infrastructure/params/prod.bicepparam \
            --name "deploy-${{ github.sha }}"
```

The deploy stage only runs on main, after review, and uses GitHub's `environment: production` protection rules to gate access. These protection rules can require specific reviewer approvals, limit which branches can deploy, and enforce a waiting period before deployment proceeds — all configured in the GitHub repository settings rather than in the pipeline YAML itself. Teams on Azure DevOps use a nearly identical three-stage pipeline structure, adapted to ADO's YAML schema and service connections:

```yaml
# azure-pipelines.yml
trigger:
  branches:
    include:
      - main
  paths:
    include:
      - infrastructure/*

pool:
  vmImage: ubuntu-latest

stages:
  - stage: Validate
    jobs:
      - job: ValidateBicep
        steps:
          - task: AzureCLI@2
            displayName: Bicep Build
            inputs:
              azureSubscription: 'Azure-Connection'
              scriptType: bash
              scriptLocation: inlineScript
              inlineScript: |
                az bicep build --file infrastructure/main.bicep

          - task: AzureCLI@2
            displayName: Validate Deployment
            inputs:
              azureSubscription: 'Azure-Connection'
              scriptType: bash
              scriptLocation: inlineScript
              inlineScript: |
                az deployment sub validate \
                  --location eastus \
                  --template-file infrastructure/main.bicep \
                  --parameters @infrastructure/params/$(Environment).bicepparam

  - stage: WhatIf
    dependsOn: Validate
    jobs:
      - job: WhatIf
        steps:
          - task: AzureCLI@2
            displayName: What-If Analysis
            inputs:
              azureSubscription: 'Azure-Connection'
              scriptType: bash
              scriptLocation: inlineScript
              inlineScript: |
                az deployment sub what-if \
                  --location eastus \
                  --template-file infrastructure/main.bicep \
                  --parameters @infrastructure/params/$(Environment).bicepparam

  - stage: Deploy
    dependsOn: WhatIf
    condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))
    jobs:
      - deployment: DeployBicep
        environment: production
        strategy:
          runOnce:
            deploy:
              steps:
                - checkout: self
                - task: AzureCLI@2
                  displayName: Deploy Bicep
                  inputs:
                    azureSubscription: 'Azure-Connection'
                    scriptType: bash
                    scriptLocation: inlineScript
                    inlineScript: |
                      az deployment sub create \
                        --location eastus \
                        --template-file infrastructure/main.bicep \
                        --parameters @infrastructure/params/prod.bicepparam
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Hardcoded resource names | Name conflicts prevent deploying the same template to multiple environments, and globally unique names like storage accounts can block any redeployment | Use `uniqueString()` with the resource group or subscription ID, combined with environment prefixes |
| No API version pinning in `bicepconfig.json` | Resources may use deprecated API versions (defaulting to the latest available at compile time), which can introduce breaking changes silently | Pin specific API versions in `bicepconfig.json` under the `use-recent-api-versions` rule, or audit with the linter |
| Secrets in plaintext parameters | Credentials appear in ARM deployment history, which is readable by anyone with read access to the resource group | Use `@secure()` decorator for parameters, and prefer `az.getSecret()` or Key Vault references for actual credential values |
| Missing `dependsOn` for logical dependencies | ARM may deploy resources in an order that fails because a logical prerequisite (not captured by property references) is not yet ready | Use `dependsOn` only when the dependency is invisible in property assignments; prefer implicit dependencies through property references |
| Skipping `what-if` before production deploy | Unexpected resource changes — especially deletions or property modifications — reach production without review | Always run `az deployment group what-if` before `create`; in CI/CD, gate deployment on what-if passing review |
| Copy-pasting resources instead of using modules | Inconsistency between environments, missed updates during changes, and maintenance burden proportional to the number of copies | Extract reusable patterns into modules; publish versioned modules to a Bicep registry for cross-team consumption |
| Omitting output values from modules | Downstream templates or deployment scripts cannot access resource IDs, endpoints, or names without hardcoding or separate lookups | Every module should expose at minimum its resource ID and primary endpoint; consuming templates should never construct resource IDs manually |
| Deploying at the wrong scope | Resources created in the wrong resource group or subscription, requiring manual cleanup and redeployment | Set `targetScope` explicitly and use the `scope` parameter on modules to control where each deployment lands; validate with `what-if` |

---

## Quiz

The following eight questions test your understanding of Bicep's transpilation model, secret management, dependency resolution, multi-region deployment, what-if previews, module registries, deployment scopes, and the `existing` keyword. Answer each question before revealing the detailed explanation below.

<details>
<summary>1. What is the relationship between Bicep and ARM templates, and why does this architectural choice matter?</summary>

**Answer:** Bicep is a domain-specific language (DSL) that **transpiles to ARM JSON templates**. When you deploy Bicep, the Bicep CLI converts the `.bicep` file to ARM JSON and passes it to Azure Resource Manager. ARM executes the deployment exactly as it would for a hand-written JSON template.

This architecture matters for two reasons. First, Bicep inherits ARM's entire capability surface — if ARM can deploy a resource type or API version, Bicep can too, on the same day Azure releases it. There is no provider plugin to update. Second, Bicep does not introduce a new state model. ARM deployment history is the authoritative record of what was deployed and when. You never need to manage, back up, or recover a state file.

You can inspect the generated ARM JSON at any time:
```bash
# See the generated ARM template
az bicep build --file main.bicep --stdout
```
</details>

<details>
<summary>2. How do you securely reference secrets from Key Vault in Bicep, and why is this better than plaintext parameters?</summary>

**Answer:** Two methods exist, both of which avoid ever storing the secret value in source code, parameter files, or deployment history.

**Method 1: In a `.bicepparam` file using `az.getSecret()`**
```bicep
param adminPassword = az.getSecret(
  'subscription-id',
  'keyvault-rg',
  'keyvault-name',
  'secret-name'
)
```
At deployment time, the Azure CLI retrieves the secret from Key Vault using the deploying principal's credentials and passes it to ARM as a secure parameter. The secret never appears in logs.

**Method 2: Using an `existing` Key Vault resource**
```bicep
resource kv 'Microsoft.KeyVault/vaults@2023-02-01' existing = {
  name: 'mykeyvault'
  scope: resourceGroup('keyvault-rg')
}

module vm 'vm.bicep' = {
  params: {
    adminPassword: kv.getSecret('vm-password')
  }
}
```

Plaintext parameters are dangerous because ARM deployment history stores all parameter values — including plaintext secrets — and anyone with read access to the resource group can retrieve them. Using Key Vault references eliminates this exposure.
</details>

<details>
<summary>3. What is the difference between implicit and explicit dependencies, and when should you use each?</summary>

**Answer:**

**Implicit dependency** (preferred): Bicep automatically creates dependencies when your resource references another resource's property. ARM detects the property reference during the deployment graph resolution and ensures the referenced resource exists first:
```bicep
resource nic 'Microsoft.Network/networkInterfaces@2023-05-01' = {
  properties: {
    ipConfigurations: [{
      properties: {
        subnet: {
          id: vnet.properties.subnets[0].id  // Implicit dependency on vnet
        }
      }
    }]
  }
}
```

**Explicit dependency**: Use `dependsOn` when the dependency is logical rather than syntactic — meaning the resource does not reference the prerequisite's properties, but still needs it to exist. A common case is a VM extension that needs a storage account to exist (for script downloads) even though the extension definition does not contain the storage account's resource ID:
```bicep
resource extension 'Microsoft.Compute/virtualMachines/extensions@2023-07-01' = {
  parent: vm
  dependsOn: [
    storageAccount  // VM extension needs storage but doesn't reference it
  ]
}
```

Prefer implicit dependencies — they are self-documenting and cannot be accidentally removed during refactoring. Use explicit `dependsOn` only when the dependency relationship is invisible in the property assignments, and always add a comment explaining why.
</details>

<details>
<summary>4. How do you deploy resources to multiple Azure regions with Bicep, and what are the two approaches?</summary>

**Answer:** Two approaches, depending on whether the resources live in the same resource group or different ones.

**Approach 1: Same resource group, multiple regions (loop over locations)**
```bicep
param locations array = ['eastus', 'westeurope', 'southeastasia']

resource storageAccounts 'Microsoft.Storage/storageAccounts@2023-01-01' = [for location in locations: {
  name: 'stg${uniqueString(resourceGroup().id, location)}'
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
}]

output storageEndpoints array = [for (location, i) in locations: {
  location: location
  endpoint: storageAccounts[i].properties.primaryEndpoints.blob
}]
```

**Approach 2: Different resource groups per region (module loop with scope)**
```bicep
module regionalDeployment 'regional.bicep' = [for location in locations: {
  scope: resourceGroup('myapp-${location}-rg')
  name: 'deploy-${location}'
  params: {
    location: location
  }
}]
```

Approach 1 works when you want to manage regional resources within a single resource group. Approach 2 is necessary when you need separate resource groups per region — each module instance deploys to its own resource group, and the loop generates one deployment per region.
</details>

<details>
<summary>5. What is the purpose of `what-if` deployment, and how does it differ from `terraform plan`?</summary>

**Answer:** What-if shows what changes Azure would make without actually making them. It queries ARM directly for the current state of every resource in the template and compares it against the desired state:

```bash
az deployment group what-if \
  --resource-group myapp-rg \
  --template-file main.bicep \
  --parameters @params/prod.bicepparam
```

Output shows four categories:
- **Create**: New resources to be created
- **Delete**: Resources to be removed
- **Modify**: Properties that will change (with before/after values)
- **NoChange**: Resources that will remain unchanged

The key difference from `terraform plan` is the **source of truth**. Terraform plan compares desired configuration against the state file, which can drift from reality if someone made a change through the portal or CLI. Bicep what-if queries the Azure control plane directly — the current state of each resource in Azure, not the last-known state in a file. This means what-if detects drift automatically, without needing a separate refresh step. Always run what-if before production deployments and review the output for unexpected modifications or deletions.
</details>

<details>
<summary>6. How do you publish and consume Bicep modules from a registry?</summary>

**Answer:** Bicep uses Azure Container Registry (ACR) as its module registry, storing modules as OCI artifacts.

**Publish a module:**
```bash
az bicep publish \
  --file modules/vnet.bicep \
  --target br:myregistry.azurecr.io/bicep/modules/vnet:v1.0.0
```

**Consume a module:**
```bicep
module networking 'br:myregistry.azurecr.io/bicep/modules/vnet:v1.0.0' = {
  name: 'networking'
  params: {
    vnetName: 'myapp-vnet'
  }
}
```

**Configure an alias in `bicepconfig.json`:** to shorten registry references:
```json
{
  "moduleAliases": {
    "br": {
      "mymodules": {
        "registry": "myregistry.azurecr.io",
        "modulePath": "bicep/modules"
      }
    }
  }
}
```

Then consume with: `module vnet 'br/mymodules:vnet:v1.0.0'`

The public Microsoft registry is available at `br/public:avm/...` and contains Azure Verified Modules — production-grade, Microsoft-maintained modules for common Azure patterns. Check AVM before writing your own module; it may already exist.
</details>

<details>
<summary>7. What are the four deployment scopes in Bicep, and what resources can you deploy at each?</summary>

**Answer:** Four deployment scopes, in order of increasing hierarchy breadth:

1. **resourceGroup** (default): Deploy any Azure resource that lives in a resource group — VMs, storage accounts, VNets, databases. This is where most day-to-day infrastructure work happens.

2. **subscription**: Deploy resource groups themselves, plus subscription-level resources like role assignments and policy assignments. This is the entry point for environment provisioning.

3. **managementGroup**: Deploy policy definitions and assignments that apply across multiple subscriptions. Governance teams use this scope to enforce tagging, region restrictions, and SKU allowlists across the organization.

4. **tenant**: Deploy management groups themselves and tenant-level role assignments. This is the root of the hierarchy; most teams interact with tenant-scoped templates only through their central platform or identity team.

The `targetScope` directive selects the scope, and individual modules can use the `scope` property to deploy to a different scope than the calling template — enabling a single subscription-scoped `main.bicep` to create resource groups and deploy resources into them in one deployment.
</details>

<details>
<summary>8. How do you reference existing resources that were not created by your Bicep template?</summary>

**Answer:** Use the `existing` keyword. Bicep looks up the resource in Azure at deployment time, makes its properties available to your template's expressions, but does **not** attempt to create, modify, or delete the resource:

```bicep
// Same resource group
resource existingVnet 'Microsoft.Network/virtualNetworks@2023-05-01' existing = {
  name: 'my-existing-vnet'
}

// Different resource group
resource existingKeyVault 'Microsoft.KeyVault/vaults@2023-02-01' existing = {
  name: 'my-keyvault'
  scope: resourceGroup('other-rg')
}

// Different subscription
resource existingStorage 'Microsoft.Storage/storageAccounts@2023-01-01' existing = {
  name: 'mystorageaccount'
  scope: resourceGroup('sub-id', 'storage-rg')
}

// Use existing resource
resource newSubnet 'Microsoft.Network/virtualNetworks/subnets@2023-05-01' = {
  parent: existingVnet
  name: 'new-subnet'
  properties: {
    addressPrefix: '10.0.99.0/24'
  }
}
```

The deploying principal needs read access to the existing resource to resolve its properties but does not need write access. This separation means application teams can reference shared infrastructure (hub VNets, central Key Vaults, Log Analytics workspaces) without the ability to modify it — the RBAC model that Azure itself enforces.
</details>

---

## Hands-On Exercise

### Exercise: Multi-Environment Deployment with Modules

**Objective:** Create a modular Bicep deployment for a web application with environment-specific configurations. You will practice module composition, parameter files, and the deploy-validate-whatif workflow.

**Tasks:** Follow the steps below, creating each file as specified and running the validation commands in order to verify correctness at each stage before proceeding.

**Success Criteria:** All checkboxes below must be verifiable. Run each validation command and confirm the output matches expectations before checking the box.
```bash
mkdir -p bicep-lab/{modules,params}
cd bicep-lab
```

2. Create a networking module:
```bicep
// modules/networking.bicep
param vnetName string
param location string = resourceGroup().location
param addressPrefix string = '10.0.0.0/16'
param tags object = {}

resource vnet 'Microsoft.Network/virtualNetworks@2023-05-01' = {
  name: vnetName
  location: location
  tags: tags
  properties: {
    addressSpace: {
      addressPrefixes: [addressPrefix]
    }
    subnets: [
      {
        name: 'web'
        properties: { addressPrefix: '10.0.1.0/24' }
      }
      {
        name: 'app'
        properties: { addressPrefix: '10.0.2.0/24' }
      }
    ]
  }
}

output vnetId string = vnet.id
output webSubnetId string = vnet.properties.subnets[0].id
```

3. Create main template:
```bicep
// main.bicep
targetScope = 'subscription'

param location string = 'eastus'
param environment string

resource rg 'Microsoft.Resources/resourceGroups@2023-07-01' = {
  name: 'webapp-${environment}-rg'
  location: location
}

module networking 'modules/networking.bicep' = {
  scope: rg
  name: 'networking'
  params: {
    vnetName: 'webapp-${environment}-vnet'
    location: location
    tags: {
      Environment: environment
    }
  }
}
```

4. Create parameter files:
```bicep
// params/dev.bicepparam
using '../main.bicep'
param location = 'eastus'
param environment = 'dev'
```

5. Validate and deploy:
```bash
# Validate
az deployment sub validate \
  --location eastus \
  --template-file main.bicep \
  --parameters @params/dev.bicepparam

# What-if
az deployment sub what-if \
  --location eastus \
  --template-file main.bicep \
  --parameters @params/dev.bicepparam

# Deploy
az deployment sub create \
  --location eastus \
  --template-file main.bicep \
  --parameters @params/dev.bicepparam
```

**Success Criteria:** Verify each of the following outcomes by running the specified validation commands and confirming the results match expectations before considering the exercise complete:

- [ ] Bicep builds without errors: `az bicep build --file main.bicep` exits with code 0 and produces `main.json`
- [ ] Linter passes with no warnings: `az bicep lint --file main.bicep` shows no issues in the output
- [ ] What-if shows expected resources: one resource group named `webapp-dev-rg`, one VNet with two subnets (`web` and `app`)
- [ ] Deployment completes successfully: `az deployment sub create` returns with `provisioningState: Succeeded`
- [ ] Resources are tagged correctly: the resource group and VNet both have `Environment: dev` in their tags
- [ ] Module outputs are accessible: the VNet ID and web subnet ID appear in the deployment outputs

---

## Next Module

You have completed the IaC Toolkit! Continue your learning:
- [Module 6.1: IaC Fundamentals](/platform/disciplines/delivery-automation/iac/module-6.1-iac-fundamentals/) — Review core concepts
- [Platform Engineering Track](/platform/disciplines/core-platform/platform-engineering/) — Apply IaC in platform contexts
- [GitOps Discipline](/platform/disciplines/delivery-automation/gitops/) — Combine IaC with GitOps practices

---

## Sources

- [Bicep Documentation — Microsoft Learn](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/)
- [Bicep GitHub Repository](https://github.com/Azure/bicep)
- [ARM Template Reference](https://learn.microsoft.com/en-us/azure/templates/)
- [Bicep Configuration (bicepconfig.json)](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/bicep-config)
- [Bicep Parameter Files](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/parameter-files)
- [Bicep Modules](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/modules)
- [What-If Deployment](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/deploy-what-if)
- [Bicep Deployment Stacks](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/deployment-stacks)
- [Install Bicep](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/install)
- [Bicep Playground](https://aka.ms/bicepdemo)
- [Azure Verified Modules](https://azure.github.io/Azure-Verified-Modules/)
- [Bicep VS Code Extension](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-bicep)
- [Bicep Registry Modules (GitHub)](https://github.com/Azure/bicep-registry-modules)
- [ARM Templates Overview](https://learn.microsoft.com/en-us/azure/azure-resource-manager/templates/overview)
- [Bicep Learning Path — Microsoft Learn](https://learn.microsoft.com/en-us/training/paths/bicep-deploy/)
- [Bicep Best Practices](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/best-practices)
- [Quickstart: Create Bicep Files with VS Code](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/quickstart-create-bicep-use-visual-studio-code)
- [Decompiling ARM Templates to Bicep](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/decompile)
- [Use Azure Key Vault to Pass Secure Parameter Values](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/key-vault-parameter)
- [Comparing JSON and Bicep for Templates](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/compare-template-syntax)
- [Bicep Linter](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/linter)
- [Bicep Frequently Asked Questions](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/frequently-asked-questions)
- [Azure Resource Manager Overview](https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/overview)
- [PSRule for Azure — Bicep Validation](https://azure.github.io/PSRule.Rules.Azure/)
- [Terraform AzureRM Provider](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)
- [Pulumi Azure Native Provider](https://www.pulumi.com/registry/packages/azure-native/)

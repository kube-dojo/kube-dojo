---
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
- [Module 6.1: IaC Fundamentals](../../disciplines/delivery-automation/iac/module-6.1-iac-fundamentals/)
- Azure subscription with Contributor access
- Azure CLI installed (`az --version`)
- Basic understanding of Azure Resource Manager (ARM)

---

## Why This Module Matters

*The ARM template sprawled across 2,847 lines of impenetrable JSON.*

When the fintech startup's platform engineer opened the infrastructure code inherited from their acquisition, she found ARM templates that would make a seasoned developer weep. Nested JSON objects 15 levels deep. Copy-pasted resource definitions with subtle differences. No comments, no documentation, no hope of understanding what it actually deployed.

The team had two choices: continue the suffering or rewrite everything. They chose to rewrite—but not in Terraform. Their Azure-only environment, compliance requirements, and need for same-day Azure feature support pointed to one solution: **Bicep**.

In three weeks, they converted 47 ARM templates into 12 Bicep modules. Lines of code dropped by 60%. The DevOps team could finally read their infrastructure. New engineers onboarded in days instead of weeks.

**Bicep isn't just "ARM templates made readable."** It's Azure's answer to the HCL question: what if infrastructure code could be concise, type-safe, and actually pleasant to write?

**This module teaches you** Bicep's syntax, module system, and deployment patterns. You'll learn why Azure shops increasingly choose Bicep over Terraform—and when you might choose differently.

---

## War Story: The ARM Template That Ate Christmas

**Characters:**
- Diego: Azure Cloud Architect (7 years experience)
- Team: 4 engineers managing Azure infrastructure
- Stack: 200+ Azure resources across 3 environments

**The Incident:**

December 23rd. Diego's team needed to deploy a critical security patch before the holiday freeze. The patch required modifying a single parameter in an ARM template.

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

**What Bicep Fixed:**
1. **Readability**: 60% less code, actual syntax highlighting
2. **Type safety**: Catches errors before deployment
3. **IntelliSense**: VS Code knows Azure resource properties
4. **No string interpolation hell**: Clean variable references
5. **Modules**: Reusable, parameterized components

**Lessons Learned:**
1. JSON is not a programming language
2. Readability = maintainability = reliability
3. "We don't have time to rewrite" is often false
4. Native tools get Azure features first

---

## Bicep vs. ARM Templates: The Evolution

### Why Bicep Exists

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

### Bicep vs. Terraform: Comparison

| Aspect | Bicep | Terraform |
|--------|-------|-----------|
| **Cloud support** | Azure only | Multi-cloud |
| **State management** | Azure-managed (ARM) | File-based |
| **New Azure features** | Day-0 support | Days-to-weeks delay |
| **Language** | Bicep DSL | HCL |
| **Learning curve** | Moderate | Moderate |
| **IDE support** | Excellent (VS Code) | Excellent |
| **Community modules** | Growing | Extensive |
| **Testing frameworks** | Limited | Terratest, etc. |
| **Deployment** | Azure CLI / PowerShell | Terraform CLI |
| **Cost** | Free | Free (open-source) |

**When to choose Bicep:**
- Azure-only environment
- Need immediate access to new Azure features
- Team already knows ARM concepts
- Compliance requires Azure-native tooling
- Don't want to manage state files

**When to choose Terraform:**
- Multi-cloud environment
- Team has Terraform expertise
- Need extensive community modules
- Complex state manipulation needed

---

## Bicep Fundamentals

### Installation and Setup

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

### Basic Syntax

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

### Deploying Bicep

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

---

## Bicep Modules

### Module Structure

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

### Using Modules

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

---

## Bicep Registry and Versioning

### Publishing to Registry

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

### Using Registry Modules

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

### bicepconfig.json

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

---

## Parameter Files

### Bicep Parameter File (.bicepparam)

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

### JSON Parameter File (Legacy)

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

### Conditional Resources

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

### Loops and Iterations

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

### Existing Resources

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

### Resource Dependencies

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

---

## Deployment Scopes

### Different Deployment Levels

```bicep
// Resource Group scope (default)
// targetScope = 'resourceGroup'  // implicit

resource storage 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  // ...
}
```

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

### GitHub Actions Pipeline

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

### Azure DevOps Pipeline

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
| Hardcoded resource names | Name conflicts, not reusable | Use `uniqueString()` and parameters |
| No API version pinning | Breaking changes on upgrade | Pin specific API versions in bicepconfig.json |
| Secrets in parameters | Credentials exposed in deployment history | Use Key Vault references |
| Missing dependsOn | Resources created before dependencies | Use resource references (implicit) or explicit dependsOn |
| No what-if before deploy | Unexpected changes in production | Always run `az deployment what-if` first |
| Ignoring linter warnings | Potential bugs or security issues | Configure bicepconfig.json rules as errors |
| Copy-pasting resources | Inconsistency, maintenance burden | Create modules for reusable components |
| No output values | Can't use resources from other templates | Add outputs for IDs, endpoints, names |
| Wrong scope | Resources created in wrong location | Set targetScope and use scope parameter |
| Not using existing resources | Recreating resources that already exist | Use `existing` keyword for references |

---

## Quiz

Test your Bicep knowledge:

<details>
<summary>1. What is the relationship between Bicep and ARM templates?</summary>

**Answer:** Bicep is a domain-specific language (DSL) that **transpiles to ARM JSON templates**. When you deploy Bicep:

1. Bicep CLI converts .bicep to ARM JSON
2. ARM JSON is sent to Azure Resource Manager
3. ARM deploys the resources

Benefits:
- Same deployment engine = same capabilities
- Day-0 support for new Azure features
- Can decompile ARM JSON to Bicep
- State managed by Azure (no state files)

```bash
# See the generated ARM template
az bicep build --file main.bicep --stdout
```
</details>

<details>
<summary>2. How do you reference secrets from Key Vault in Bicep?</summary>

**Answer:** Two methods:

**Method 1: In parameter file (.bicepparam)**
```bicep
param adminPassword = az.getSecret(
  'subscription-id',
  'keyvault-rg',
  'keyvault-name',
  'secret-name'
)
```

**Method 2: Using existing resource**
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

Secrets are never exposed in deployment history with these methods.
</details>

<details>
<summary>3. What is the difference between implicit and explicit dependencies?</summary>

**Answer:**

**Implicit dependency** (preferred): Bicep automatically creates dependencies when you reference another resource:
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

**Explicit dependency**: Use `dependsOn` when there's no property reference:
```bicep
resource extension 'Microsoft.Compute/virtualMachines/extensions@2023-07-01' = {
  parent: vm
  dependsOn: [
    storageAccount  // VM extension needs storage but doesn't reference it
  ]
}
```

Prefer implicit dependencies—they're cleaner and self-documenting.
</details>

<details>
<summary>4. How do you deploy resources to multiple regions with Bicep?</summary>

**Answer:** Use loops over a locations array:

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

For more complex scenarios, use modules with `scope` to deploy to different resource groups:

```bicep
module regionalDeployment 'regional.bicep' = [for location in locations: {
  scope: resourceGroup('myapp-${location}-rg')
  name: 'deploy-${location}'
  params: {
    location: location
  }
}]
```
</details>

<details>
<summary>5. What is the purpose of `what-if` deployment?</summary>

**Answer:** What-if shows what changes Azure would make without actually making them—similar to Terraform plan:

```bash
az deployment group what-if \
  --resource-group myapp-rg \
  --template-file main.bicep \
  --parameters @params/prod.bicepparam
```

Output shows:
- **Create**: New resources to be created
- **Delete**: Resources to be removed
- **Modify**: Properties that will change
- **NoChange**: Resources unchanged

Always run what-if before production deployments to catch unexpected changes.
</details>

<details>
<summary>6. How do you use Bicep modules from a registry?</summary>

**Answer:**

**Publish module:**
```bash
az bicep publish \
  --file modules/vnet.bicep \
  --target br:myregistry.azurecr.io/bicep/modules/vnet:v1.0.0
```

**Use module:**
```bicep
module networking 'br:myregistry.azurecr.io/bicep/modules/vnet:v1.0.0' = {
  name: 'networking'
  params: {
    vnetName: 'myapp-vnet'
  }
}
```

**Configure alias in bicepconfig.json:**
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

Then use: `module vnet 'br/mymodules:vnet:v1.0.0'`
</details>

<details>
<summary>7. What are the different deployment scopes in Bicep?</summary>

**Answer:** Four deployment scopes:

1. **resourceGroup** (default): Deploy to a resource group
   ```bicep
   // targetScope = 'resourceGroup'  // implicit
   resource storage 'Microsoft.Storage/...' = { }
   ```

2. **subscription**: Deploy resource groups, policies
   ```bicep
   targetScope = 'subscription'
   resource rg 'Microsoft.Resources/resourceGroups@...' = { }
   ```

3. **managementGroup**: Deploy policies across subscriptions
   ```bicep
   targetScope = 'managementGroup'
   resource policy 'Microsoft.Authorization/policyDefinitions@...' = { }
   ```

4. **tenant**: Deploy management groups
   ```bicep
   targetScope = 'tenant'
   resource mg 'Microsoft.Management/managementGroups@...' = { }
   ```
</details>

<details>
<summary>8. How do you reference existing resources that weren't created by your template?</summary>

**Answer:** Use the `existing` keyword:

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
</details>

---

## Key Takeaways

1. **Bicep transpiles to ARM**: Same deployment engine, cleaner syntax
2. **Day-0 Azure support**: New Azure features work immediately
3. **No state files**: Azure manages state—no corruption risk
4. **Type-safe with IntelliSense**: VS Code catches errors before deployment
5. **Modules for reusability**: Build a library of composable components
6. **Registry for sharing**: Publish versioned modules to Azure Container Registry
7. **What-if before deploy**: Always preview changes before production
8. **Scopes control where**: resourceGroup, subscription, managementGroup, tenant
9. **Existing keyword**: Reference resources created outside your template
10. **Parameter files**: Separate configuration from code

---

## Did You Know?

1. **Bicep was created by a single engineer** (Anthony Martin) at Microsoft who was frustrated with ARM template JSON. It started as a side project before becoming an official Azure product.

2. **You can decompile ARM to Bicep** with `az bicep decompile --file template.json`. This makes migration from existing ARM templates straightforward (though manual cleanup is often needed).

3. **The name "Bicep"** is a playful reference to ARM (Azure Resource Manager)—biceps are part of your arm. Microsoft's naming humor at work.

4. **Azure Verified Modules (AVM)** is Microsoft's official repository of production-ready Bicep modules. These are maintained by Microsoft and follow strict quality standards—check them before writing your own modules.

---

## Hands-On Exercise

### Exercise: Multi-Environment Deployment with Modules

**Objective:** Create a modular Bicep deployment for a web application with environment-specific configurations.

**Tasks:**

1. Create the project structure:
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

**Success Criteria:**
- [ ] Bicep builds without errors
- [ ] Linter passes with no warnings
- [ ] What-if shows expected resources
- [ ] Deployment completes successfully
- [ ] Resources tagged correctly

---

## Next Steps

You've completed the IaC Toolkit! Continue your learning:
- [Module 6.1: IaC Fundamentals](../../disciplines/delivery-automation/iac/module-6.1-iac-fundamentals/) - Review core concepts
- [Platform Engineering Track](../../disciplines/core-platform/platform-engineering/) - Apply IaC in platform contexts
- [GitOps Discipline](../../disciplines/delivery-automation/gitops/) - Combine IaC with GitOps practices

---

## Further Reading

- [Bicep Documentation](https://learn.microsoft.com/azure/azure-resource-manager/bicep/)
- [Bicep Playground](https://aka.ms/bicepdemo) - Try Bicep in browser
- [Azure Verified Modules](https://aka.ms/avm)
- [Bicep GitHub Repository](https://github.com/Azure/bicep)
- [ARM Template Reference](https://learn.microsoft.com/azure/templates/)
- [Bicep VS Code Extension](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-bicep)

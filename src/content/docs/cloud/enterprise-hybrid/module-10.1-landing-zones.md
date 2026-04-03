---
title: "Module 10.1: Enterprise Landing Zones & Account Vending"
slug: cloud/enterprise-hybrid/module-10.1-landing-zones
sidebar:
  order: 2
---
**Complexity**: [COMPLEX] | **Time to Complete**: 3h | **Prerequisites**: Cloud Essentials (AWS/Azure/GCP), Kubernetes Basics, Cloud Architecture Patterns

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Design enterprise landing zones using AWS Control Tower, Azure Landing Zones, and GCP Organization Hierarchy**
- **Implement automated account vending machines that provision cloud accounts with Kubernetes clusters in under 30 minutes**
- **Configure guardrails (SCPs, Azure Policy, Organization Policies) that enforce security baselines across all accounts**
- **Deploy landing zone customizations that integrate Kubernetes cluster bootstrapping with GitOps from day zero**

---

## Why This Module Matters

In March 2023, a Fortune 500 insurance company attempted to launch a new Kubernetes-based claims processing platform. The development team had been building for nine months. When they requested a production AWS account, the cloud team told them the wait time was fourteen weeks. The reason: every account was manually provisioned. A senior cloud architect had to create the VPC, configure the Transit Gateway attachment, set up IAM roles, create the SCPs, register the account in the CMDB, provision the DNS delegation, and configure logging to the central SIEM. This architect handled three accounts per week. There were twenty-two teams in the queue.

The claims platform missed its launch window. A competitor released an equivalent product. The insurance company later estimated the delay cost them $8.6 million in lost first-mover revenue. The problem was not cloud technology. The problem was that the organization treated cloud account creation as an artisanal craft instead of an automated factory line.

Enterprise Landing Zones solve this exact problem. They are the foundational architecture that defines how an organization uses cloud at scale -- the account structure, the networking topology, the security guardrails, the identity model, and the automation that provisions all of it in minutes instead of weeks. When Kubernetes enters the picture, Landing Zones become even more critical: every cluster needs networking, identity, logging, and policy from day zero. In this module, you will learn how AWS Control Tower, Azure Landing Zones, and GCP Organization Hierarchy work, how to automate account vending with Kubernetes bootstrap included, and how to wire it all together so a team can go from "I need a cluster" to "I have a production-ready cluster" in under thirty minutes.

---

## The Landing Zone Mental Model

Before diving into specific cloud implementations, you need to understand what a Landing Zone actually is. Think of it as the building code for a city. Before anyone constructs a building, the city has already defined the zoning regulations, the sewer and electrical grid connections, the fire code, and the permit process. A Landing Zone does the same thing for cloud infrastructure.

### The Four Pillars

Every enterprise Landing Zone, regardless of cloud provider, addresses four pillars:

```text
┌─────────────────────────────────────────────────────────────────┐
│                    ENTERPRISE LANDING ZONE                       │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  IDENTITY &   │  │  NETWORK     │  │  SECURITY &  │          │
│  │  ACCESS       │  │  TOPOLOGY    │  │  COMPLIANCE  │          │
│  │              │  │              │  │              │          │
│  │ - SSO/IdP    │  │ - Hub-spoke  │  │ - SCPs/Policy│          │
│  │ - IAM roles  │  │ - Transit GW │  │ - Guardrails │          │
│  │ - RBAC       │  │ - DNS        │  │ - Logging    │          │
│  │ - Federation │  │ - Firewall   │  │ - Encryption │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
│  ┌──────────────────────────────────────────────────┐           │
│  │              ACCOUNT VENDING MACHINE              │           │
│  │                                                    │           │
│  │  Template → Provision → Wire → Validate → Deliver │           │
│  └──────────────────────────────────────────────────┘           │
│                                                                  │
│  Time: Request to Ready  =  < 30 minutes                        │
└─────────────────────────────────────────────────────────────────┘
```

**Identity and Access**: Who can do what, across every account, with centralized SSO and federated identity. This must extend from cloud IAM into Kubernetes RBAC seamlessly.

**Network Topology**: How accounts connect to each other, to on-premises data centers, and to the internet. Every Kubernetes cluster needs a network that is already wired into this topology from birth.

**Security and Compliance**: The guardrails that prevent teams from doing dangerous things (like opening port 22 to the internet) while enabling them to move fast on everything else. These guardrails must cover both cloud resources and Kubernetes configurations.

**Account Vending**: The automation that provisions new accounts (or subscriptions, or projects) with all three pillars pre-configured. This is the factory line that eliminates the fourteen-week wait.

---

## AWS Control Tower and Account Factory

AWS Control Tower is Amazon's opinionated Landing Zone solution. It builds on top of AWS Organizations, AWS SSO (now IAM Identity Center), AWS Config, and AWS CloudTrail to create a multi-account environment with pre-configured guardrails.

### Architecture Overview

```text
┌──────────────────────────────────────────────────────────────┐
│                    AWS Organization                            │
│                                                                │
│  Root OU                                                       │
│  ├── Security OU                                               │
│  │   ├── Log Archive Account (CloudTrail, Config logs)        │
│  │   └── Audit Account (Security Hub, GuardDuty delegated)    │
│  │                                                             │
│  ├── Infrastructure OU                                         │
│  │   ├── Network Hub Account (Transit GW, DNS, firewalls)     │
│  │   └── Shared Services Account (CI/CD, container registry)  │
│  │                                                             │
│  ├── Sandbox OU (relaxed guardrails)                           │
│  │   └── Developer sandbox accounts                           │
│  │                                                             │
│  ├── Workloads OU                                              │
│  │   ├── Production OU (strict guardrails)                    │
│  │   │   ├── Team-Alpha-Prod                                  │
│  │   │   └── Team-Beta-Prod                                   │
│  │   └── Non-Production OU                                    │
│  │       ├── Team-Alpha-Dev                                   │
│  │       └── Team-Beta-Staging                                │
│  │                                                             │
│  └── Suspended OU (decommissioned accounts)                   │
│                                                                │
│  Guardrails: SCPs attached at each OU level                    │
│  Identity: IAM Identity Center with permission sets            │
│  Logging: Centralized in Log Archive account                   │
└──────────────────────────────────────────────────────────────┘
```

### Setting Up Control Tower

```bash
# Control Tower is set up via the AWS Console, but you can manage it via CLI after setup
# List enrolled accounts
aws controltower list-enabled-controls \
  --target-identifier "arn:aws:organizations::123456789012:ou/o-abc123/ou-xyz789"

# Check guardrail status
aws controltower list-enabled-controls \
  --target-identifier "arn:aws:organizations::123456789012:ou/o-abc123/ou-xyz789" \
  --query 'enabledControls[*].{Control:controlIdentifier, Status:statusSummary.status}'
```

### Account Factory for Terraform (AFT)

The real power comes from Account Factory for Terraform (AFT), which turns account vending into a GitOps workflow. You define an account in a Terraform file, push to a repo, and AFT provisions the account with all Landing Zone configurations.

```hcl
# account-requests/team-alpha-production.tf
module "team_alpha_prod" {
  source = "./modules/aft-account-request"

  control_tower_parameters = {
    AccountEmail              = "team-alpha-prod@company.com"
    AccountName               = "Team-Alpha-Production"
    ManagedOrganizationalUnit = "Workloads/Production"
    SSOUserEmail              = "team-alpha-lead@company.com"
    SSOUserFirstName          = "Platform"
    SSOUserLastName           = "Team"
  }

  account_tags = {
    team        = "alpha"
    environment = "production"
    cost-center = "CC-4521"
    data-class  = "confidential"
  }

  # Custom fields that trigger account customizations
  account_customizations_name = "k8s-production-baseline"

  change_management_parameters = {
    change_requested_by = "platform-team"
    change_reason       = "New production workload account for Team Alpha"
  }
}
```

### Kubernetes Bootstrap in Account Vending

The critical extension for Kubernetes-centric organizations is wiring cluster provisioning into the account vending pipeline. When an account is created, the customization pipeline can automatically:

1. Create a VPC with the standard CIDR from the IPAM pool
2. Attach the VPC to the Transit Gateway
3. Provision an EKS cluster with the organization's baseline configuration
4. Install mandatory add-ons (logging, monitoring, policy enforcement)
5. Configure Access Entries for the team's IAM roles
6. Register the cluster with the central Backstage catalog

```bash
#!/bin/bash
# AFT account customization script: k8s-production-baseline
# This runs automatically after account creation

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION="us-east-1"

# Step 1: Create VPC from IPAM pool
VPC_CIDR=$(aws ec2 allocate-ipam-pool-cidr \
  --ipam-pool-id ipam-pool-0abc123 \
  --netmask-length 20 \
  --query 'IpamPoolAllocation.Cidr' --output text)

# Step 2: Deploy baseline infrastructure via Terraform
cd /opt/aft/customizations/k8s-baseline
terraform init
terraform apply -auto-approve \
  -var="account_id=${ACCOUNT_ID}" \
  -var="vpc_cidr=${VPC_CIDR}" \
  -var="cluster_name=eks-${ACCOUNT_ID}-prod" \
  -var="cluster_version=1.32"

# Step 3: Register cluster in Backstage catalog
CLUSTER_ENDPOINT=$(aws eks describe-cluster \
  --name "eks-${ACCOUNT_ID}-prod" \
  --query 'cluster.endpoint' --output text)

curl -X POST "https://backstage.internal.company.com/api/catalog/entities" \
  -H "Content-Type: application/json" \
  -d "{
    \"apiVersion\": \"backstage.io/v1alpha1\",
    \"kind\": \"Resource\",
    \"metadata\": {
      \"name\": \"eks-${ACCOUNT_ID}-prod\",
      \"annotations\": {
        \"kubernetes.io/cluster-name\": \"eks-${ACCOUNT_ID}-prod\"
      }
    },
    \"spec\": {
      \"type\": \"kubernetes-cluster\",
      \"owner\": \"team-alpha\",
      \"lifecycle\": \"production\"
    }
  }"

echo "Account ${ACCOUNT_ID} fully provisioned with EKS cluster"
```

---

## Azure Landing Zones and Subscription Vending

Azure takes a similar but structurally different approach. Instead of accounts, Azure uses Subscriptions organized under Management Groups. The Azure Landing Zone architecture (formerly known as Enterprise-Scale) is a reference architecture maintained by Microsoft's Cloud Adoption Framework team.

### Azure Landing Zone Architecture

```text
┌──────────────────────────────────────────────────────────────┐
│                    Azure AD Tenant                             │
│                                                                │
│  Root Management Group                                         │
│  ├── Platform                                                  │
│  │   ├── Management (Log Analytics, Automation)               │
│  │   ├── Identity (Active Directory, DNS)                     │
│  │   └── Connectivity (Hub VNet, ExpressRoute, Firewall)      │
│  │                                                             │
│  ├── Landing Zones                                             │
│  │   ├── Corp (internal apps, private networking)             │
│  │   │   ├── Team-Alpha-Prod Subscription                     │
│  │   │   └── Team-Beta-Prod Subscription                      │
│  │   └── Online (internet-facing apps)                        │
│  │       ├── Team-Alpha-Web Subscription                      │
│  │       └── Team-Beta-API Subscription                       │
│  │                                                             │
│  ├── Sandbox                                                   │
│  │   └── Developer subscriptions (relaxed policies)           │
│  │                                                             │
│  └── Decommissioned                                            │
│                                                                │
│  Hub-Spoke Network: Azure Firewall + VNet Peering             │
│  Policy: Azure Policy assigned at Management Group level       │
│  Identity: Azure AD + RBAC + AKS Azure AD integration         │
└──────────────────────────────────────────────────────────────┘
```

### Subscription Vending with Bicep

```bicep
// subscription-vending/main.bicep
targetScope = 'managementGroup'

@description('Name of the workload team')
param teamName string

@description('Environment: dev, staging, production')
param environment string

@description('Whether to provision an AKS cluster')
param provisionAKS bool = true

// Create the subscription
module subscription 'modules/subscription.bicep' = {
  name: 'sub-${teamName}-${environment}'
  params: {
    subscriptionName: 'sub-${teamName}-${environment}'
    managementGroupId: environment == 'production' ? 'mg-landing-zones-corp' : 'mg-landing-zones-sandbox'
    billingScope: '/providers/Microsoft.Billing/billingAccounts/1234/enrollmentAccounts/5678'
    tags: {
      team: teamName
      environment: environment
      costCenter: 'CC-${teamName}'
    }
  }
}

// Deploy networking into the new subscription
module networking 'modules/spoke-vnet.bicep' = {
  name: 'net-${teamName}-${environment}'
  scope: subscription
  params: {
    vnetName: 'vnet-${teamName}-${environment}'
    vnetAddressSpace: '10.${uniqueOctet}.0.0/16'
    hubVnetId: '/subscriptions/hub-sub-id/resourceGroups/rg-hub/providers/Microsoft.Network/virtualNetworks/vnet-hub'
    firewallPrivateIp: '10.0.1.4'
  }
}

// Deploy AKS if requested
module aks 'modules/aks-baseline.bicep' = if (provisionAKS) {
  name: 'aks-${teamName}-${environment}'
  scope: subscription
  params: {
    clusterName: 'aks-${teamName}-${environment}'
    kubernetesVersion: '1.32'
    subnetId: networking.outputs.aksSubnetId
    aadAdminGroupId: '${teamName}-k8s-admins'  // Azure AD group
    enableDefender: environment == 'production'
    enablePolicyAddon: true
  }
}
```

### Identity Integration: Azure AD to AKS

Azure's biggest advantage for enterprises already using Microsoft is the seamless identity chain from Azure AD through to Kubernetes RBAC:

```bash
# Azure AD Group → AKS RBAC (no aws-auth equivalent needed)
# The AKS cluster natively understands Azure AD tokens

# Create an Azure AD group for cluster admins
az ad group create --display-name "aks-team-alpha-admins" \
  --mail-nickname "aks-team-alpha-admins"

# Assign the group as AKS cluster admin
az role assignment create \
  --assignee-object-id $(az ad group show -g "aks-team-alpha-admins" --query id -o tsv) \
  --role "Azure Kubernetes Service Cluster Admin Role" \
  --scope "/subscriptions/$SUB_ID/resourceGroups/rg-alpha/providers/Microsoft.ContainerService/managedClusters/aks-alpha-prod"

# Developers get namespace-scoped access
az role assignment create \
  --assignee-object-id $(az ad group show -g "aks-team-alpha-devs" --query id -o tsv) \
  --role "Azure Kubernetes Service Cluster User Role" \
  --scope "/subscriptions/$SUB_ID/resourceGroups/rg-alpha/providers/Microsoft.ContainerService/managedClusters/aks-alpha-prod"
```

---

## GCP Organization Hierarchy and Project Factory

Google Cloud organizes resources under an Organization, with Folders providing the hierarchy and Projects serving as the account boundary.

### GCP Landing Zone Structure

```text
┌──────────────────────────────────────────────────────────────┐
│                    GCP Organization                            │
│                                                                │
│  org-policies/  (Organization-level constraints)              │
│                                                                │
│  Folders:                                                      │
│  ├── Bootstrap (Terraform state, CI/CD service accounts)      │
│  ├── Common (shared VPC host projects, logging, DNS)          │
│  ├── Production                                                │
│  │   ├── team-alpha-prod (project)                            │
│  │   └── team-beta-prod (project)                             │
│  ├── Non-Production                                            │
│  │   ├── team-alpha-dev (project)                             │
│  │   └── team-beta-staging (project)                          │
│  └── Sandbox                                                   │
│      └── developer-sandbox-* (projects)                       │
│                                                                │
│  Shared VPC: Host project in Common, service projects in LZ   │
│  Identity: Google Workspace / Cloud Identity + Workload ID    │
│  Logging: Organization sink → BigQuery + Cloud Logging        │
└──────────────────────────────────────────────────────────────┘
```

### Project Factory with Terraform

Google's Cloud Foundation Toolkit provides a Project Factory module that automates project vending:

```hcl
# project-factory/team-alpha-prod.tf
module "team_alpha_prod" {
  source  = "terraform-google-modules/project-factory/google"
  version = "~> 15.0"

  name                    = "team-alpha-prod"
  org_id                  = "123456789"
  folder_id               = google_folder.production.id
  billing_account         = "AABBCC-112233-DDEEFF"
  default_service_account = "disable"

  activate_apis = [
    "container.googleapis.com",
    "compute.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "dns.googleapis.com",
  ]

  shared_vpc         = "vpc-host-project"
  shared_vpc_subnets = [
    "projects/vpc-host-project/regions/us-central1/subnetworks/team-alpha-prod-nodes",
    "projects/vpc-host-project/regions/us-central1/subnetworks/team-alpha-prod-pods",
    "projects/vpc-host-project/regions/us-central1/subnetworks/team-alpha-prod-services",
  ]

  labels = {
    team        = "alpha"
    environment = "production"
    cost_center = "cc_4521"
  }
}

# GKE cluster in the vended project
module "gke_alpha_prod" {
  source  = "terraform-google-modules/kubernetes-engine/google//modules/private-cluster"
  version = "~> 33.0"

  project_id        = module.team_alpha_prod.project_id
  name              = "gke-alpha-prod"
  region            = "us-central1"
  network           = "vpc-host-network"
  subnetwork        = "team-alpha-prod-nodes"
  ip_range_pods     = "team-alpha-prod-pods"
  ip_range_services = "team-alpha-prod-services"

  enable_private_nodes    = true
  enable_private_endpoint = false
  master_ipv4_cidr_block  = "172.16.0.0/28"

  release_channel = "REGULAR"

  node_pools = [
    {
      name         = "general"
      machine_type = "e2-standard-4"
      min_count    = 2
      max_count    = 10
      auto_upgrade = true
    }
  ]
}
```

---

## Guardrails: Preventive and Detective Controls

Landing Zones without guardrails are just organized chaos. Guardrails come in two flavors: **preventive** (stop bad things before they happen) and **detective** (find bad things after they happen and alert).

### Preventive Guardrails Across Clouds

| Guardrail | AWS (SCP) | Azure (Policy) | GCP (Org Policy) |
| :--- | :--- | :--- | :--- |
| Deny public S3/Storage buckets | SCP on OU | `Deny` effect policy | `constraints/storage.publicAccessPrevention` |
| Require encryption at rest | SCP deny unencrypted | `DeployIfNotExists` | `constraints/compute.requireOsLogin` |
| Restrict regions | SCP deny non-approved regions | `AllowedLocations` | `constraints/gcp.resourceLocations` |
| Deny privilege escalation | SCP deny IAM:* except break-glass | Custom policy definition | `constraints/iam.disableServiceAccountKeyCreation` |
| Require tags/labels | SCP deny untagged resources | `Require tag` initiative | Custom org policy |
| Block public Kubernetes API | SCP deny public EKS endpoint | `Deny public AKS` | `constraints/container.restrictPublicCluster` |

### Example: AWS SCP for Kubernetes Guardrails

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyPublicEKSEndpoint",
      "Effect": "Deny",
      "Action": [
        "eks:CreateCluster",
        "eks:UpdateClusterConfig"
      ],
      "Resource": "*",
      "Condition": {
        "ForAnyValue:StringEquals": {
          "eks:endpointPublicAccess": "true"
        }
      }
    },
    {
      "Sid": "DenyEKSWithoutLogging",
      "Effect": "Deny",
      "Action": "eks:CreateCluster",
      "Resource": "*",
      "Condition": {
        "Null": {
          "eks:logging": "true"
        }
      }
    },
    {
      "Sid": "RequireEKSEncryption",
      "Effect": "Deny",
      "Action": "eks:CreateCluster",
      "Resource": "*",
      "Condition": {
        "Null": {
          "eks:encryptionConfig": "true"
        }
      }
    }
  ]
}
```

### Connecting Cloud Guardrails to Kubernetes Policy

The key insight that most organizations miss is that cloud guardrails and Kubernetes policy engines must work together as a unified system. A cloud SCP can prevent a public EKS endpoint, but it cannot prevent a Kubernetes Service of type LoadBalancer from creating a public-facing ALB. For that, you need an in-cluster policy engine.

```text
┌─────────────────────────────────────────────────────────┐
│                    GUARDRAIL LAYERS                       │
│                                                           │
│  Layer 1: Cloud Provider   ──► SCPs / Azure Policy / Org │
│           (Preventive)          Policy                    │
│           What resources can be created?                  │
│                                                           │
│  Layer 2: Infrastructure   ──► Terraform/Crossplane       │
│           as Code               validation (pre-apply)    │
│           Is the configuration correct?                   │
│                                                           │
│  Layer 3: Kubernetes       ──► Kyverno / OPA Gatekeeper   │
│           Admission             (ValidatingWebhook)       │
│           Is the K8s manifest compliant?                  │
│                                                           │
│  Layer 4: Runtime          ──► Falco / KubeArmor          │
│           Detection             (eBPF runtime policy)     │
│           Is the workload behaving correctly?             │
└─────────────────────────────────────────────────────────┘
```

---

## Backstage as the Enterprise Front Door

Backstage, originally built by Spotify and now a CNCF incubating project, has become the standard Internal Developer Platform (IDP) for enterprise Landing Zones. It serves as the self-service portal where teams request infrastructure without needing to understand the underlying automation.

### How Backstage Fits Into Account Vending

```text
┌───────────────────────────────────────────────────────────┐
│  Developer clicks "New Project" in Backstage               │
│                                                            │
│  ┌──────────┐     ┌──────────────┐     ┌──────────────┐  │
│  │ Backstage │────►│  Software    │────►│  Git Repo    │  │
│  │ Template  │     │  Template    │     │  (with TF/   │  │
│  │ Wizard    │     │  Engine      │     │   Crossplane)│  │
│  └──────────┘     └──────────────┘     └──────┬───────┘  │
│                                                │          │
│                                        ┌───────▼───────┐  │
│                                        │  CI/CD Pipeline│  │
│                                        │  (AFT / Azure  │  │
│                                        │   Pipelines)   │  │
│                                        └───────┬───────┘  │
│                                                │          │
│  ┌──────────────────────────────────────────────▼───────┐  │
│  │  Provisioned Account/Subscription/Project            │  │
│  │  + VPC/VNet + EKS/AKS/GKE Cluster                   │  │
│  │  + GitOps repo + ArgoCD Application                  │  │
│  │  + Registered in Backstage Catalog                   │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────┘
```

### Backstage Software Template for K8s Environment

```yaml
# backstage-templates/new-k8s-environment.yaml
apiVersion: scaffolder.backstage.io/v1beta3
kind: Template
metadata:
  name: new-k8s-environment
  title: Request New Kubernetes Environment
  description: Provision a new cloud account with a production-ready K8s cluster
  tags:
    - kubernetes
    - infrastructure
spec:
  owner: platform-team
  type: environment

  parameters:
    - title: Team Information
      required:
        - teamName
        - costCenter
      properties:
        teamName:
          title: Team Name
          type: string
          pattern: '^[a-z][a-z0-9-]{2,20}$'
        costCenter:
          title: Cost Center
          type: string

    - title: Environment Configuration
      required:
        - environment
        - cloudProvider
        - region
      properties:
        environment:
          title: Environment
          type: string
          enum: ['development', 'staging', 'production']
        cloudProvider:
          title: Cloud Provider
          type: string
          enum: ['aws', 'azure', 'gcp']
        region:
          title: Region
          type: string
          enum: ['us-east-1', 'eu-west-1', 'ap-southeast-1']

    - title: Cluster Configuration
      properties:
        clusterSize:
          title: Cluster Size
          type: string
          enum: ['small', 'medium', 'large']
          default: 'medium'
          description: |
            small: 2-5 nodes, dev/test workloads
            medium: 3-20 nodes, production services
            large: 5-100 nodes, high-traffic production
        enableServiceMesh:
          title: Enable Istio Service Mesh
          type: boolean
          default: false
        enableGPU:
          title: Include GPU Node Pool
          type: boolean
          default: false

  steps:
    - id: generate-terraform
      name: Generate Infrastructure Code
      action: fetch:template
      input:
        url: ./skeleton
        values:
          teamName: ${{ parameters.teamName }}
          environment: ${{ parameters.environment }}
          cloudProvider: ${{ parameters.cloudProvider }}
          region: ${{ parameters.region }}
          clusterSize: ${{ parameters.clusterSize }}

    - id: create-repo
      name: Create Infrastructure Repository
      action: publish:github
      input:
        repoUrl: github.com?owner=company-infra&repo=env-${{ parameters.teamName }}-${{ parameters.environment }}
        defaultBranch: main

    - id: trigger-pipeline
      name: Trigger Provisioning Pipeline
      action: github:actions:dispatch
      input:
        repoUrl: github.com?owner=company-infra&repo=env-${{ parameters.teamName }}-${{ parameters.environment }}
        workflowId: provision.yml

    - id: register-catalog
      name: Register in Backstage Catalog
      action: catalog:register
      input:
        repoContentsUrl: ${{ steps['create-repo'].output.repoContentsUrl }}
        catalogInfoPath: /catalog-info.yaml

  output:
    links:
      - title: Infrastructure Repository
        url: ${{ steps['create-repo'].output.remoteUrl }}
      - title: Provisioning Pipeline
        url: ${{ steps['trigger-pipeline'].output.runUrl }}
```

*War Story: A telecommunications company with 2,300 engineers implemented Backstage-driven account vending in 2024. Before Backstage, their average time from "team needs infrastructure" to "team has a working cluster" was 23 business days. After implementing the template system, it dropped to 38 minutes. The platform team reported that the most surprising benefit was not speed but consistency -- every cluster came out identical, with the same monitoring, the same policies, and the same security baseline. The number of "snowflake cluster" incidents dropped by 91%.*

---

## Did You Know?

1. AWS Control Tower manages over 350,000 organizational accounts as of early 2025. The Account Factory for Terraform (AFT) was originally an internal AWS tool used by their own teams to provision accounts for new AWS services. They open-sourced it after realizing that enterprise customers were building inferior versions of the same thing independently.

2. Azure Landing Zones were redesigned three times between 2019 and 2023. The original "Enterprise-Scale" architecture was so complex that Microsoft found only 12% of enterprises could implement it successfully. The current "Azure Landing Zones" approach reduced the minimum viable deployment from 6 weeks to 3 days by making more decisions opinionated rather than configurable.

3. The concept of "guardrails vs. gates" revolutionized how enterprises think about cloud governance. Gates require approval before proceeding (slow, bottleneck). Guardrails prevent dangerous actions automatically but allow everything else (fast, scalable). The term was popularized by AWS in 2019, and within two years, every major cloud provider adopted the language. The distinction matters for Kubernetes too: Kyverno and Gatekeeper are guardrails, while manual YAML review is a gate.

4. Backstage crossed 2,800 adopting companies in 2025 and has over 200 community plugins. The most popular plugin category is "infrastructure provisioning," which directly maps to the account vending pattern. Spotify's internal Backstage instance has over 4,500 registered software templates, and their average developer provisions new infrastructure 3.2 times per month through it.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
| :--- | :--- | :--- |
| **One giant account for everything** | Simplicity. "We only have 3 teams, we do not need multiple accounts." Then the organization grows to 30 teams. | Start with multi-account from day one. The overhead is minimal with automation, and retrofitting is extremely painful. |
| **Landing Zone without Kubernetes integration** | The Landing Zone team is a separate group from the Kubernetes platform team. They design the zone without considering K8s networking, identity, or policy needs. | Include Kubernetes architects in Landing Zone design. Every account template should include VPC sizing for pod CIDRs, IAM roles for cluster operations, and policy baseline for K8s. |
| **Manual account vending** | "We only create accounts once a quarter, automation is overkill." Then demand spikes and the queue grows to months. | Automate account vending from the start. Even if you provision one account per month, the automation ensures consistency and eliminates human error. |
| **Guardrails too restrictive** | Security team designs guardrails without developer input. Developers cannot deploy basic workloads. Shadow IT begins. | Co-design guardrails with developers. Start permissive and tighten based on actual incidents. Monitor guardrail denials to find legitimate use cases being blocked. |
| **No DNS strategy in the Landing Zone** | DNS is treated as an afterthought. Each account manages its own DNS, leading to naming conflicts and resolution failures across the hub-spoke network. | Design DNS delegation as part of the Landing Zone: a central Route53/Azure DNS/Cloud DNS zone with automatic subdomain delegation per account. |
| **Ignoring IPAM from the start** | VPC CIDR ranges assigned ad-hoc. Within 18 months, overlapping CIDRs prevent Transit Gateway peering, and pod IP exhaustion appears in tightly-sized clusters. | Use AWS VPC IPAM, Azure IPAM, or a third-party tool like NetBox. Assign CIDRs from a centralized pool that accounts for node IPs, pod IPs, and service IPs per cluster. |
| **Backstage template without validation** | Templates allow any input. Teams create clusters with names that violate DNS conventions or sizes that exceed their budget approval. | Add JSON Schema validation to Backstage templates. Implement approval workflows for production environments. Connect cost estimation to the template wizard. |
| **No Landing Zone lifecycle plan** | Landing Zone is deployed once and never updated. Cloud providers release new features (like EKS Pod Identity or AKS Workload Identity) but the baseline never adopts them. | Treat the Landing Zone as a product with a roadmap. Quarterly reviews of cloud provider releases. Automated testing of Landing Zone updates before rollout. |

---

## Quiz

<details>
<summary>Question 1: Your organization has 15 teams, each with dev, staging, and production environments. A colleague suggests using a single AWS account with namespaces to isolate teams. Why is this a bad idea for enterprise Kubernetes?</summary>

A single account creates a **blast radius problem** and an **IAM complexity nightmare**. First, all teams share the same AWS service quotas (like EC2 instance limits, EBS volumes, and EKS cluster count). One team's runaway autoscaling can exhaust quotas for everyone. Second, IAM policies in a single account must use resource-level conditions to separate access, which becomes unmanageably complex with 15 teams. Third, billing attribution requires complex tagging instead of simple per-account cost reports. Fourth, a security breach in one team's workload potentially exposes all teams' data since they share the same account boundary. The multi-account pattern gives each team (or each environment) its own blast radius, its own quotas, its own billing, and its own security boundary.
</details>

<details>
<summary>Question 2: What is the difference between a preventive guardrail and a detective guardrail? Give one example of each for Kubernetes in the cloud.</summary>

A **preventive guardrail** stops a non-compliant action before it happens. Example: an AWS SCP that denies `eks:CreateCluster` when `endpointPublicAccess` is true. The cluster simply cannot be created with a public endpoint. A **detective guardrail** identifies non-compliant resources after they are created and alerts or remediates. Example: an AWS Config rule that checks all EKS clusters for enabled audit logging and flags non-compliant clusters in Security Hub. Preventive guardrails are stronger (they prevent the problem) but more rigid. Detective guardrails are more flexible (they allow creation but monitor compliance) and work better for existing resources that predate the guardrail. A mature Landing Zone uses both in combination.
</details>

<details>
<summary>Question 3: A developer wants to provision a new Kubernetes cluster. With the Landing Zone described in this module, what is the sequence of events from request to running cluster?</summary>

The sequence is: (1) Developer opens Backstage and selects the "New Kubernetes Environment" template. (2) They fill in team name, environment, cloud provider, region, and cluster size. (3) Backstage's scaffolder generates infrastructure-as-code files from the template skeleton. (4) The scaffolder creates a new Git repository with the generated code. (5) A CI/CD pipeline (triggered by the repository creation) runs the IaC -- this provisions the cloud account (via AFT/subscription vending/project factory), creates the VPC, deploys the K8s cluster, installs baseline add-ons, and configures identity. (6) The pipeline registers the new cluster in the Backstage catalog. (7) The developer sees the cluster appear in Backstage with connection instructions. Total time: under 30 minutes for the automation, zero manual approvals for non-production environments.
</details>

<details>
<summary>Question 4: Why does the Landing Zone need to account for Kubernetes pod CIDRs when designing the VPC/VNet IP address plan?</summary>

In cloud-native Kubernetes deployments like EKS with VPC CNI, **each pod gets a real VPC IP address**. A node running 30 pods consumes 30+ IP addresses from the subnet. A cluster with 50 nodes could consume 1,500+ IPs just for pods. If the Landing Zone designed VPCs with /24 subnets (251 usable IPs), the cluster would be IP-exhausted almost immediately. The IPAM strategy must allocate large enough CIDRs -- typically /16 or /17 per VPC -- with dedicated subnets for nodes, pods, and services. Azure CNI has similar requirements. GKE uses secondary IP ranges (alias IPs) which need dedicated /14 ranges for pod CIDRs. Ignoring pod IP requirements during Landing Zone design is the number one cause of retroactive VPC redesigns in enterprise Kubernetes.
</details>

<details>
<summary>Question 5: How does identity propagation work from the cloud Landing Zone into Kubernetes RBAC? Compare the AWS and Azure approaches.</summary>

In **AWS**, identity propagation works through EKS Access Entries (modern) or the aws-auth ConfigMap (legacy). An IAM role from the Landing Zone (e.g., `TeamAlphaDevRole`) is mapped to a Kubernetes RBAC identity via an Access Entry and Access Policy. The chain is: AWS IAM Identity Center -> Assume IAM Role -> EKS Access Entry -> Kubernetes RBAC. In **Azure**, the chain is more direct: Azure AD user/group -> AKS Azure AD integration -> Kubernetes RBAC. Azure AD groups can be directly referenced in Kubernetes ClusterRoleBindings. Azure's approach is more seamless because AKS natively understands Azure AD tokens, while EKS requires the explicit mapping layer. Both approaches should be automated as part of the account/subscription vending process so that teams have correct RBAC from day one.
</details>

<details>
<summary>Question 6: What is the risk of deploying a Landing Zone without including the Kubernetes platform team in the design?</summary>

The Landing Zone will have **architectural blind spots** that create friction or outright blockers for Kubernetes workloads. Common issues include: (1) VPC subnets too small for pod IP allocation, forcing expensive VPC redesigns. (2) Transit Gateway routing that does not account for pod CIDR ranges, breaking cross-cluster communication. (3) SCPs that inadvertently block Kubernetes operations (like denying EC2 actions needed by the cluster autoscaler). (4) DNS delegation that does not support ExternalDNS or cert-manager. (5) Logging pipelines that cannot ingest Kubernetes audit logs. (6) IAM role designs that do not support IRSA or Pod Identity. Each of these is expensive to fix after deployment and could have been prevented with a single architecture review session.
</details>

<details>
<summary>Question 7: Your company uses Backstage for self-service infrastructure. A team submits a request for a production Kubernetes cluster. Should this be automatically provisioned without approval?</summary>

**It depends on the environment and the organization's risk tolerance.** For non-production environments (dev, staging), automatic provisioning is ideal -- it maximizes developer velocity and the cost risk is low. For production environments, most enterprises implement an **approval gate** within the Backstage workflow. This is not a manual infrastructure review (the automation handles correctness) but a business approval: confirming the cost center has budget, the team has completed security training, and there is a documented service owner. The key principle is that the approval should be about **business readiness**, not technical correctness. If your guardrails are properly configured, the technical correctness is guaranteed by the automation itself.
</details>

---

## Hands-On Exercise: Build a Mini Landing Zone with Account Vending

In this exercise, you will simulate an enterprise Landing Zone using local tools. You will create a multi-account structure, implement guardrails, and build a self-service vending pipeline that provisions a Kubernetes cluster.

**What you will build:**

```text
┌──────────────────────────────────────────────────┐
│  Simulated Landing Zone (using kind + Crossplane) │
│                                                    │
│  Management Cluster (kind)                         │
│  ├── Crossplane (infrastructure provisioner)       │
│  ├── Kyverno (guardrails)                          │
│  └── Backstage (self-service portal)               │
│                                                    │
│  Vending Pipeline:                                 │
│  1. Create namespace (simulates account)           │
│  2. Apply network policies (simulates VPC)         │
│  3. Deploy workload cluster (kind-in-kind)         │
│  4. Install baseline (monitoring, policy)           │
│  5. Register in catalog                            │
└──────────────────────────────────────────────────┘
```

### Task 1: Create the Management Cluster

Set up the local management cluster that will serve as your Landing Zone control plane.

<details>
<summary>Solution</summary>

```bash
# Create a kind cluster to act as the management cluster
cat <<'EOF' > /tmp/mgmt-cluster.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: landing-zone-mgmt
nodes:
  - role: control-plane
  - role: worker
  - role: worker
EOF

kind create cluster --config /tmp/mgmt-cluster.yaml

# Verify the cluster is running
k get nodes
# NAME                               STATUS   ROLES           AGE   VERSION
# landing-zone-mgmt-control-plane    Ready    control-plane   45s   v1.32.0
# landing-zone-mgmt-worker           Ready    <none>          30s   v1.32.0
# landing-zone-mgmt-worker2          Ready    <none>          30s   v1.32.0
```

</details>

### Task 2: Install the Guardrail Layer

Deploy Kyverno and create policies that simulate enterprise guardrails (no privileged containers, mandatory labels, resource limits required).

<details>
<summary>Solution</summary>

```bash
# Install Kyverno
helm repo add kyverno https://kyverno.github.io/kyverno/
helm install kyverno kyverno/kyverno -n kyverno --create-namespace --wait

# Create enterprise guardrail policies
cat <<'EOF' | k apply -f -
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-team-label
  annotations:
    policies.kyverno.io/description: "All namespaces must have a team label"
spec:
  validationFailureAction: Enforce
  rules:
    - name: check-team-label
      match:
        any:
          - resources:
              kinds:
                - Namespace
      exclude:
        any:
          - resources:
              namespaces:
                - kube-system
                - kube-public
                - kube-node-lease
                - kyverno
                - default
      validate:
        message: "Namespace must have a 'team' label. This is required by the Landing Zone policy."
        pattern:
          metadata:
            labels:
              team: "?*"
---
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: deny-privileged
spec:
  validationFailureAction: Enforce
  rules:
    - name: deny-privileged-containers
      match:
        any:
          - resources:
              kinds:
                - Pod
      exclude:
        any:
          - resources:
              namespaces:
                - kube-system
                - kyverno
      validate:
        message: "Privileged containers are not allowed by Landing Zone policy."
        pattern:
          spec:
            containers:
              - securityContext:
                  privileged: "!true"
---
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-resource-limits
spec:
  validationFailureAction: Enforce
  rules:
    - name: check-limits
      match:
        any:
          - resources:
              kinds:
                - Pod
      exclude:
        any:
          - resources:
              namespaces:
                - kube-system
                - kyverno
      validate:
        message: "All containers must have CPU and memory limits set."
        pattern:
          spec:
            containers:
              - resources:
                  limits:
                    memory: "?*"
                    cpu: "?*"
EOF

# Test the guardrails
echo "Testing: namespace without team label (should fail)"
k create namespace bad-namespace 2>&1 || true

echo "Testing: namespace with team label (should succeed)"
k create namespace good-namespace --dry-run=server -o yaml \
  | k label --local -f - team=alpha --dry-run=client -o yaml \
  | k apply -f - --dry-run=server
```

</details>

### Task 3: Create an Account Vending Script

Build a script that simulates account vending -- creating a namespace with all the Landing Zone baseline configurations.

<details>
<summary>Solution</summary>

```bash
cat <<'SCRIPT' > /tmp/vend-account.sh
#!/bin/bash
set -euo pipefail

TEAM_NAME=$1
ENVIRONMENT=$2

NAMESPACE="${TEAM_NAME}-${ENVIRONMENT}"
echo "=== Vending account: ${NAMESPACE} ==="

# Step 1: Create namespace with required labels
echo "[1/5] Creating namespace with Landing Zone labels..."
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Namespace
metadata:
  name: ${NAMESPACE}
  labels:
    team: ${TEAM_NAME}
    environment: ${ENVIRONMENT}
    managed-by: landing-zone
    cost-center: "cc-${TEAM_NAME}"
EOF

# Step 2: Apply network policies (simulates VPC isolation)
echo "[2/5] Applying network isolation policies..."
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
  namespace: ${NAMESPACE}
spec:
  podSelector: {}
  policyTypes:
    - Ingress
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-same-namespace
  namespace: ${NAMESPACE}
spec:
  podSelector: {}
  ingress:
    - from:
        - podSelector: {}
  policyTypes:
    - Ingress
EOF

# Step 3: Create resource quotas
echo "[3/5] Setting resource quotas..."
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ResourceQuota
metadata:
  name: landing-zone-quota
  namespace: ${NAMESPACE}
spec:
  hard:
    requests.cpu: "8"
    requests.memory: 16Gi
    limits.cpu: "16"
    limits.memory: 32Gi
    pods: "50"
    services.loadbalancers: "2"
EOF

# Step 4: Create RBAC for the team
echo "[4/5] Configuring RBAC..."
cat <<EOF | kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: team-developer
  namespace: ${NAMESPACE}
rules:
  - apiGroups: ["", "apps", "batch"]
    resources: ["pods", "deployments", "services", "configmaps", "secrets", "jobs"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
  - apiGroups: [""]
    resources: ["pods/log", "pods/exec"]
    verbs: ["get", "create"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: team-developer-binding
  namespace: ${NAMESPACE}
subjects:
  - kind: Group
    name: "team-${TEAM_NAME}-developers"
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: team-developer
  apiGroup: rbac.authorization.k8s.io
EOF

# Step 5: Deploy baseline monitoring
echo "[5/5] Deploying baseline services..."
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: landing-zone-config
  namespace: ${NAMESPACE}
data:
  team: "${TEAM_NAME}"
  environment: "${ENVIRONMENT}"
  provisioned-at: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  landing-zone-version: "2.1.0"
EOF

echo ""
echo "=== Account vended successfully ==="
echo "Namespace:    ${NAMESPACE}"
echo "Team:         ${TEAM_NAME}"
echo "Environment:  ${ENVIRONMENT}"
echo "Quotas:       CPU 8/16 req/limit, Memory 16/32Gi req/limit"
echo "Network:      Default deny ingress, allow same-namespace"
echo "RBAC:         team-${TEAM_NAME}-developers -> team-developer role"
SCRIPT

chmod +x /tmp/vend-account.sh

# Vend accounts for two teams
/tmp/vend-account.sh alpha production
/tmp/vend-account.sh beta development

# Verify the vended accounts
k get namespaces -l managed-by=landing-zone
k get resourcequota -A -l managed-by!=null 2>/dev/null || k get resourcequota -n alpha-production
k get networkpolicy -n alpha-production
```

</details>

### Task 4: Test Guardrail Enforcement

Verify that the guardrails prevent non-compliant resources in vended accounts.

<details>
<summary>Solution</summary>

```bash
# Test 1: Try to create a privileged pod (should be denied)
echo "--- Test: Privileged pod (expect DENIED) ---"
cat <<'EOF' | k apply -f - 2>&1 || true
apiVersion: v1
kind: Pod
metadata:
  name: bad-privileged-pod
  namespace: alpha-production
spec:
  containers:
    - name: evil
      image: nginx:1.27
      securityContext:
        privileged: true
      resources:
        limits:
          cpu: 100m
          memory: 128Mi
EOF

# Test 2: Try to create a pod without resource limits (should be denied)
echo "--- Test: Pod without limits (expect DENIED) ---"
cat <<'EOF' | k apply -f - 2>&1 || true
apiVersion: v1
kind: Pod
metadata:
  name: no-limits-pod
  namespace: alpha-production
spec:
  containers:
    - name: wasteful
      image: nginx:1.27
EOF

# Test 3: Create a compliant pod (should succeed)
echo "--- Test: Compliant pod (expect SUCCESS) ---"
cat <<'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: good-pod
  namespace: alpha-production
spec:
  containers:
    - name: web
      image: nginx:1.27
      securityContext:
        privileged: false
      resources:
        limits:
          cpu: 100m
          memory: 128Mi
        requests:
          cpu: 50m
          memory: 64Mi
EOF

# Verify the compliant pod is running
k get pods -n alpha-production
```

</details>

### Task 5: Audit the Landing Zone

Generate a compliance report for all vended accounts.

<details>
<summary>Solution</summary>

```bash
cat <<'SCRIPT' > /tmp/audit-landing-zone.sh
#!/bin/bash
echo "========================================="
echo "  LANDING ZONE COMPLIANCE AUDIT REPORT"
echo "  Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "========================================="
echo ""

# List all vended namespaces
NAMESPACES=$(kubectl get namespaces -l managed-by=landing-zone -o jsonpath='{.items[*].metadata.name}')

for NS in $NAMESPACES; do
  echo "--- Namespace: $NS ---"
  TEAM=$(kubectl get namespace $NS -o jsonpath='{.metadata.labels.team}')
  ENV=$(kubectl get namespace $NS -o jsonpath='{.metadata.labels.environment}')
  echo "  Team: $TEAM | Environment: $ENV"

  # Check network policies
  NP_COUNT=$(kubectl get networkpolicy -n $NS --no-headers 2>/dev/null | wc -l)
  if [ "$NP_COUNT" -ge 1 ]; then
    echo "  Network Policies: PASS ($NP_COUNT policies)"
  else
    echo "  Network Policies: FAIL (no policies found)"
  fi

  # Check resource quotas
  RQ_COUNT=$(kubectl get resourcequota -n $NS --no-headers 2>/dev/null | wc -l)
  if [ "$RQ_COUNT" -ge 1 ]; then
    echo "  Resource Quotas: PASS ($RQ_COUNT quotas)"
  else
    echo "  Resource Quotas: FAIL (no quotas found)"
  fi

  # Check RBAC
  ROLE_COUNT=$(kubectl get role -n $NS --no-headers 2>/dev/null | wc -l)
  if [ "$ROLE_COUNT" -ge 1 ]; then
    echo "  RBAC Roles: PASS ($ROLE_COUNT roles)"
  else
    echo "  RBAC Roles: FAIL (no roles found)"
  fi

  # Check Kyverno policy reports
  VIOLATIONS=$(kubectl get policyreport -n $NS -o jsonpath='{.items[*].summary.fail}' 2>/dev/null)
  if [ -z "$VIOLATIONS" ] || [ "$VIOLATIONS" = "0" ]; then
    echo "  Policy Violations: PASS (0 violations)"
  else
    echo "  Policy Violations: WARN ($VIOLATIONS violations)"
  fi

  echo ""
done

echo "========================================="
echo "  Guardrail Policy Summary"
echo "========================================="
kubectl get clusterpolicy -o custom-columns=NAME:.metadata.name,ACTION:.spec.validationFailureAction,READY:.status.ready
SCRIPT

chmod +x /tmp/audit-landing-zone.sh
bash /tmp/audit-landing-zone.sh
```

</details>

### Clean Up

```bash
kind delete cluster --name landing-zone-mgmt
rm /tmp/mgmt-cluster.yaml /tmp/vend-account.sh /tmp/audit-landing-zone.sh
```

### Success Criteria

- [ ] I created a management cluster with Kyverno guardrails installed
- [ ] I deployed three guardrail policies (team label, no privileged, resource limits)
- [ ] I built and ran an account vending script that provisions namespaces with full baseline
- [ ] I successfully vended accounts for two teams
- [ ] I verified that guardrails block non-compliant resources
- [ ] I generated a compliance audit report for all vended accounts
- [ ] I can explain the four pillars of an enterprise Landing Zone

---

## Next Module

With the Landing Zone foundation in place, it is time to go deeper into the policy layer. Head to [Module 10.2: Cloud Governance & Policy as Code](../module-10.2-governance/) to learn how AWS SCPs, Azure Policies, and GCP Organization Policies map to Kubernetes policy engines like Kyverno and OPA Gatekeeper, and how to build a unified governance model across cloud and cluster.

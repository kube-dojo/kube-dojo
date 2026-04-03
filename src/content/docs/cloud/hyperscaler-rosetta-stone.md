---
title: "The Hyperscaler Rosetta Stone"
sidebar:
  order: 2
---
**Complexity**: [MEDIUM]
**Time to Complete**: 2 hours
**Prerequisites**: Cloud Native 101 (containers, Docker basics)

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Compare equivalent services across AWS, GCP, and Azure for compute, storage, networking, and identity domains**
- **Diagnose multi-cloud migration failures caused by architectural differences (regional vs global VPCs, IAM models)**
- **Design multi-cloud architectures that account for fundamental structural differences between hyperscalers**
- **Evaluate cloud provider tradeoffs for specific workload patterns using the service mapping framework**

---

## Why This Module Matters

In late 2022, a rapidly scaling fintech enterprise decided to adopt a multi-cloud strategy to mitigate vendor lock-in and satisfy regulatory compliance requirements. Their primary infrastructure, built over six years, was heavily entrenched in Amazon Web Services (AWS). They utilized IAM roles, complex regional VPC peering, and an extensive array of ECS services. When the engineering leadership mandated a complete replication of their core transaction processing pipeline in Google Cloud Platform (GCP) and Microsoft Azure, the architecture team assumed the migration would be straightforward. They reasoned that a virtual machine is just a virtual machine, a network is just a network, and a database is just a database.

This assumption led to a catastrophic six-month delay, millions in burned runway, and an architectural disaster that required a complete teardown. The team attempted to map AWS's regional VPC model directly to GCP's global VPC architecture, resulting in overlapping subnets, complex routing nightmares, and severe performance bottlenecks. They misunderstood how GCP Service Accounts differ from AWS IAM Roles, leading to a sprawling mess of long-lived, hardcoded keys exported across environments, which ultimately triggered a severe security audit failure. In Azure, they attempted to implement resource grouping exactly like AWS tags, ignoring Azure's native Resource Group hierarchy, which broke their entire automated deployment pipeline and cost-tracking dashboards.

The fundamental disconnect was not a lack of technical skill. These were senior engineers. The failure stemmed from a lack of fluency in the specific dialects of the hyperscalers. They were trying to speak French using Spanish grammar rules.

Understanding the translation layer between Amazon Web Services (AWS), Google Cloud Platform (GCP), and Microsoft Azure is not merely about memorizing a glossary of marketing terms. It is about understanding the underlying philosophical differences in how these platforms were designed, how their networks route packets, and how their security perimeters are defined. By learning this "Rosetta Stone" of cloud computing, engineers can seamlessly transition between environments, design robust multi-cloud architectures without falling into conceptual traps, and accurately evaluate the true cost and operational burden of migrating workloads. You will learn to map not just the services, but the structural paradigms that govern them. This module provides that translation layer.

---

## 1. Identity and Access Management: The Rosetta Stone of Security

When you strip away the branding, every cloud provider offers the same basic building blocks: a way to run code, a way to grant permissions, and a way to group resources. However, the implementation of Identity and Access Management (IAM) varies wildly and is the source of the most dangerous migration errors.

### The Core Philosophies

Think of cloud providers like different operating systems. AWS is highly granular, demanding explicit permissions for every single action, and relies heavily on assuming temporary roles. GCP relies on a more cohesive, project-based structure where identities are treated as resources themselves. Azure is deeply integrated with enterprise identity (Microsoft Entra ID, formerly Azure AD) and relies on a strict hierarchical management model.

```text
Identity Model Comparison

AWS                          GCP                          Azure
┌──────────────────┐         ┌──────────────────┐         ┌──────────────────┐
│   AWS Account    │         │  GCP Organization│         │  Entra ID Tenant │
│   (root user)    │         │                  │         │  (Azure AD)      │
│  ┌────────────┐  │         │  ┌────────────┐  │         │  ┌────────────┐  │
│  │ IAM Users  │  │         │  │  Folders    │  │         │  │ Management │  │
│  │ IAM Groups │  │         │  │  (optional) │  │         │  │  Groups    │  │
│  │ IAM Roles  │  │         │  │            │  │         │  │            │  │
│  └────────────┘  │         │  └──────┬─────┘  │         │  └──────┬─────┘  │
│        │         │         │         │        │         │         │        │
│  ┌─────▼──────┐  │         │  ┌──────▼─────┐  │         │  ┌──────▼─────┐  │
│  │  Policies  │  │         │  │  Projects  │  │         │  │Subscriptions│ │
│  │  (JSON)    │  │         │  │ (boundary) │  │         │  │            │  │
│  │  attached  │  │         │  │  roles     │  │         │  │  ┌────────┐│  │
│  │  to role   │  │         │  │  bound at  │  │         │  │  │Resource││  │
│  └────────────┘  │         │  │  this level│  │         │  │  │ Groups ││  │
│                  │         │  └────────────┘  │         │  │  └────────┘│  │
│  Key concept:    │         │  Key concept:    │         │  │  RBAC at   │  │
│  "Assume Role"   │         │  "Bind Role to   │         │  │  any scope │  │
│  via STS tokens  │         │   identity at    │         │  └────────────┘  │
│                  │         │   resource"      │         │  Key concept:    │
│                  │         │                  │         │  "Managed        │
│                  │         │                  │         │   Identities"    │
└──────────────────┘         └──────────────────┘         └──────────────────┘
```

**AWS Identity Philosophy**
AWS uses a default-deny model. You create Users, Groups, and Roles. The most critical concept is the **IAM Role**. A role is not a user; it is an identity that can be assumed by anyone (or any service) that has permission to do so. Permissions are attached via JSON policies.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::my-company-data-bucket/*"
    }
  ]
}
```

```bash
# Create an IAM role for an EC2 instance
aws iam create-role \
    --role-name my-app-role \
    --assume-role-policy-document file://trust-policy.json

# Attach a managed policy
aws iam attach-role-policy \
    --role-name my-app-role \
    --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess

# Create an instance profile and add the role
aws iam create-instance-profile --instance-profile-name my-app-profile
aws iam add-role-to-instance-profile \
    --instance-profile-name my-app-profile \
    --role-name my-app-role
```

**GCP Identity Philosophy**
GCP uses Google Accounts (for humans) and **Service Accounts** (for machines). A Service Account acts more like a dedicated machine user. It has its own email address (e.g., `my-app@my-project.iam.gserviceaccount.com`). Instead of attaching policies to the identity, you bind roles (collections of permissions) to identities at a specific resource level (Project, Folder, or Organization).

```bash
# Create a service account
gcloud iam service-accounts create my-app-sa \
    --display-name="My Application Service Account"

# Granting a role to a service account on a specific project
gcloud projects add-iam-policy-binding my-gcp-project-id \
    --member="serviceAccount:my-app-sa@my-gcp-project-id.iam.gserviceaccount.com" \
    --role="roles/storage.objectViewer"

# Attach the service account to a Compute Engine instance (no keys needed!)
gcloud compute instances create my-vm \
    --service-account=my-app-sa@my-gcp-project-id.iam.gserviceaccount.com \
    --scopes=cloud-platform \
    --zone=us-central1-a
```

**Azure Identity Philosophy**
Azure relies on **Role-Based Access Control (RBAC)** backed by Entra ID. For applications, you use **Managed Identities**. A Managed Identity is an identity automatically managed in Entra ID and tightly coupled to an Azure resource (like a Virtual Machine). When the VM is deleted, the identity is deleted.

```bash
# Create a VM with a system-assigned managed identity
az vm create \
    --resource-group my-rg \
    --name my-vm \
    --image Ubuntu2204 \
    --assign-identity '[system]'

# Assigning a role to a managed identity for a storage account
az role assignment create \
    --assignee-object-id <managed-identity-object-id> \
    --role "Storage Blob Data Reader" \
    --scope /subscriptions/<sub-id>/resourceGroups/<rg-name>/providers/Microsoft.Storage/storageAccounts/<account-name>
```

### IAM Translation Table

| Concept | AWS | GCP | Azure |
| :--- | :--- | :--- | :--- |
| Human identity | IAM User | Google Account / Cloud Identity | Entra ID User |
| Machine identity | IAM Role (assumed) | Service Account | Managed Identity |
| Permission grouping | IAM Policy (JSON) | Role (predefined or custom) | Role Definition (RBAC) |
| Temporary credentials | STS AssumeRole | Service Account tokens (auto) | Managed Identity tokens (auto) |
| Federation | SAML / OIDC to IAM | Workload Identity Federation | Entra ID Federation |
| Resource boundary | Account | Project | Subscription |
| Organizational grouping | AWS Organizations + OUs | Organization + Folders | Management Groups |
| Cross-service auth | Instance Profiles | Attached Service Account | System-Assigned Identity |

### War Story: The Long-Lived Key Disaster

A DevOps team migrating an application from AWS to GCP needed their application to read from a cloud storage bucket. In AWS, they were accustomed to attaching an IAM Instance Profile to their EC2 instance. The EC2 instance magically received temporary credentials.

When moving to GCP, they couldn't find "Instance Profiles." Instead of reading the documentation on how to attach a GCP Service Account to a Compute Engine instance (which behaves similarly), they created a Service Account, generated a long-lived JSON key file, baked that key file into their Docker image, and deployed it. Three months later, a developer accidentally pushed that Dockerfile to a public repository. Because the key was long-lived and highly privileged, attackers immediately gained access to their entire GCP project.

The lesson: Always translate the *intent* of the security model, not just the mechanism. The intent was "temporary, instance-bound credentials." The translation from AWS IAM Instance Profile is a GCP Service Account attached to the VM, or an Azure System-Assigned Managed Identity.

---

## 2. The Network: Connecting the Pieces

Networking is where the most subtle and dangerous mistranslations occur. If you build a GCP network using AWS principles, you will create unnecessary complexity.

### The Virtual Private Cloud (VPC) Paradigms

The Virtual Private Cloud (VPC) is your isolated network boundary.

**AWS VPC: The Regional Fortress**
AWS VPCs are strictly **regional**. A VPC exists within one region (e.g., `us-east-1`). Subnets within that VPC are tied to specific Availability Zones (AZs). If you have a VPC in `us-east-1` and another VPC in `eu-west-1`, they are completely isolated. To connect them, you must configure VPC Peering or a Transit Gateway.

```text
+-------------------------------------------------------------+
| AWS Regional Architecture                                   |
|                                                             |
|  [VPC us-east-1 (10.0.0.0/16)]                              |
|   |-- [Subnet AZ-a (10.0.1.0/24)]                           |
|   |-- [Subnet AZ-b (10.0.2.0/24)]                           |
|                                                             |
|          ^                                                  |
|          | (Requires explicit Peering or Transit Gateway)   |
|          v                                                  |
|                                                             |
|  [VPC eu-west-1 (10.1.0.0/16)]                              |
|   |-- [Subnet AZ-a (10.1.1.0/24)]                           |
+-------------------------------------------------------------+
```

```bash
# Create a VPC in AWS
aws ec2 create-vpc --cidr-block 10.0.0.0/16 --region us-east-1

# Create subnets in specific AZs
aws ec2 create-subnet \
    --vpc-id vpc-abc123 \
    --cidr-block 10.0.1.0/24 \
    --availability-zone us-east-1a

aws ec2 create-subnet \
    --vpc-id vpc-abc123 \
    --cidr-block 10.0.2.0/24 \
    --availability-zone us-east-1b

# Peer two VPCs (even in the same region, it's explicit)
aws ec2 create-vpc-peering-connection \
    --vpc-id vpc-abc123 \
    --peer-vpc-id vpc-def456 \
    --peer-region eu-west-1
```

**GCP VPC: The Global Backbone**
GCP VPCs are inherently **global**. A single VPC can span all regions worldwide. Subnets are regional. This means a Virtual Machine in Tokyo can communicate with a Virtual Machine in London using their internal, private IP addresses over Google's private fiber network, without you configuring any peering or VPNs.

```text
+-------------------------------------------------------------+
| GCP Global Architecture                                     |
|                                                             |
|  [Global VPC (default)]                                     |
|   |                                                         |
|   |-- [Subnet us-central1 (10.128.0.0/20)]                  |
|   |      (VM A: 10.128.0.2)                                 |
|   |                                                         |
|   |-- [Subnet europe-west1 (10.132.0.0/20)]                 |
|          (VM B: 10.132.0.2)                                 |
|                                                             |
|  * VM A and VM B route directly to each other internally.   |
+-------------------------------------------------------------+
```

```bash
# Create a custom VPC (it's automatically global)
gcloud compute networks create my-vpc --subnet-mode=custom

# Create subnets in different regions — same VPC
gcloud compute networks subnets create us-subnet \
    --network=my-vpc \
    --region=us-central1 \
    --range=10.0.1.0/24

gcloud compute networks subnets create eu-subnet \
    --network=my-vpc \
    --region=europe-west1 \
    --range=10.0.2.0/24

# No peering needed! VMs in us-subnet and eu-subnet
# can talk to each other over private IPs immediately.
```

**Azure VNet: The Regional Network**
Azure Virtual Networks (VNets) are, like AWS, **regional**. Subnets are not tied to specific Availability Zones by default (though resources inside them can be). Connecting VNets requires VNet Peering.

```bash
# Create a VNet in Azure
az network vnet create \
    --resource-group my-rg \
    --name my-vnet \
    --address-prefix 10.0.0.0/16 \
    --location eastus

# Create subnets (not AZ-specific by default)
az network vnet subnet create \
    --resource-group my-rg \
    --vnet-name my-vnet \
    --name web-subnet \
    --address-prefixes 10.0.1.0/24

# Peer two VNets
az network vnet peering create \
    --resource-group my-rg \
    --name vnet1-to-vnet2 \
    --vnet-name my-vnet \
    --remote-vnet /subscriptions/<sub>/resourceGroups/rg2/providers/Microsoft.Network/virtualNetworks/vnet2 \
    --allow-vnet-access
```

### Networking Quick-Reference Table

| Concept | AWS | GCP | Azure |
| :--- | :--- | :--- | :--- |
| Private network | VPC (regional) | VPC (global) | VNet (regional) |
| Subnet scope | Per Availability Zone | Per Region | Per VNet (not AZ-bound) |
| Cross-region private | VPC Peering / Transit GW | Automatic (same VPC) | VNet Peering / vWAN |
| Firewall rules | Security Groups + NACLs | Firewall Rules (on VPC) | NSGs + Azure Firewall |
| Private DNS | Route 53 Private Zones | Cloud DNS Private Zones | Azure Private DNS |
| VPN gateway | VPN Gateway | Cloud VPN | VPN Gateway |
| Direct connect | Direct Connect | Cloud Interconnect | ExpressRoute |

### Traffic Management and Load Balancing

Routing user traffic from the public internet into your private network relies on managed DNS and load balancers.

*   **AWS**: Route 53 is the DNS service. For layer 7 (HTTP/HTTPS) traffic, you use an Application Load Balancer (ALB). ALBs are regional. To achieve global load balancing, you must use Route 53 latency-based routing or AWS Global Accelerator.
*   **GCP**: Cloud DNS manages records. GCP's Cloud Load Balancing is a massive differentiator because it is a global Anycast IP by default. A single IP address routes users to the closest healthy region.
*   **Azure**: Azure DNS manages records. Azure Application Gateway provides regional layer 7 load balancing. Azure Front Door provides global load balancing and CDN capabilities.

| Load Balancing Feature | AWS | GCP | Azure |
| :--- | :--- | :--- | :--- |
| Regional L7 (HTTP) | ALB | Regional HTTP(S) LB | Application Gateway |
| Global L7 (HTTP) | CloudFront + ALB | Global HTTP(S) LB | Front Door |
| Regional L4 (TCP/UDP) | NLB | Regional TCP/UDP LB | Load Balancer (Standard) |
| Global L4 (TCP/UDP) | Global Accelerator | Global TCP Proxy LB | Front Door / Traffic Manager |
| DNS-based routing | Route 53 | Cloud DNS (limited) | Traffic Manager |
| CDN | CloudFront | Cloud CDN | Azure CDN / Front Door |
| Single global IP? | No (multi-region = multi-IP) | Yes (Anycast) | Yes (Front Door) |

---

## 3. Compute Primitives: From Bare Metal to Auto Scaling

Before containers took over the world, virtual machines were the bedrock of cloud computing. Understanding the raw compute translation is essential for legacy workloads and stateful systems.

### Virtual Machines

The naming conventions are straightforward:
*   **AWS**: Elastic Compute Cloud (EC2)
*   **GCP**: Google Compute Engine (GCE)
*   **Azure**: Azure Virtual Machines

However, the lifecycle and management differ. AWS heavily utilizes AMI (Amazon Machine Images) which are regional. If you build an AMI in `us-east-1`, you must explicitly copy it to `us-west-2` to launch instances there. GCP Custom Images are global resources; an image built in one region is immediately accessible everywhere.

```bash
# AWS: Launch an EC2 instance
aws ec2 run-instances \
    --image-id ami-0abcdef1234567890 \
    --instance-type t3.medium \
    --key-name my-key \
    --subnet-id subnet-abc123 \
    --security-group-ids sg-abc123

# GCP: Launch a Compute Engine instance
gcloud compute instances create my-vm \
    --machine-type=e2-medium \
    --zone=us-central1-a \
    --image-family=debian-12 \
    --image-project=debian-cloud

# Azure: Launch a Virtual Machine
az vm create \
    --resource-group my-rg \
    --name my-vm \
    --image Ubuntu2204 \
    --size Standard_B2s \
    --admin-username azureuser \
    --generate-ssh-keys
```

### Instance Type Naming: The Hidden Complexity

Every cloud has its own naming convention for machine sizes. Understanding the patterns saves enormous time.

| AWS (example) | GCP (example) | Azure (example) | Rough Equivalent |
| :--- | :--- | :--- | :--- |
| `t3.micro` | `e2-micro` | `Standard_B1s` | Burstable, 1 vCPU, ~1 GB |
| `t3.medium` | `e2-medium` | `Standard_B2s` | Burstable, 2 vCPU, ~4 GB |
| `m5.xlarge` | `n2-standard-4` | `Standard_D4s_v5` | General purpose, 4 vCPU, ~16 GB |
| `c5.2xlarge` | `c2-standard-8` | `Standard_F8s_v2` | Compute-optimized, 8 vCPU |
| `r5.large` | `n2-highmem-2` | `Standard_E2s_v5` | Memory-optimized, 2 vCPU |
| `p3.2xlarge` | `a2-highgpu-1g` | `Standard_NC6s_v3` | GPU instance, 1 GPU |

### Auto Scaling and Instance Groups

When building resilient architectures, you never run a single VM. You run groups of VMs that automatically scale out under load and self-heal when instances fail.

*   **AWS: Auto Scaling Groups (ASG)**. You define a Launch Template (specifying the AMI, instance type, and IAM role) and create an ASG that spans multiple AZs within a region.
*   **GCP: Managed Instance Groups (MIG)**. You define an Instance Template. MIGs can be Zonal (single zone) or Regional (spanning multiple zones).
*   **Azure: Virtual Machine Scale Sets (VMSS)**. Similar to ASGs, VMSS allows you to create and manage a group of identical, load-balanced VMs.

### War Story: The Unhealthy Health Check

An engineering group translated an AWS architecture to Azure. In AWS, their ALB checked the health of their EC2 instances using an HTTP endpoint (`/healthz`). If the instance failed, the ASG terminated it and spun up a new one.

In Azure, they configured an Azure Load Balancer and a VMSS. They configured the load balancer health probe to hit `/healthz`. The load balancer correctly stopped sending traffic to unhealthy nodes. However, the VMs were never replaced. They had failed to realize that in Azure, the load balancer health probe only controls traffic routing. To achieve auto-healing (terminating and replacing the VM), they needed to configure an *Application Health Extension* directly on the VMSS. They assumed the load balancer governed the VM lifecycle, an AWS-centric assumption that caused a massive production outage during a traffic spike.

---

## 4. The Container Ecosystem: Standalone, Managed K8s, and Serverless

Modern applications rarely run on bare virtual machines. They run in containers or as serverless functions. The hyperscalers offer multiple abstraction layers for these workloads.

### Standalone Containers (Containers as a Service)

When you have a Docker image and simply want it to run without managing underlying virtual machines or complex orchestration platforms like Kubernetes:

*   **AWS: ECS with Fargate**. Elastic Container Service (ECS) is Amazon's proprietary container orchestrator. Fargate is the serverless compute engine for containers. You define a Task Definition, point it to an image, and AWS provisions the compute on the fly.
*   **GCP: Cloud Run**. Cloud Run is built on Knative. It allows you to run stateless HTTP containers. Its massive advantage is the ability to scale to absolute zero when there is no traffic, costing you nothing.
*   **Azure: Azure Container Instances (ACI) or Azure Container Apps**. ACI is for simple, single-container deployments. Azure Container Apps is a more robust, serverless environment optimized for microservices and built on top of Kubernetes and KEDA (Kubernetes Event-driven Autoscaling).

```bash
# AWS: Deploy a container to ECS Fargate (simplified)
aws ecs create-service \
    --cluster my-cluster \
    --service-name my-service \
    --task-definition my-task:1 \
    --desired-count 2 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-abc],securityGroups=[sg-abc]}"

# GCP: Deploy a container to Cloud Run (one command!)
gcloud run deploy my-service \
    --image=gcr.io/my-project/my-app:latest \
    --platform=managed \
    --region=us-central1 \
    --allow-unauthenticated

# Azure: Deploy a container to Azure Container Apps
az containerapp create \
    --name my-app \
    --resource-group my-rg \
    --environment my-env \
    --image myregistry.azurecr.io/my-app:latest \
    --target-port 8080 \
    --ingress external
```

### Serverless Container Comparison

| Feature | AWS ECS Fargate | GCP Cloud Run | Azure Container Apps |
| :--- | :--- | :--- | :--- |
| Scale to zero | No (minimum 1 task) | Yes | Yes |
| Max request timeout | No limit (long-running) | 60 min (HTTP) | 30 min |
| GPU support | Yes | Yes | Yes |
| Built on | Proprietary (ECS) | Knative | Kubernetes + KEDA |
| Min billing unit | 1 second | 100ms | 1 second |
| Max vCPU per instance | 16 | 8 | 4 |
| Max memory per instance | 120 GB | 32 GB | 16 GB |
| VPC integration | Native | VPC Connector | VNet integration |
| Sidecar containers | Yes | Yes | Yes |

### Managed Kubernetes: The Great Equalizer

Kubernetes is the great equalizer of the cloud. The API is standard; a Kubernetes Deployment manifest looks exactly the same whether it runs on Amazon, Google, or Microsoft. However, the managed services wrap the control plane differently.

Always ensure your clusters are running modern, supported versions (e.g., Kubernetes 1.35+) to leverage the latest Gateway API, improved resource management, and security patches. You will typically interact with all three using `kubectl` (often aliased as `k`).

```text
Managed Kubernetes Architecture Comparison

AWS EKS                      GCP GKE                      Azure AKS
┌──────────────────┐         ┌──────────────────┐         ┌──────────────────┐
│  Control Plane   │         │  Control Plane   │         │  Control Plane   │
│  (AWS-managed)   │         │  (Google-managed) │         │  (Azure-managed) │
│  ┌────────────┐  │         │  ┌────────────┐  │         │  ┌────────────┐  │
│  │ API Server │  │         │  │ API Server │  │         │  │ API Server │  │
│  │ etcd       │  │         │  │ etcd       │  │         │  │ etcd       │  │
│  │ scheduler  │  │         │  │ scheduler  │  │         │  │ scheduler  │  │
│  │ controller │  │         │  │ controller │  │         │  │ controller │  │
│  └────────────┘  │         │  └────────────┘  │         │  └────────────┘  │
│  Cost: ~$73/mo   │         │  Cost: $0 (std)  │         │  Cost: $0 (free) │
│                  │         │  $73/mo (autoplt) │         │  $73/mo (std)    │
└────────┬─────────┘         └────────┬─────────┘         └────────┬─────────┘
         │                            │                            │
┌────────▼─────────┐         ┌────────▼─────────┐         ┌────────▼─────────┐
│  Worker Nodes    │         │  Worker Nodes    │         │  Worker Nodes    │
│  ┌────────────┐  │         │  ┌────────────┐  │         │  ┌────────────┐  │
│  │ Managed    │  │         │  │ Standard:  │  │         │  │ Node Pools │  │
│  │ Node Groups│  │         │  │  Node Pools│  │         │  │ (VMSS-     │  │
│  │ (EC2-based)│  │         │  │ Autopilot: │  │         │  │  backed)   │  │
│  │            │  │         │  │  No nodes  │  │         │  │            │  │
│  │ YOU manage │  │         │  │  to manage │  │         │  │ YOU manage │  │
│  └────────────┘  │         │  └────────────┘  │         │  └────────────┘  │
│                  │         │                  │         │                  │
│  CNI: VPC CNI    │         │  CNI: Dataplane  │         │  CNI: Azure CNI  │
│  (pod = VPC IP)  │         │  V2 (Cilium/eBPF)│         │  or CNI Overlay  │
│                  │         │                  │         │                  │
│  Auth: IAM +     │         │  Auth: Google    │         │  Auth: Entra ID  │
│  OIDC (complex)  │         │  IAM (native)    │         │  + Azure RBAC    │
└──────────────────┘         └──────────────────┘         └──────────────────┘
```

*   **AWS EKS (Elastic Kubernetes Service)**: Highly configurable but requires the most operational overhead. You are responsible for managing node groups, upgrading core add-ons (like the CNI and CoreDNS), and managing the complex integration between AWS IAM and Kubernetes RBAC (via OIDC). It is the "Linux" of managed K8s.
*   **GCP GKE (Google Kubernetes Engine)**: Widely considered the gold standard. Google invented Kubernetes, and GKE is deeply integrated. GKE Autopilot takes this a step further by managing the entire underlying infrastructure, including the nodes; you only pay for the pod resource requests.
*   **Azure AKS (Azure Kubernetes Service)**: Offers deep integration with Azure Active Directory (Entra ID) and developer tooling. It provides fast cluster creation and robust integration with Azure's networking stack.

```bash
# AWS: Create an EKS cluster
eksctl create cluster \
    --name my-cluster \
    --region us-east-1 \
    --version 1.35 \
    --nodegroup-name workers \
    --node-type t3.medium \
    --nodes 3

# GCP: Create a GKE Autopilot cluster
gcloud container clusters create-auto my-cluster \
    --region=us-central1 \
    --cluster-version=1.35

# Azure: Create an AKS cluster
az aks create \
    --resource-group my-rg \
    --name my-cluster \
    --kubernetes-version 1.35 \
    --node-count 3 \
    --node-vm-size Standard_B2s \
    --generate-ssh-keys
```

```yaml
# A standard Kubernetes Deployment is the ultimate Rosetta Stone.
# This exact manifest works seamlessly across EKS, GKE, and AKS.
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rosetta-frontend
  labels:
    app: frontend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: web
        image: nginx:1.25-alpine
        ports:
        - containerPort: 80
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 250m
            memory: 256Mi
```

### Managed Kubernetes Comparison

| Feature | AWS EKS | GCP GKE | Azure AKS |
| :--- | :--- | :--- | :--- |
| Control plane cost | ~$73/month | Free (Standard), ~$73 (Autopilot/Enterprise) | Free (Free tier), ~$73 (Standard) |
| Serverless nodes | Fargate profiles | Autopilot (fully managed) | Virtual Nodes (ACI-backed) |
| Default CNI | VPC CNI (VPC IPs to pods) | Dataplane V2 (Cilium/eBPF) | Azure CNI / CNI Overlay |
| Node auto-provisioning | Karpenter | Autopilot / NAP | Karpenter (preview) |
| Max nodes per cluster | 5,000 | 15,000 | 5,000 |
| Cluster creation time | ~15 minutes | ~5 minutes (Autopilot) | ~8 minutes |
| Built-in service mesh | App Mesh (deprecated) | Istio (managed) | Istio (managed) |
| Windows node support | Yes | Yes | Yes |
| GPU support | Yes | Yes (with drivers) | Yes |
| Multi-cluster management | None (use Argo/Flux) | Fleet (multi-cluster) | Azure Arc |

### Serverless Functions

For event-driven, short-lived code that executes in response to triggers (like a file uploaded to storage, or an HTTP request):

*   **AWS: AWS Lambda**. The pioneer of serverless. Supports multiple languages, integrates deeply with SQS, SNS, and API Gateway.
*   **GCP: Cloud Functions**. Excellent for lightweight data processing and webhook integrations.
*   **Azure: Azure Functions**. Unique in its use of "bindings," which declaratively connect functions to other Azure services (like CosmosDB or Service Bus) without writing boilerplate connection code.

### Serverless Functions Comparison

| Feature | AWS Lambda | GCP Cloud Functions | Azure Functions |
| :--- | :--- | :--- | :--- |
| Max execution time | 15 minutes | 60 minutes (2nd gen) | 10 min (Consumption), unlimited (Dedicated) |
| Max memory | 10 GB | 32 GB (2nd gen) | 14 GB (Premium) |
| Languages | Node, Python, Java, Go, .NET, Ruby, custom | Node, Python, Java, Go, .NET, Ruby, PHP | Node, Python, Java, C#, F#, PowerShell, custom |
| Cold start | ~100-500ms | ~100-500ms | ~200ms-2s (Consumption) |
| Provisioned concurrency | Yes | Yes (min instances) | Yes (Premium plan) |
| Container image support | Yes | Yes (2nd gen) | Yes |
| Event sources | 200+ AWS integrations | Eventarc + Pub/Sub | Event Grid + Service Bus |
| Unique feature | Layers, Extensions | Built on Cloud Run | Durable Functions (stateful workflows) |
| Free tier | 1M requests/month | 2M invocations/month | 1M executions/month |

---

## 5. Storage, Databases, and Observability

You cannot operate an application if you cannot store its state, manage its data, and monitor its health.

### Storage Paradigms

Object storage is the foundation of cloud data lakes, backups, and static assets.
*   **AWS: Amazon S3 (Simple Storage Service)**. The industry standard. Uses buckets.
*   **GCP: Cloud Storage (GCS)**. Functionally identical to S3, uses buckets, offers strong consistency globally.
*   **Azure: Azure Blob Storage**. Exists within an Azure Storage Account. You create containers, and inside containers, you store blobs.

```bash
# AWS: Upload a file to S3
aws s3 cp my-file.tar.gz s3://my-bucket/backups/

# GCP: Upload a file to Cloud Storage
gcloud storage cp my-file.tar.gz gs://my-bucket/backups/

# Azure: Upload a file to Blob Storage
az storage blob upload \
    --account-name mystorageaccount \
    --container-name backups \
    --file my-file.tar.gz \
    --name my-file.tar.gz
```

### Storage Tiers Comparison

Every provider offers tiered storage classes to optimize cost. The concept is the same: hot data (accessed frequently) costs more per GB but less to retrieve, cold data costs less per GB but more to retrieve.

| Access Pattern | AWS S3 | GCP Cloud Storage | Azure Blob Storage |
| :--- | :--- | :--- | :--- |
| Frequently accessed | S3 Standard | Standard | Hot |
| Infrequent access | S3 Standard-IA | Nearline (30-day min) | Cool (30-day min) |
| Archival | S3 Glacier Instant Retrieval | Coldline (90-day min) | Cold (90-day min) |
| Deep archive | S3 Glacier Deep Archive | Archive (365-day min) | Archive (180-day min) |
| Intelligent tiering | S3 Intelligent-Tiering | Autoclass | Access tier change (manual/policy) |
| ~Cost per GB/month (hot) | $0.023 | $0.020 | $0.018 |
| ~Cost per GB/month (cold) | $0.004 (Glacier IR) | $0.004 (Coldline) | $0.002 (Cold) |
| Minimum storage duration | None (Standard) | None (Standard) | None (Hot) |

Block storage provides attached disks for virtual machines.
*   **AWS**: Elastic Block Store (EBS).
*   **GCP**: Persistent Disk (PD).
*   **Azure**: Managed Disks.

### Relational Databases

Managed PostgreSQL and MySQL are available everywhere.
*   **AWS**: Amazon RDS (Relational Database Service) or Amazon Aurora (a highly scalable, proprietary database engine compatible with MySQL/PostgreSQL).
*   **GCP**: Cloud SQL or Cloud Spanner (a globally distributed, strongly consistent relational database).
*   **Azure**: Azure Database for PostgreSQL / MySQL.

### Database Service Translation Table

| Database Type | AWS | GCP | Azure |
| :--- | :--- | :--- | :--- |
| Managed PostgreSQL/MySQL | RDS | Cloud SQL | Database for PostgreSQL/MySQL |
| High-perf relational | Aurora | AlloyDB | Hyperscale (Citus) |
| Global relational | Aurora Global DB | Cloud Spanner | Cosmos DB (relational API) |
| Key-value / NoSQL | DynamoDB | Firestore / Bigtable | Cosmos DB |
| In-memory cache | ElastiCache (Redis) | Memorystore | Azure Cache for Redis |
| Document database | DocumentDB | Firestore | Cosmos DB (MongoDB API) |
| Data warehouse | Redshift | BigQuery | Synapse Analytics |
| Search | OpenSearch Service | (Elastic on GCP) | Azure AI Search |

### Observability and Telemetry

Understanding system behavior requires unified logging and metrics.

*   **AWS**: Amazon CloudWatch. You use CloudWatch Metrics for performance data and CloudWatch Logs for application output. It can feel fragmented, often requiring additional services like X-Ray for distributed tracing.
*   **GCP**: Cloud Operations (formerly Stackdriver). Highly unified. Logs, metrics, and distributed tracing are tightly integrated into a single pane of glass.
*   **Azure**: Azure Monitor. Provides comprehensive metrics. Application Insights is an exceptionally powerful tool within Azure Monitor specifically designed for deep, code-level application performance monitoring and tracing.

| Observability Pillar | AWS | GCP | Azure |
| :--- | :--- | :--- | :--- |
| Metrics | CloudWatch Metrics | Cloud Monitoring | Azure Monitor Metrics |
| Logs | CloudWatch Logs | Cloud Logging | Log Analytics |
| Tracing | X-Ray | Cloud Trace | Application Insights |
| Dashboards | CloudWatch Dashboards | Cloud Monitoring Dashboards | Azure Dashboards / Grafana |
| Alerting | CloudWatch Alarms + SNS | Cloud Alerting | Azure Monitor Alerts |
| APM | X-Ray + CloudWatch | Cloud Profiler + Trace | Application Insights |
| Unified experience? | No (fragmented) | Yes (Cloud Operations suite) | Mostly (Monitor as hub) |

---

## 6. CI/CD: Building and Deploying Across Clouds

Every hyperscaler has a native CI/CD offering. These range from tightly integrated but opinionated (Azure DevOps) to minimal and composable (GCP Cloud Build). Understanding the native tools matters even if you ultimately standardize on GitHub Actions or GitLab CI, because native integrations with IAM, artifact registries, and deployment targets are always tighter.

### CI/CD Service Mapping

| CI/CD Capability | AWS | GCP | Azure |
| :--- | :--- | :--- | :--- |
| Source control | CodeCommit (deprecated) | Cloud Source Repos (deprecated) | Azure Repos |
| Build service | CodeBuild | Cloud Build | Azure Pipelines |
| Pipeline orchestration | CodePipeline | Cloud Build (triggers + steps) | Azure Pipelines (multi-stage) |
| Artifact registry | ECR (containers), CodeArtifact (packages) | Artifact Registry | Azure Container Registry, Azure Artifacts |
| Deployment service | CodeDeploy | Cloud Deploy | Azure Pipelines (release) |
| IaC deployment | CloudFormation | Deployment Manager (deprecated) / Terraform | ARM Templates / Bicep |

### The Philosophical Difference

**AWS CodePipeline** is a stage-based orchestrator. You define Source, Build, Test, and Deploy stages. Each stage contains actions backed by CodeBuild, CodeDeploy, or Lambda. It is rigid but predictable.

**GCP Cloud Build** is a step-based builder. You write a `cloudbuild.yaml` with sequential steps, each running in a container. It is flexible and feels more like a Makefile than a pipeline product. Google has largely moved toward standardizing on Cloud Deploy for the deployment phase.

**Azure DevOps Pipelines** is the most complete offering. It includes boards (project management), repos (Git), pipelines (CI/CD), test plans, and artifacts all in one product. Multi-stage YAML pipelines can model complex release workflows with approvals, environments, and deployment strategies (canary, blue-green) natively.

```yaml
# AWS CodeBuild buildspec.yml
version: 0.2
phases:
  install:
    commands:
      - echo Installing dependencies...
  build:
    commands:
      - echo Building the app...
      - docker build -t my-app .
  post_build:
    commands:
      - docker push $ECR_REPO:$CODEBUILD_RESOLVED_SOURCE_VERSION
```

```yaml
# GCP Cloud Build cloudbuild.yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'us-central1-docker.pkg.dev/$PROJECT_ID/my-repo/my-app:$COMMIT_SHA', '.']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'us-central1-docker.pkg.dev/$PROJECT_ID/my-repo/my-app:$COMMIT_SHA']
images:
  - 'us-central1-docker.pkg.dev/$PROJECT_ID/my-repo/my-app:$COMMIT_SHA'
```

```yaml
# Azure Pipelines azure-pipelines.yml
trigger:
  - main
pool:
  vmImage: 'ubuntu-latest'
steps:
  - task: Docker@2
    inputs:
      command: buildAndPush
      repository: my-app
      containerRegistry: myACRConnection
      tags: $(Build.SourceVersion)
```

---

## 7. Infrastructure as Code: Native Tools

While Terraform and OpenTofu are the cross-cloud standard (covered in our IaC track), each provider has a native IaC tool. Understanding them matters because you will encounter them in existing codebases.

| Characteristic | AWS CloudFormation | GCP Deployment Manager | Azure ARM / Bicep |
| :--- | :--- | :--- | :--- |
| Language | JSON or YAML | YAML + Jinja2/Python | JSON (ARM) or Bicep (DSL) |
| State management | AWS-managed (stack state) | GCP-managed | Azure-managed |
| Rollback on failure | Automatic | Manual | Automatic |
| Preview changes | Change Sets | Preview | What-if |
| Multi-region | StackSets | Manual | Deployment Stacks |
| Community adoption | High (legacy) | Low (deprecated) | Growing (Bicep) |
| Recommendation | Use for AWS-only shops | Use Terraform/OpenTofu | Use Bicep for Azure-only |

The most important thing to understand: **GCP Deployment Manager is effectively deprecated** in favor of Terraform. Google actively recommends Terraform and even provides official modules. AWS CloudFormation remains a first-class citizen but is AWS-only. Azure Bicep is actively developed and provides a modern, readable alternative to ARM templates, but Terraform remains the multi-cloud standard.

---

## 8. Pricing Models: The Most Dangerous Translation

The most expensive multi-cloud mistake is not technical, it is financial. Each provider offers discount mechanisms that do not translate 1:1, and the billing models have subtle differences that compound at scale.

### On-Demand Pricing (Pay-as-you-go)

All three providers charge per second (or per hour, depending on the service) for on-demand compute. The prices for similar instance types are remarkably close, but not identical.

| Instance (~4 vCPU, 16 GB) | AWS | GCP | Azure |
| :--- | :--- | :--- | :--- |
| Instance type name | m5.xlarge | n2-standard-4 | Standard_D4s_v5 |
| On-demand (US, Linux, /hr) | ~$0.192 | ~$0.194 | ~$0.192 |
| Monthly (730 hrs) | ~$140 | ~$142 | ~$140 |

The per-hour costs are nearly identical. The real differences emerge in discount mechanisms and data transfer.

### Discount Mechanisms

| Discount Type | AWS | GCP | Azure |
| :--- | :--- | :--- | :--- |
| Commitment (1-3 yr) | Reserved Instances / Savings Plans | Committed Use Discounts (CUDs) | Reserved VM Instances |
| Typical 1-year savings | 30-40% | 28-37% | 30-40% |
| Typical 3-year savings | 50-60% | 52-57% | 55-65% |
| Automatic discounts | None | Sustained Use Discounts (up to 30%) | None |
| Preemptible / Spot | Spot Instances (up to 90% off) | Spot VMs (up to 91% off) | Spot VMs (up to 90% off) |
| Spot termination notice | 2 minutes | 30 seconds | 30 seconds |
| Free tier | 750 hrs/mo t2.micro (12 mo) | e2-micro always-free | 750 hrs/mo B1s (12 mo) |

### The GCP Sustained Use Discount Advantage

GCP is unique in offering **Sustained Use Discounts (SUDs)** automatically. If you run an instance for more than 25% of a month, GCP starts discounting. By the end of a full month, you receive up to a 30% discount without any commitment. AWS and Azure offer nothing comparable; you must actively purchase Reserved Instances or Savings Plans to get discounts.

### Data Egress: The Hidden Cost

Data transfer between clouds and to the internet is where bills explode. This is the single most important pricing concept for multi-cloud architectures.

| Transfer Type | AWS | GCP | Azure |
| :--- | :--- | :--- | :--- |
| Ingress (data in) | Free | Free | Free |
| Same-zone traffic | Free | Free | Free |
| Cross-zone (same region) | ~$0.01/GB | Free | Free |
| Cross-region (same provider) | $0.01-0.02/GB | $0.01-0.08/GB | $0.02-0.05/GB |
| Egress to internet (first 10 TB) | ~$0.09/GB | ~$0.12/GB | ~$0.087/GB |

The critical difference: **AWS charges for cross-AZ traffic** within the same region. If your microservices are spread across AZs for high availability (which they should be), every cross-AZ API call costs money. GCP and Azure do not charge for cross-zone traffic.

---

## Did You Know?

1.  Google Cloud's global network handles a significant percentage of all global internet traffic before it ever hits the public internet. This is because their global VPC utilizes the same private, physical fiber-optic backbone that serves YouTube and Google Search worldwide.
2.  AWS S3 was launched in 2006 with a simple SOAP and REST interface as one of the very first public cloud services. It has scaled astronomically and now holds over one hundred trillion individual objects, routinely peaking at tens of millions of requests per second globally.
3.  Azure Active Directory (now Entra ID) processes over thirty billion authentication requests every single day. Because it is deeply integrated with Microsoft 365 and Office deployments, it acts as the primary identity backbone for a vast majority of the Fortune 500.
4.  While Kubernetes is seen as a cloud-native standard, the underlying Container Network Interface (CNI) plugins provided by the hyperscalers completely change how your cluster behaves. The AWS VPC CNI assigns native VPC IP addresses to every pod, which can rapidly exhaust your subnet IPs, whereas GCP and Azure often use overlay networks by default to conserve address space.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
| :--- | :--- | :--- |
| **Applying AWS regional VPC logic to GCP** | Engineers assume VPCs must be explicitly peered across regions to communicate, leading to complex management. | Utilize GCP's global VPC by default. Place subnets in different regions within the exact same VPC for seamless, private connectivity. |
| **Misunderstanding IAM Roles vs Service Accounts** | Trying to attach a GCP Service Account to a resource exactly like an AWS IAM Role profile, or generating long-lived keys. | Treat GCP Service Accounts as resource identities. Use Workload Identity Federation for cross-platform access, and attach Service Accounts directly to VMs without exporting keys. |
| **Ignoring CNI differences in Managed K8s** | Assuming pod IP address exhaustion works exactly the same in EKS as it does in standard GKE. | The AWS EKS VPC CNI assigns native VPC IPs to individual pods. You must plan subnet CIDR blocks much larger in AWS than in GCP's default overlay network setup to avoid IP exhaustion. |
| **Blindly lifting and shifting CI/CD pipelines** | Translating AWS CodePipeline steps perfectly 1:1 to GitHub Actions or Azure DevOps without leveraging native features. | Redesign the pipeline around the target platform's strengths, such as utilizing Azure DevOps multi-stage release pipelines instead of rigid, single-path CodePipelines. |
| **Overlooking regional data egress costs** | Assuming data transfer between regions, or data out to the internet, costs the exact same everywhere. | Architect systems to keep high-bandwidth, chatty traffic within the exact same availability zone or region whenever possible, regardless of the cloud provider. |
| **Assuming 'Serverless' implies identical limits** | AWS Lambda has specific execution time maximums and payload limits that differ entirely from Azure Functions. | Rigorously validate payload sizes, maximum execution timeouts, and concurrent invocation limits when migrating serverless architectures. |
| **Translating AWS Tags directly to Azure Resource Groups** | AWS uses flat tags for everything. Azure relies on Resource Groups as mandatory deployment boundaries. | Do not use Azure Resource Groups just for tagging. Use them to group resources that share identical lifecycles, and use Azure Tags for billing categorizations. |
| **Ignoring cross-AZ data transfer costs on AWS** | On GCP and Azure, cross-zone traffic is free. Engineers assume the same on AWS and get surprised by bills. | On AWS, cross-AZ traffic costs ~$0.01/GB in each direction. Design services to prefer same-AZ communication for high-throughput internal calls, or accept the cost for HA. |

---

## Quiz

<details>
<summary>Question 1: If your application architecture relies heavily on cross-region private network communication, which cloud provider's default VPC design simplifies this the most?</summary>
Google Cloud Platform (GCP). GCP's VPCs are global resources by default, meaning subnets deployed in completely different regions can communicate privately over Google's backbone without requiring explicit peering connections or Transit Gateways, unlike AWS or Azure where VPCs and VNets are strictly regional constructs.
</details>

<details>
<summary>Question 2: You are migrating a stateless web application from AWS ECS Fargate. You want the absolute closest equivalent in Google Cloud that runs standard Docker containers and scales entirely to zero when there is no traffic. What service do you choose?</summary>
Cloud Run. While GKE is intended for full Kubernetes orchestration and cluster management, Cloud Run is GCP's serverless container platform. It allows you to run stateless HTTP-driven containers that automatically scale based on incoming requests and scale to zero, heavily mirroring the operational simplicity of Fargate for web workloads.
</details>

<details>
<summary>Question 3: In AWS, you assign permissions to an EC2 instance by attaching an IAM Role via an Instance Profile. How is the exact equivalent outcome achieved securely in GCP for a Compute Engine instance?</summary>
You attach a Service Account directly to the Compute Engine instance during creation. The virtual machine then authenticates to GCP APIs using the short-lived credentials of that specific Service Account, which acts as the trusted identity of the compute resource.
</details>

<details>
<summary>Question 4: True or False: AWS S3, GCP Cloud Storage, and Azure Blob Storage all offer a single, unified global endpoint for reading and writing data without specifying regions.</summary>
False. While they are all object storage services, the endpoint architecture varies. AWS S3 requires specifying regional endpoints for optimal routing and performance (though global endpoints exist, they are for specific routing rules), and data residency is strictly enforced at the bucket level within a specific geographic region.
</details>

<details>
<summary>Question 5: A company wants to run a managed Kubernetes cluster on version 1.35. They demand that the control plane be completely hidden, and crucially, that the worker nodes scale automatically without the engineering team managing underlying virtual machine scale sets. Which hyperscaler service mode fits this requirement perfectly?</summary>
GKE Autopilot. While standard GKE requires you to manage node pools (which utilize underlying Managed Instance Groups), GKE Autopilot completely abstracts the node infrastructure. You deploy your pods, and Google provisions the exact compute needed, charging you only for the pod resource requests rather than the entire virtual machine.
</details>

<details>
<summary>Question 6: What is the direct Microsoft Azure equivalent of AWS Auto Scaling Groups (ASG) for managing fleets of virtual machines?</summary>
Virtual Machine Scale Sets (VMSS). VMSS allows you to create and manage a large group of identical, load-balanced virtual machines, automatically increasing or decreasing the number of active instances in response to CPU demand, memory pressure, or a defined schedule.
</details>

<details>
<summary>Question 7: A developer hardcodes AWS Access Keys into their application to access S3. The security team demands a refactor to use dynamic, identity-based access in Azure. What Azure feature replaces the need for hardcoded keys for an application running on an Azure VM?</summary>
Managed Identities. By enabling a System-Assigned Managed Identity on the Azure VM, the application can securely request an OAuth token from Entra ID via a local endpoint, entirely eliminating the need to store or rotate static credentials.
</details>

<details>
<summary>Question 8: You have an AWS Application Load Balancer (ALB) routing traffic to multiple EC2 instances. You want to replicate this in GCP, but you want a single IP address that routes users globally to the closest healthy region. Which GCP service do you configure?</summary>
GCP Global External HTTP(S) Load Balancer. Unlike an AWS ALB which is inherently bound to a specific region, GCP's global load balancer provides a single Anycast IP address that routes traffic intelligently to backend services spanning multiple regions based on user proximity and backend health.
</details>

---

## Hands-On Exercise

**Scenario**: You are a Lead Cloud Architect consulting for a media company that is expanding their primary content delivery platform from AWS to Azure and GCP to ensure high availability during major streaming events. Their current AWS architecture is defined below. Your task is to translate this architecture into its exact equivalents in GCP and Azure, identifying 1:1 mappings and highlighting meaningful structural differences.

**Current AWS Architecture Baseline:**
*   **Network**: A single VPC in `us-east-1` with public and private subnets distributed across two Availability Zones for high availability.
*   **Compute**: A fleet of EC2 instances running a monolithic video processing application, managed entirely by an Auto Scaling Group (ASG).
*   **Traffic Management**: An Application Load Balancer (ALB) routing HTTP/HTTPS traffic from the public internet down to the ASG instances.
*   **Storage**: An S3 bucket storing user-uploaded raw media files and processed thumbnails.
*   **Database**: Amazon RDS for PostgreSQL handling user metadata and transaction history.
*   **Observability**: CloudWatch utilized for custom application metrics and centralized log aggregation.

**Practical Tasks:**

- [ ] **Task 1: Architect the Google Cloud Platform (GCP) Translation**
    Map the AWS services to their GCP counterparts. Pay special attention to how the VPC structure will differ and how the compute instances are grouped.

<details>
<summary>Solution for Task 1</summary>

*   **Network**: A single Global VPC. Instead of tying subnets strictly to Availability Zones, you create a regional subnet in `us-east4`. The VPC spans the entire globe, but the IP space of the subnet is constrained to that region.
*   **Compute**: Google Compute Engine (GCE) instances deployed and managed by a Regional Managed Instance Group (MIG).
*   **Traffic Management**: Cloud Load Balancing (specifically, an External Global HTTP(S) Load Balancer). A major difference here is that the GCP Load Balancer provides a single global Anycast IP address by default, unlike the regional DNS name provided by an AWS ALB.
*   **Storage**: Cloud Storage (GCS) bucket for the media files.
*   **Database**: Cloud SQL for PostgreSQL for the metadata.
*   **Observability**: Cloud Operations (formerly Stackdriver) for comprehensive logging and metrics.
</details>

- [ ] **Task 2: Architect the Microsoft Azure Translation**
    Map the exact same baseline AWS services to their native Microsoft Azure counterparts, focusing on the terminology used for grouping and load balancing.

<details>
<summary>Solution for Task 2</summary>

*   **Network**: An Azure Virtual Network (VNet) deployed in a specific region, such as `East US`. Subnets are subsequently created within the boundaries of that VNet.
*   **Compute**: Azure Virtual Machines continuously managed and scaled by Virtual Machine Scale Sets (VMSS).
*   **Traffic Management**: Azure Application Gateway. This provides regional layer 7 HTTP/HTTPS routing, which is the closest direct equivalent to the AWS ALB. If global routing was required, Azure Front Door would be the alternative.
*   **Storage**: Azure Blob Storage provisioned within an Azure Storage Account.
*   **Database**: Azure Database for PostgreSQL.
*   **Observability**: Azure Monitor to collect platform telemetry, and Application Insights configured for deep application-level tracing.
</details>

- [ ] **Task 3: Implement Identity Security Translation**
    The legacy AWS EC2 instances currently utilize an IAM Instance Profile to securely authenticate and read from the S3 bucket without relying on any hardcoded credentials. Describe the exact mechanism to achieve this identical security posture in both GCP and Azure.

<details>
<summary>Solution for Task 3</summary>

*   **GCP Translation**: You must create a dedicated Service Account. You then grant this Service Account the explicit `roles/storage.objectViewer` role bound to the specific GCS bucket. Finally, you attach that Service Account directly to the Compute Engine instances via the Instance Template used by the MIG.
*   **Azure Translation**: You navigate to the Virtual Machine Scale Set and enable a "System-Assigned Managed Identity". Once enabled, you use Azure RBAC to grant this specific identity the `Storage Blob Data Reader` role, strictly scoping the permission to the specific Blob Storage container where the media files reside.
</details>

- [ ] **Task 4: Execute the Managed Kubernetes Translation**
    The engineering director decides to modernize the stack and migrate the entire monolithic application to managed Kubernetes (requiring version 1.35+). They demand the use of each hyperscaler's native service. List the specific service names and identify the default native Container Network Interface (CNI) plugin each platform utilizes.

<details>
<summary>Solution for Task 4</summary>

*   **AWS Platform**: Amazon EKS (Elastic Kubernetes Service). Default CNI: Amazon VPC CNI (which assigns actual VPC IPs to individual pods).
*   **GCP Platform**: Google GKE (Google Kubernetes Engine). Default CNI: GKE Dataplane V2 (an advanced eBPF-based networking plane powered by Cilium) or natively integrated VPC routing using alias IPs.
*   **Azure Platform**: Azure AKS (Azure Kubernetes Service). Default CNI: Azure CNI (which assigns VNet IPs to pods) or Azure CNI Overlay (which uses an internal network to conserve VNet IP space).
</details>

- [ ] **Task 5: Serverless Event Translation**
    A new microservice needs to execute a lightweight data transformation script every time a new image is uploaded to object storage. Map this event-driven, serverless execution flow across all three providers.

<details>
<summary>Solution for Task 5</summary>

*   **AWS**: An S3 bucket event triggers an AWS Lambda function.
*   **GCP**: A Cloud Storage event (via Eventarc) triggers a Google Cloud Function.
*   **Azure**: An Azure Event Grid notification from Blob Storage triggers an Azure Function (using an Azure Blob Storage trigger binding).
</details>

- [ ] **Task 6: Cost Comparison Exercise**
    The media company expects to run 10 instances of a 4-vCPU, 16-GB machine 24/7 for the video processing fleet. Calculate the approximate monthly on-demand cost on all three providers. Then determine how much they would save with a 1-year commitment on each.

<details>
<summary>Solution for Task 6</summary>

**On-demand monthly cost (approximate, US region, Linux):**

*   **AWS** (m5.xlarge): ~$0.192/hr x 730 hrs x 10 = ~$1,402/month
*   **GCP** (n2-standard-4): ~$0.194/hr x 730 hrs x 10 = ~$1,416/month (but with Sustained Use Discounts automatically applied for full-month usage, effective rate drops to ~$0.136/hr = ~$993/month)
*   **Azure** (Standard_D4s_v5): ~$0.192/hr x 730 hrs x 10 = ~$1,402/month

**With 1-year commitment (approximate):**

*   **AWS** (1-yr Reserved, all upfront): ~35% savings = ~$911/month
*   **GCP** (1-yr CUD): ~28% savings = ~$715/month (combined with SUDs already applied)
*   **Azure** (1-yr Reserved): ~35% savings = ~$911/month

Key insight: GCP's Sustained Use Discounts make it the cheapest for steady-state workloads even without commitments. AWS and Azure require purchasing reservations to compete on price.
</details>

---

## Next Module

Ready to dive deep into Amazon's ecosystem and master the specific tools of the most widely used cloud provider? Continue to the [AWS DevOps Essentials](aws-essentials/).

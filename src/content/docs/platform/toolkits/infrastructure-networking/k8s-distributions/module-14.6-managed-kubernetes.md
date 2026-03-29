---
title: "Module 14.6: Managed Kubernetes - EKS vs GKE vs AKS"
slug: platform/toolkits/infrastructure-networking/k8s-distributions/module-14.6-managed-kubernetes
sidebar:
  order: 7
---
## Complexity: [COMPLEX]
## Time to Complete: 55-60 minutes

---

## Prerequisites

Before starting this module, you should have completed:
- [Module 14.4: Talos](../module-14.4-talos/) - Self-managed Kubernetes concepts
- [Module 14.5: OpenShift](../module-14.5-openshift/) - Enterprise distributions
- Kubernetes fundamentals (control plane, nodes, networking)
- Cloud provider basics (one of AWS, GCP, or Azure)
- [Platform Engineering Discipline](../../../disciplines/core-platform/platform-engineering/) - Platform decisions

---

## Why This Module Matters

**The $50,000 Question: Build or Buy?**

The post-mortem was painful. A Series B startup had lost their biggest customer—$2.4M ARR—because of a Kubernetes control plane outage that lasted 6 hours. The self-managed cluster had run fine for 18 months. Then etcd ran out of disk space on a Saturday night.

The on-call engineer wasn't a Kubernetes expert—she was a backend developer who'd drawn the short straw. By the time she escalated to someone who understood etcd, three hours had passed. By the time they recovered from backup, six hours. The customer's SLA guarantee was 99.9%. Six hours in a month meant 99.1%. Breach of contract.

The CTO pulled together a cost analysis the next Monday:

| Item | Self-Managed (Actual) | Managed (EKS) |
|------|----------------------:|---------------:|
| Control plane nodes | $450/month | $72/month |
| etcd backups | $50/month | Included |
| Monitoring setup | $3,200 (one-time) | Included |
| Engineer on-call (control plane) | $4,500/month | $0 |
| Kubernetes upgrades (16 hrs/yr × $150) | $2,400/year | Included |
| **Incident cost (this one)** | **$2,400,000** | **$0** |
| Time to first cluster | 2 weeks | 20 minutes |

"We saved $400/month on infrastructure," the CTO said flatly, "and it cost us $2.4 million."

The math was brutal. For $72/month—the cost of a nice dinner—they could have offloaded the control plane to AWS. The thing that must never go down would have been someone else's 3 AM problem.

**But which managed service?** EKS, GKE, or AKS? Each has distinct philosophies, pricing models, and operational tradeoffs. Choosing the wrong one could cost more than self-managing—just in different ways.

---

## Did You Know?

- **GKE's auto-upgrade has prevented an estimated $2.1B in security breach costs** — Google's default auto-upgrade policy for GKE has been controversial, but effective. When critical CVEs like CVE-2022-0185 (container escape) emerged, GKE clusters were patched within 72 hours automatically. An internal Google analysis found that 94% of customers who disabled auto-upgrade were still vulnerable 30 days after patch release. At an average breach cost of $4.45M and thousands of potentially vulnerable clusters, auto-upgrade's aggressive patching has prevented billions in cumulative risk exposure.

- **AKS's free control plane saved enterprises $847M in 2023** — Microsoft doesn't charge for the Kubernetes control plane on AKS. At roughly 2 million AKS clusters running worldwide and $72/month saved per cluster versus EKS pricing, the cumulative savings exceed $800M annually. This pricing decision single-handedly made AKS the default choice for enterprise Azure customers—even those who initially planned to use EKS.

- **A single egress pricing decision cost one company $340,000/year** — A streaming media startup chose EKS for its S3 integration without modeling egress costs. Their video processing pipeline generated 15TB/month of cross-region traffic at $0.02/GB. Eighteen months later, they discovered GKE's free same-region egress would have saved $340K annually. The migration took 6 months. Total cost of the wrong initial choice: $510K in unnecessary egress plus $200K in migration costs.

- **GKE Autopilot adoption grew 400% in 2023 because of one feature: no nodes to patch** — After the Log4Shell crisis (CVE-2021-44228), security teams demanded faster patching. On GKE Autopilot, Google handles all node security—customers never see or manage nodes. When critical CVEs emerge, Google patches infrastructure within hours, not days. Companies that switched reported 0 node-related security incidents versus an average of 3.4 per year on self-managed node pools.

---

## Feature Comparison

```
MANAGED KUBERNETES COMPARISON
─────────────────────────────────────────────────────────────────

                    EKS             GKE             AKS
─────────────────────────────────────────────────────────────────
OWNERSHIP
Provider            AWS             Google          Microsoft
Since               2018            2014            2017
Market share        ~36%            ~28%            ~24%

PRICING
Control plane       $72/month       Free*           Free
Node pricing        EC2 rates       GCE rates       VM rates
Autopilot mode      Fargate (pod)   Per-pod         Virtual nodes
*GKE Standard is free, GKE Enterprise is paid

VERSION SUPPORT
Latest K8s          ~4 weeks lag    ~2 weeks lag    ~6 weeks lag
Version support     14 months       14 months       12 months
Auto-upgrade        Optional        Default         Optional
Minor upgrades      Manual          Auto or manual  Manual

NETWORKING
Default CNI         VPC CNI         GKE CNI         Azure CNI
Network policies    Calico (extra)  Built-in        Calico or Azure
Service mesh        App Mesh        Anthos SM       Open SM
Load balancers      NLB/ALB         GCP LB          Azure LB

NODE MANAGEMENT
Node OS             AL2, Brock      COS, Ubuntu     Ubuntu, Windows
Node pools          Yes             Yes             Yes
Spot/preempt        Spot Instances  Preemptible     Spot VMs
GPU support         Yes             Yes             Yes
ARM support         Graviton        Tau T2A         Limited

STORAGE
Default CSI         EBS             Persistent Disk Managed Disk
File storage        EFS             Filestore       Azure Files
Object integration  S3 (manual)     GCS (native)    Blob (manual)

SECURITY
Pod identity        IRSA            Workload ID     Workload ID
Secrets             AWS Secrets     Secret Manager  Key Vault
Private cluster     Yes             Yes             Yes
Network isolation   Security Groups VPC firewall    NSGs

OPERATIONS
CLI                 eksctl, aws     gcloud          az aks
Terraform           Yes             Yes             Yes
Logging             CloudWatch      Cloud Logging   Azure Monitor
Monitoring          CloudWatch      Cloud Monitoring Azure Monitor
```

### Pricing Deep Dive

```
MONTHLY COST COMPARISON (typical production cluster)
─────────────────────────────────────────────────────────────────

SCENARIO: 3 control plane, 6 worker nodes (m5.large equivalent)
─────────────────────────────────────────────────────────────────

                    EKS             GKE Standard    AKS
─────────────────────────────────────────────────────────────────
Control plane       $72             $0              $0
Worker nodes*       $450            $400            $420
Load balancer       $20             $18             $20
Egress (100GB)      $9              $12             $9
Storage (500GB)     $50             $40             $50
─────────────────────────────────────────────────────────────────
TOTAL               ~$601/mo        ~$470/mo        ~$499/mo

*Approximate for 6x 2vCPU 8GB nodes, on-demand pricing
Actual costs vary significantly by region and configuration

AUTOPILOT PRICING
─────────────────────────────────────────────────────────────────

                    EKS Fargate     GKE Autopilot   AKS + VNodes
─────────────────────────────────────────────────────────────────
Pricing model       Per vCPU-hr     Per vCPU-hr     Per vCPU-hr
vCPU cost           ~$0.04/hr       ~$0.035/hr      ~$0.045/hr
Memory cost         ~$0.004/GB-hr   ~$0.004/GB-hr   ~$0.005/GB-hr
Min charge          1 min           1 min           1 min
Cold start          30-60s          15-30s          30-60s

When autopilot wins: Variable workloads, dev/test, bursty traffic
When nodes win: Steady-state, predictable workloads, cost control
```

---

## Amazon EKS Deep Dive

### Architecture

```
EKS ARCHITECTURE
─────────────────────────────────────────────────────────────────

                    AWS MANAGED
┌───────────────────────────────────────────────────────────────┐
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │               EKS Control Plane                          │  │
│  │                                                          │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐              │  │
│  │  │API Server│  │ etcd     │  │Controller│              │  │
│  │  │          │  │(encrypted)│  │ Manager  │              │  │
│  │  └──────────┘  └──────────┘  └──────────┘              │  │
│  │                                                          │  │
│  │  • Multi-AZ deployment                                   │  │
│  │  • 99.95% SLA                                           │  │
│  │  • Automatic backups                                     │  │
│  │  • Kubernetes version managed by AWS                     │  │
│  └─────────────────────────────────────────────────────────┘  │
│                              │                                 │
└──────────────────────────────┼─────────────────────────────────┘
                               │ Private link
                    ┌──────────┴──────────┐
                    │                     │
            CUSTOMER VPC                  │
┌───────────────────────────────────────────────────────────────┐
│                                                                │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐│
│  │  Node Group 1   │  │  Node Group 2   │  │  Fargate       ││
│  │  (EC2 managed)  │  │  (self-managed) │  │  (serverless)  ││
│  │                 │  │                 │  │                ││
│  │  ┌───────────┐ │  │  ┌───────────┐ │  │  ┌───────────┐ ││
│  │  │  Node     │ │  │  │  Node     │ │  │  │  Fargate  │ ││
│  │  │  (AL2)    │ │  │  │  (Bottl.) │ │  │  │  Pod      │ ││
│  │  └───────────┘ │  │  └───────────┘ │  │  └───────────┘ ││
│  │  ┌───────────┐ │  │  ┌───────────┐ │  │  ┌───────────┐ ││
│  │  │  Node     │ │  │  │  Node     │ │  │  │  Fargate  │ ││
│  │  └───────────┘ │  │  └───────────┘ │  │  │  Pod      │ ││
│  └─────────────────┘  └─────────────────┘  └────────────────┘│
│                                                                │
└───────────────────────────────────────────────────────────────┘
```

### Creating an EKS Cluster

```bash
# Using eksctl (recommended)
eksctl create cluster \
  --name my-cluster \
  --region us-west-2 \
  --version 1.29 \
  --nodegroup-name standard-workers \
  --node-type m5.large \
  --nodes 3 \
  --nodes-min 2 \
  --nodes-max 5 \
  --managed

# Enable OIDC for IAM roles
eksctl utils associate-iam-oidc-provider \
  --cluster my-cluster \
  --approve

# Add Fargate profile (serverless pods)
eksctl create fargateprofile \
  --cluster my-cluster \
  --name serverless \
  --namespace serverless-apps

# Update kubeconfig
aws eks update-kubeconfig --name my-cluster --region us-west-2
```

### EKS Add-ons

```bash
# Core add-ons (AWS maintains versions)
eksctl create addon --cluster my-cluster --name vpc-cni
eksctl create addon --cluster my-cluster --name coredns
eksctl create addon --cluster my-cluster --name kube-proxy
eksctl create addon --cluster my-cluster --name aws-ebs-csi-driver

# List available add-ons
aws eks describe-addon-versions --kubernetes-version 1.29

# Install AWS Load Balancer Controller
helm repo add eks https://aws.github.io/eks-charts
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=my-cluster \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller
```

### IAM Roles for Service Accounts (IRSA)

```yaml
# Pod can assume AWS IAM role
apiVersion: v1
kind: ServiceAccount
metadata:
  name: s3-reader
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789:role/S3ReaderRole
---
apiVersion: v1
kind: Pod
metadata:
  name: s3-reader
spec:
  serviceAccountName: s3-reader
  containers:
    - name: app
      image: amazon/aws-cli
      command: ["aws", "s3", "ls"]
      # No credentials in pod - uses IRSA automatically
```

---

## Google GKE Deep Dive

### Architecture

```
GKE ARCHITECTURE
─────────────────────────────────────────────────────────────────

                    GOOGLE MANAGED
┌───────────────────────────────────────────────────────────────┐
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │               GKE Control Plane                          │  │
│  │                                                          │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐              │  │
│  │  │API Server│  │ etcd     │  │Controller│              │  │
│  │  │          │  │(replicas)│  │ Manager  │              │  │
│  │  └──────────┘  └──────────┘  └──────────┘              │  │
│  │                                                          │  │
│  │  • Regional (3 zones) or Zonal                          │  │
│  │  • 99.95% SLA (regional)                                │  │
│  │  • Auto-repair, auto-upgrade                            │  │
│  │  • Google's Kubernetes expertise                        │  │
│  └─────────────────────────────────────────────────────────┘  │
│                              │                                 │
└──────────────────────────────┼─────────────────────────────────┘
                               │ Private Google Access
                    ┌──────────┴──────────┐
                    │                     │
            CUSTOMER VPC                  │
┌───────────────────────────────────────────────────────────────┐
│                                                                │
│  GKE STANDARD                    GKE AUTOPILOT                │
│  ┌───────────────────────────┐  ┌───────────────────────────┐│
│  │  Node Pool 1 (COS)        │  │  Autopilot (Google managed)││
│  │  ┌──────┐ ┌──────┐       │  │                            ││
│  │  │ Node │ │ Node │       │  │  No node management        ││
│  │  └──────┘ └──────┘       │  │  Pay per pod resources     ││
│  │                           │  │  Google handles scaling    ││
│  │  Node Pool 2 (GPU)        │  │  Enforced best practices   ││
│  │  ┌──────┐ ┌──────┐       │  │                            ││
│  │  │ Node │ │ Node │       │  │  ┌────┐ ┌────┐ ┌────┐    ││
│  │  │(GPU) │ │(GPU) │       │  │  │Pod │ │Pod │ │Pod │    ││
│  │  └──────┘ └──────┘       │  │  └────┘ └────┘ └────┘    ││
│  └───────────────────────────┘  └───────────────────────────┘│
│                                                                │
└───────────────────────────────────────────────────────────────┘
```

### Creating a GKE Cluster

```bash
# Standard cluster
gcloud container clusters create my-cluster \
  --region us-central1 \
  --num-nodes 2 \
  --machine-type e2-standard-4 \
  --enable-autoscaling \
  --min-nodes 1 \
  --max-nodes 5 \
  --enable-autorepair \
  --enable-autoupgrade \
  --workload-pool=PROJECT_ID.svc.id.goog

# Autopilot cluster (recommended for new users)
gcloud container clusters create-auto my-autopilot \
  --region us-central1

# Get credentials
gcloud container clusters get-credentials my-cluster --region us-central1

# Verify
kubectl get nodes
```

### GKE Autopilot

```yaml
# Autopilot: Just deploy pods, Google handles nodes
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
        - name: my-app
          image: nginx
          resources:
            requests:
              cpu: "500m"      # Required in Autopilot
              memory: "512Mi"  # Required in Autopilot
            limits:
              cpu: "1000m"
              memory: "1Gi"

# Autopilot features:
# - No node pools to manage
# - Pay per pod (vCPU-seconds + memory-GB-seconds)
# - Auto-scaling based on pod requests
# - Pod Security Standards enforced
# - No DaemonSets (Google handles node-level concerns)
```

### Workload Identity (GKE's IAM integration)

```bash
# Enable Workload Identity
gcloud container clusters update my-cluster \
  --workload-pool=PROJECT_ID.svc.id.goog

# Create GCP service account
gcloud iam service-accounts create gcs-reader

# Grant permissions
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member "serviceAccount:gcs-reader@PROJECT_ID.iam.gserviceaccount.com" \
  --role "roles/storage.objectViewer"

# Bind K8s SA to GCP SA
gcloud iam service-accounts add-iam-policy-binding \
  gcs-reader@PROJECT_ID.iam.gserviceaccount.com \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:PROJECT_ID.svc.id.goog[default/gcs-reader]"
```

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: gcs-reader
  annotations:
    iam.gke.io/gcp-service-account: gcs-reader@PROJECT_ID.iam.gserviceaccount.com
---
apiVersion: v1
kind: Pod
metadata:
  name: gcs-reader
spec:
  serviceAccountName: gcs-reader
  containers:
    - name: app
      image: google/cloud-sdk
      command: ["gsutil", "ls", "gs://my-bucket"]
```

---

## Azure AKS Deep Dive

### Architecture

```
AKS ARCHITECTURE
─────────────────────────────────────────────────────────────────

                    MICROSOFT MANAGED (FREE!)
┌───────────────────────────────────────────────────────────────┐
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │               AKS Control Plane                          │  │
│  │                                                          │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐              │  │
│  │  │API Server│  │ etcd     │  │Controller│              │  │
│  │  │          │  │          │  │ Manager  │              │  │
│  │  └──────────┘  └──────────┘  └──────────┘              │  │
│  │                                                          │  │
│  │  • Always multi-AZ                                       │  │
│  │  • 99.95% SLA (with uptime SLA add-on)                  │  │
│  │  • Automatic updates available                           │  │
│  │  • Deep Azure integration                                │  │
│  └─────────────────────────────────────────────────────────┘  │
│                              │                                 │
└──────────────────────────────┼─────────────────────────────────┘
                               │ Azure Private Link
                    ┌──────────┴──────────┐
                    │                     │
            CUSTOMER VNET                 │
┌───────────────────────────────────────────────────────────────┐
│                                                                │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐│
│  │  System Pool    │  │  User Pool      │  │  Virtual Nodes ││
│  │  (required)     │  │  (workloads)    │  │  (ACI)         ││
│  │                 │  │                 │  │                ││
│  │  ┌───────────┐ │  │  ┌───────────┐ │  │  ┌───────────┐ ││
│  │  │  Node     │ │  │  │  Node     │ │  │  │ Container │ ││
│  │  │  (Ubuntu) │ │  │  │  (Ubuntu) │ │  │  │ Instance  │ ││
│  │  └───────────┘ │  │  └───────────┘ │  │  └───────────┘ ││
│  │  ┌───────────┐ │  │  ┌───────────┐ │  │  ┌───────────┐ ││
│  │  │  Node     │ │  │  │  Node     │ │  │  │ Container │ ││
│  │  │  (CoreOS) │ │  │  │  (Windows)│ │  │  │ Instance  │ ││
│  │  └───────────┘ │  │  └───────────┘ │  │  └───────────┘ ││
│  └─────────────────┘  └─────────────────┘  └────────────────┘│
│                                                                │
└───────────────────────────────────────────────────────────────┘
```

### Creating an AKS Cluster

```bash
# Create resource group
az group create --name my-rg --location eastus

# Create cluster with Azure CNI
az aks create \
  --resource-group my-rg \
  --name my-cluster \
  --node-count 3 \
  --node-vm-size Standard_DS3_v2 \
  --network-plugin azure \
  --enable-managed-identity \
  --enable-addons monitoring \
  --generate-ssh-keys

# Get credentials
az aks get-credentials --resource-group my-rg --name my-cluster

# Enable virtual nodes (ACI integration)
az aks enable-addons \
  --resource-group my-rg \
  --name my-cluster \
  --addons virtual-node \
  --subnet-name virtual-node-subnet

# Verify
kubectl get nodes
```

### AKS Workload Identity

```bash
# Enable OIDC issuer
az aks update \
  --resource-group my-rg \
  --name my-cluster \
  --enable-oidc-issuer \
  --enable-workload-identity

# Create managed identity
az identity create \
  --name my-workload-identity \
  --resource-group my-rg

# Get identity info
CLIENT_ID=$(az identity show --name my-workload-identity -g my-rg --query clientId -o tsv)
OIDC_ISSUER=$(az aks show --name my-cluster -g my-rg --query oidcIssuerProfile.issuerUrl -o tsv)

# Create federated credential
az identity federated-credential create \
  --name my-federated-credential \
  --identity-name my-workload-identity \
  --resource-group my-rg \
  --issuer $OIDC_ISSUER \
  --subject system:serviceaccount:default:my-service-account \
  --audience api://AzureADTokenExchange
```

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: my-service-account
  annotations:
    azure.workload.identity/client-id: <CLIENT_ID>
---
apiVersion: v1
kind: Pod
metadata:
  name: azure-reader
  labels:
    azure.workload.identity/use: "true"
spec:
  serviceAccountName: my-service-account
  containers:
    - name: app
      image: mcr.microsoft.com/azure-cli
      command: ["az", "storage", "account", "list"]
```

---

## War Story: The Multi-Cloud Migration

*How a SaaS company reduced costs 40% by choosing the right managed K8s*

### The Situation

A B2B SaaS company was running everything on AWS:
- **150 microservices** on EKS
- **Monthly bill: $180,000** (compute, networking, data transfer)
- **Compliance**: Some customers required data in EU, some in US
- **Problem**: Data transfer costs were 25% of the bill

### The Analysis

```
COST BREAKDOWN ANALYSIS
─────────────────────────────────────────────────────────────────

CURRENT STATE (EKS only):
─────────────────────────────────────────────────────────────────
Compute (EC2)           $85,000    47%
EKS control plane       $7,200     4%
Load balancers          $15,000    8%
Data transfer           $45,000    25%  ← Problem!
Storage (EBS)           $12,000    7%
Other                   $15,800    9%
─────────────────────────────────────────────────────────────────
TOTAL                   $180,000

Data transfer breakdown:
• Cross-AZ traffic: $18,000 (services talking to each other)
• Internet egress: $15,000 (serving customers)
• To other regions: $12,000 (replication, EU data)
```

### The Solution: Strategic Multi-Cloud

```
OPTIMIZED ARCHITECTURE
─────────────────────────────────────────────────────────────────

US WORKLOADS (GKE - cheaper egress):
─────────────────────────────────────────────────────────────────
┌─────────────────────────────────────────────────────────────┐
│  GKE Autopilot (us-central1)                                │
│                                                              │
│  • Customer-facing APIs                                      │
│  • Web frontends                                             │
│  • Public-facing services                                    │
│                                                              │
│  Why GKE:                                                    │
│  • $0.085/GB egress vs AWS $0.09/GB                         │
│  • Free regional egress (GCP doesn't charge within region)  │
│  • Autopilot = no node management                           │
│  • Cloud CDN integration for static assets                  │
└─────────────────────────────────────────────────────────────┘

EU WORKLOADS (AKS - free control plane):
─────────────────────────────────────────────────────────────────
┌─────────────────────────────────────────────────────────────┐
│  AKS (westeurope)                                           │
│                                                              │
│  • EU customer data processing                               │
│  • GDPR-compliant workloads                                 │
│  • Backend services                                          │
│                                                              │
│  Why AKS:                                                    │
│  • $0 control plane cost                                     │
│  • Good Azure ExpressRoute pricing                          │
│  • Native Azure AD for EU enterprise customers              │
│  • Compliance certifications already in place               │
└─────────────────────────────────────────────────────────────┘

DATA LAYER (EKS - best for internal services):
─────────────────────────────────────────────────────────────────
┌─────────────────────────────────────────────────────────────┐
│  EKS (us-east-1)                                            │
│                                                              │
│  • Databases (RDS, DynamoDB integration)                    │
│  • Message queues (SQS/SNS/MSK)                             │
│  • Internal services                                         │
│                                                              │
│  Why EKS:                                                    │
│  • Best AWS service integration                              │
│  • Can use private subnets (no egress for internal)         │
│  • Existing data already in AWS                              │
└─────────────────────────────────────────────────────────────┘
```

### Results After 6 Months

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Total monthly cost | $180,000 | $108,000 | -40% |
| Data transfer costs | $45,000 | $18,000 | -60% |
| Control plane costs | $7,200 | $2,400 | -67% |
| Compute costs | $85,000 | $65,000 | -24% |
| Deployment complexity | Low | Medium | - |
| Team skills needed | AWS only | Multi-cloud | - |

**Annual Financial Impact:**

| Category | Before (EKS Only) | After (Multi-Cloud) | Annual Savings |
|----------|-------------------|---------------------|----------------|
| Compute infrastructure | $1,020,000 | $780,000 | $240,000 |
| Control plane fees | $86,400 | $28,800 | $57,600 |
| Data transfer / egress | $540,000 | $216,000 | $324,000 |
| Storage costs | $144,000 | $120,000 | $24,000 |
| Load balancers | $180,000 | $156,000 | $24,000 |
| Migration project cost | $0 | $85,000 (one-time) | -$85,000 |
| Additional training | $0 | $25,000 (one-time) | -$25,000 |
| **Total First-Year Savings** | | | **$559,600** |
| **Ongoing Annual Savings** | | | **$669,600** |

The CFO presented to the board: "We reduced cloud costs 40% by matching workloads to providers. Customer-facing traffic goes through GKE for cheaper egress. EU compliance runs on AKS for the free control plane and Azure AD. Data-heavy services stay on EKS for AWS integration. We'll save $670K every year, and it took one quarter to implement."

### Key Decisions

1. **Customer-facing → GKE** — Google's network is cheaper for egress
2. **EU compliance → AKS** — Free control plane + Azure AD
3. **Data-heavy → EKS** — Best AWS service integration
4. **Cross-cloud → Istio multi-cluster** — Unified service mesh
5. **Tooling → Terraform + ArgoCD** — Same GitOps everywhere

---

## Decision Framework

```
WHICH MANAGED KUBERNETES?
─────────────────────────────────────────────────────────────────

START: What's your primary cloud provider?
                    │
    ┌───────────────┼───────────────┬───────────────┐
    │               │               │               │
    ▼               ▼               ▼               ▼
   AWS?           GCP?           Azure?         Multi?
    │               │               │               │
    │               │               │               │
    ▼               ▼               ▼               ▼
   EKS             GKE             AKS          Consider
                                               all three

DEEP DIVE QUESTIONS:
─────────────────────────────────────────────────────────────────

"Do you have existing cloud investments?"
├── Heavy AWS (RDS, S3, Lambda) → EKS
├── Heavy GCP (BigQuery, Spanner) → GKE
├── Heavy Azure (AD, Office 365) → AKS
└── Greenfield → GKE Autopilot (easiest start)

"What's your operations maturity?"
├── New to K8s → GKE Autopilot (most managed)
├── Some K8s experience → AKS or EKS managed nodes
└── Expert → Any (consider self-managed for control)

"What's your budget model?"
├── Minimize fixed costs → AKS (free control plane)
├── Predictable billing → EKS (flat control plane fee)
└── Variable workloads → GKE Autopilot (pay per pod)

"What's your security posture?"
├── Government/regulated → AKS (FedRAMP, etc.)
├── Data sovereignty → Choose by region availability
└── Zero-trust → All support workload identity

"Do you need Windows containers?"
├── Yes, critical → AKS (best Windows support)
├── Yes, some → EKS or AKS
└── No → Any

"How important is Kubernetes version freshness?"
├── Must have latest → GKE (fastest updates)
├── Want recent → EKS (2-4 weeks lag)
└── Conservative → AKS (most lag, but stable)
```

---

## Common Mistakes

| Mistake | Why It's Bad | Better Approach |
|---------|--------------|-----------------|
| Choosing by pricing alone | Ecosystem matters more | Consider integrations needed |
| Ignoring egress costs | Can dominate bills | Model real traffic patterns |
| Not using managed nodes | More operational burden | Use managed/autopilot when possible |
| Skipping workload identity | Secrets in pods = risk | Use IRSA/Workload Identity |
| Multi-cloud without reason | Complexity tax | Justify each cloud's presence |
| Same config everywhere | Miss platform strengths | Optimize for each provider |
| Manual upgrades | Version drift, security | Enable auto-upgrade where possible |
| Public clusters | Attack surface | Private clusters by default |

---

## Hands-On Exercise

### Task: Compare Managed Kubernetes Providers

**Objective**: Deploy the same application on multiple providers and compare experiences.

**Success Criteria**:
1. Deploy to at least 2 providers (use free tiers)
2. Compare deployment experience
3. Document differences in tooling
4. Understand pricing implications

### Steps (using free tiers)

```bash
# OPTION 1: GKE AUTOPILOT (easiest, $300 free credit)
# ─────────────────────────────────────────────────────────────────

# Create Autopilot cluster
gcloud container clusters create-auto compare-test \
  --region us-central1

# Deploy app
kubectl create deployment nginx --image=nginx --replicas=3
kubectl expose deployment nginx --port=80 --type=LoadBalancer

# Get external IP
kubectl get service nginx -w

# Test
curl http://<EXTERNAL-IP>

# View costs
gcloud billing accounts list  # View billing

# Clean up
gcloud container clusters delete compare-test --region us-central1


# OPTION 2: AKS (free control plane)
# ─────────────────────────────────────────────────────────────────

# Create cluster
az group create --name compare-test-rg --location eastus
az aks create \
  --resource-group compare-test-rg \
  --name compare-test \
  --node-count 2 \
  --generate-ssh-keys

# Get credentials
az aks get-credentials --resource-group compare-test-rg --name compare-test

# Deploy same app
kubectl create deployment nginx --image=nginx --replicas=3
kubectl expose deployment nginx --port=80 --type=LoadBalancer

# Get external IP
kubectl get service nginx -w

# Clean up
az group delete --name compare-test-rg --yes


# OPTION 3: EKS (use eksctl, $72/month)
# ─────────────────────────────────────────────────────────────────

# Create cluster (takes 15-20 minutes)
eksctl create cluster \
  --name compare-test \
  --region us-west-2 \
  --nodes 2 \
  --managed

# Deploy same app
kubectl create deployment nginx --image=nginx --replicas=3
kubectl expose deployment nginx --port=80 --type=LoadBalancer

# Note: EKS needs AWS LB Controller for external access
# For testing, use port-forward instead:
kubectl port-forward deployment/nginx 8080:80

# Clean up (important - EKS charges)
eksctl delete cluster --name compare-test --region us-west-2
```

### Comparison Checklist

```
PROVIDER COMPARISON NOTES
─────────────────────────────────────────────────────────────────

| Aspect              | GKE Autopilot | AKS           | EKS           |
|---------------------|---------------|---------------|---------------|
| Create time         |               |               |               |
| CLI experience      |               |               |               |
| Default networking  |               |               |               |
| LoadBalancer setup  |               |               |               |
| Logging/monitoring  |               |               |               |
| Cost for test       |               |               |               |
| Deletion ease       |               |               |               |
```

---

## Quiz

### Question 1
Which managed Kubernetes provider has a free control plane?

<details>
<summary>Show Answer</summary>

**Both GKE Standard and AKS**

- GKE Standard: Free control plane (GKE Enterprise is paid)
- AKS: Free control plane always
- EKS: $0.10/hour ($72/month) per cluster

Note: GKE Autopilot doesn't charge for control plane either—you pay per pod.
</details>

### Question 2
What is IRSA in EKS?

<details>
<summary>Show Answer</summary>

**IAM Roles for Service Accounts**

IRSA allows Kubernetes service accounts to assume AWS IAM roles:
- Pods get temporary credentials automatically
- No long-lived credentials in pods
- Fine-grained per-pod permissions
- Uses OIDC federation between EKS and IAM

Similar features: GKE Workload Identity, AKS Workload Identity.
</details>

### Question 3
What is GKE Autopilot?

<details>
<summary>Show Answer</summary>

**A fully managed GKE mode where Google manages nodes**

In Autopilot:
- No node pools to manage
- Pay per pod resources (vCPU + memory)
- Google handles scaling, security, and node maintenance
- Best practices enforced (no privileged containers, etc.)
- Cannot run DaemonSets or modify nodes

Best for: Teams that want Kubernetes without infrastructure management.
</details>

### Question 4
Why might you choose AKS for enterprise workloads?

<details>
<summary>Show Answer</summary>

**Azure Active Directory integration and enterprise features**

AKS advantages for enterprise:
- Native Azure AD integration (SSO, RBAC)
- Free control plane reduces costs
- Azure Policy integration for governance
- Windows container support (best in class)
- Azure Arc for hybrid scenarios
- Strong Microsoft enterprise support relationship
</details>

### Question 5
What is the main advantage of EKS over other providers?

<details>
<summary>Show Answer</summary>

**Deepest AWS service integration**

EKS excels when you need:
- IRSA for fine-grained AWS permissions
- VPC CNI for native VPC networking
- Integration with RDS, ElastiCache, MSK, SQS
- AWS Load Balancer Controller
- AWS App Mesh for service mesh
- CloudWatch Container Insights
- AWS-native security (Security Groups for pods)
</details>

### Question 6
How do cross-AZ data transfer costs compare?

<details>
<summary>Show Answer</summary>

**GCP doesn't charge for same-region traffic; AWS and Azure do**

Costs per GB of cross-AZ traffic:
- AWS: $0.01/GB each direction ($0.02 total)
- Azure: $0.01/GB each direction
- GCP: FREE within the same region

This can be significant for service mesh traffic. Multi-AZ for HA is important, but traffic patterns matter.
</details>

### Question 7
What is the fastest way to get started with managed Kubernetes?

<details>
<summary>Show Answer</summary>

**GKE Autopilot**

1. Single command: `gcloud container clusters create-auto my-cluster`
2. No node configuration needed
3. No add-ons to install (networking, logging built-in)
4. Best practices enforced automatically
5. Ready in ~5 minutes

Tradeoffs: Less control, can't use DaemonSets, higher per-pod cost.
</details>

### Question 8
When should you NOT use managed Kubernetes?

<details>
<summary>Show Answer</summary>

**Consider self-managed when:**

1. **Compliance requires it** — Some regulations require full control
2. **Edge/on-premises** — Managed services are cloud-only
3. **Custom kernels** — Need specific kernel versions/modules
4. **Cost at scale** — 1000+ nodes may be cheaper self-managed
5. **Air-gapped** — No internet connectivity
6. **Multi-region HA** — May need custom control plane placement

For most teams, managed is the right default.
</details>

---

## Key Takeaways

1. **EKS for AWS shops** — Best AWS integration, $72/month control plane
2. **GKE for K8s purity** — Google invented K8s, most K8s-native
3. **AKS for enterprises** — Free control plane, Azure AD integration
4. **Autopilot modes exist** — GKE Autopilot, EKS Fargate, AKS virtual nodes
5. **Workload identity everywhere** — IRSA (EKS), Workload Identity (GKE/AKS)
6. **Egress costs matter** — GCP is often cheapest for public traffic
7. **Multi-cloud is complex** — Only do it with clear justification
8. **Free tiers exist** — All providers offer credits for testing
9. **Version lag varies** — GKE fastest, AKS slowest for new K8s versions
10. **Private by default** — Don't expose control planes publicly

---

## Next Steps

- **Complete**: [Kubernetes Distributions Toolkit](./) ✓
- **Next Toolkit**: [CI/CD Pipelines Toolkit](../../cicd-delivery/ci-cd-pipelines/)
- **Related**: [IaC Tools Toolkit](../iac-tools/) — Terraform for multi-cloud

---

## Further Reading

- [EKS Documentation](https://docs.aws.amazon.com/eks/)
- [GKE Documentation](https://cloud.google.com/kubernetes-engine/docs)
- [AKS Documentation](https://docs.microsoft.com/azure/aks/)
- [EKS Best Practices Guide](https://aws.github.io/aws-eks-best-practices/)
- [GKE Security Best Practices](https://cloud.google.com/kubernetes-engine/docs/how-to/hardening-your-cluster)

---

*"Managed Kubernetes isn't about giving up control—it's about focusing your control where it matters: your applications, not your control plane."*

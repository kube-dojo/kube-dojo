---
title: "Module 5.1: EKS Architecture & Control Plane"
slug: cloud/eks-deep-dive/module-5.1-eks-architecture
sidebar:
  order: 2
---
**Complexity**: [MEDIUM] | **Time to Complete**: 2.5h | **Prerequisites**: AWS Essentials, Cloud Architecture Patterns

## Why This Module Matters

In December 2021, a Series C fintech startup running 340 microservices on Amazon EKS experienced a cascading failure that took down their entire payment processing platform for nearly four hours. The root cause was not a bug in their code. It was not a misconfigured Kubernetes manifest. The engineering team had deployed their EKS cluster with a public API server endpoint and no private endpoint. When a regional AWS API throttling event occurred, their worker nodes -- running in private subnets -- could not reach the Kubernetes API server through the NAT Gateway because the NAT Gateway itself was overwhelmed by unrelated outbound traffic from a data pipeline that had gone haywire. Nodes lost contact with the control plane, pods were evicted, and the entire fleet entered a crash loop. A private endpoint configuration would have kept node-to-control-plane traffic entirely within the VPC, completely bypassing the NAT Gateway and the public internet.

This story illustrates a fundamental truth about EKS: the control plane is managed by AWS, but how you connect to it, how your nodes register with it, and how you authenticate to it are entirely your responsibility. Getting these architectural decisions wrong does not just create inconveniences -- it creates single points of failure that can take down production workloads for hours.

In this module, you will learn how the EKS control plane actually works under the hood, how to choose between public, private, and dual-stack API endpoints, when to use Managed Node Groups versus self-managed nodes versus Fargate, how EKS Add-ons simplify component lifecycle management, and how to migrate from the legacy `aws-auth` ConfigMap to the modern EKS Access Entries system.

---

## EKS Control Plane Architecture

When you create an EKS cluster, AWS provisions a highly available Kubernetes control plane that you never directly see or SSH into. Understanding what happens behind the curtain is essential for making informed architectural decisions.

### What AWS Manages For You

The EKS control plane consists of at least two API server instances and three etcd nodes, spread across three Availability Zones in the AWS-owned account. You do not pay for this infrastructure directly -- it is included in the $0.10/hour cluster fee.

```text
┌─────────────────────────────────────────────────────────────────┐
│                    AWS-Managed Account                          │
│                                                                 │
│   AZ-1a              AZ-1b              AZ-1c                  │
│  ┌──────────┐      ┌──────────┐      ┌──────────┐             │
│  │ API      │      │ API      │      │          │             │
│  │ Server   │      │ Server   │      │ (Standby)│             │
│  ├──────────┤      ├──────────┤      ├──────────┤             │
│  │ etcd     │◄────►│ etcd     │◄────►│ etcd     │             │
│  │ (leader) │      │ (follower│      │ (follower│             │
│  └────┬─────┘      └────┬─────┘      └────┬─────┘             │
│       │                 │                 │                    │
│       └─────────────────┼─────────────────┘                    │
│                         │                                      │
│              Cross-Account ENIs                                │
│              (placed in YOUR VPC)                               │
└─────────────────────────┼──────────────────────────────────────┘
                          │
┌─────────────────────────┼──────────────────────────────────────┐
│              Your AWS Account / Your VPC                        │
│                         │                                      │
│              ┌──────────▼──────────┐                           │
│              │  ENI: 10.0.3.15     │  ← Control plane ENI      │
│              │  ENI: 10.0.3.42     │  ← Control plane ENI      │
│              │  (Private Subnets)  │                           │
│              └──────────┬──────────┘                           │
│                         │                                      │
│              ┌──────────▼──────────┐                           │
│              │    Worker Nodes     │                           │
│              │    10.0.10.x        │                           │
│              └─────────────────────┘                           │
└────────────────────────────────────────────────────────────────┘
```

### Cross-Account ENIs: The Bridge

The most important architectural detail in EKS is the **cross-account Elastic Network Interface (ENI)**. When you create an EKS cluster, AWS places ENIs from the managed control plane account into the subnets you specify in your VPC. These ENIs are how the control plane communicates with your worker nodes.

This has critical implications:

- The subnets you provide during cluster creation must have enough free IP addresses for these ENIs
- Security Groups attached to these ENIs control traffic between the control plane and your nodes
- If you delete or modify these ENIs, your cluster will lose control plane connectivity
- The ENIs appear in your account tagged with `kubernetes.io/cluster/<cluster-name>`

```bash
# View the cross-account ENIs in your VPC
aws ec2 describe-network-interfaces \
  --filters "Name=tag:kubernetes.io/cluster/my-cluster,Values=owned" \
  --query 'NetworkInterfaces[*].{ENI:NetworkInterfaceId, SubnetId:SubnetId, PrivateIp:PrivateIpAddress, SG:Groups[0].GroupId}' \
  --output table
```

### The Cluster Security Group

EKS automatically creates a **cluster security group** that is attached to both the cross-account ENIs and your managed node groups. This security group allows unrestricted communication between the control plane and your nodes. You can find it in the cluster details:

```bash
# Retrieve the cluster security group
aws eks describe-cluster --name my-cluster \
  --query 'cluster.resourcesVpcConfig.clusterSecurityGroupId' \
  --output text
```

Do not remove or restrict this security group unless you fully understand the consequences. Misconfiguring it is one of the fastest ways to make your nodes unable to join the cluster.

---

## Cluster Endpoint Access: Public, Private, or Both

The single most consequential architectural decision you make when creating an EKS cluster is how the Kubernetes API server endpoint is exposed. There are three configurations, and each has dramatically different security and connectivity characteristics.

### Public Endpoint Only (Default)

When you create an EKS cluster, the default configuration exposes a public endpoint. The API server gets a public DNS name (e.g., `https://ABCDEF1234.gr7.us-east-1.eks.amazonaws.com`) that resolves to public IP addresses.

```text
┌────────────────────────────────────────┐
│           Public Internet              │
│                                        │
│   Developer ──► EKS Public Endpoint    │
│   Laptop        (public IP)            │
│                     │                  │
│                     ▼                  │
│              ┌─────────────┐           │
│              │ EKS Control │           │
│              │ Plane       │           │
│              └──────┬──────┘           │
│                     │                  │
│         Cross-Account ENIs             │
│                     │                  │
│              ┌──────▼──────┐           │
│              │ Worker Nodes│           │
│              │ (Private)   │           │
│              └─────────────┘           │
└────────────────────────────────────────┘

Traffic path for kubelet → API server:
  Node → NAT Gateway → Internet → Public Endpoint → Control Plane
```

**The problem**: Your worker nodes in private subnets must traverse the NAT Gateway and the public internet to reach the API server. This adds latency, costs money (NAT data processing fees), and creates a dependency on the NAT Gateway. If your NAT Gateway is overwhelmed or fails, your nodes lose contact with the control plane.

You can restrict the public endpoint using CIDR allowlists:

```bash
aws eks update-cluster-config --name my-cluster \
  --resources-vpc-config \
    endpointPublicAccess=true,\
    publicAccessCidrs='["203.0.113.0/24","198.51.100.0/24"]'
```

### Private Endpoint Only

With a private endpoint, the API server DNS resolves to the private IP addresses of the cross-account ENIs inside your VPC. No public endpoint exists.

```text
┌────────────────────────────────────────┐
│              Your VPC                  │
│                                        │
│   Bastion ──► ENI (10.0.3.15) ──► Control Plane │
│   Host                                 │
│                                        │
│   Worker Nodes ──► ENI (10.0.3.15) ──► Control Plane │
│   (10.0.10.x)     (stays in VPC!)     │
│                                        │
│   Developer (laptop) ──► CANNOT REACH  │
│   (unless VPN/Direct Connect)          │
└────────────────────────────────────────┘

Traffic path for kubelet → API server:
  Node → ENI → Control Plane (never leaves VPC)
```

**Advantages**: Node-to-control-plane traffic stays entirely within the VPC. No NAT Gateway dependency for Kubernetes operations. No public attack surface.

**Challenge**: You cannot run `kubectl` from your laptop unless you are connected to the VPC via VPN, Direct Connect, or a bastion host. CI/CD pipelines must also run inside the VPC or have network connectivity to it.

```bash
aws eks update-cluster-config --name my-cluster \
  --resources-vpc-config \
    endpointPublicAccess=false,\
    endpointPrivateAccess=true
```

### Public + Private (Recommended for Production)

The best-practice configuration enables both endpoints. Nodes use the private endpoint (traffic stays in VPC), while developers and CI/CD pipelines can use the public endpoint (optionally restricted by CIDR).

```text
┌────────────────────────────────────────┐
│              Your VPC                  │
│                                        │
│   Worker Nodes ──► ENI (private)  ──► Control Plane │
│   (stays in VPC, no NAT needed)        │
│                                        │
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│           Public Internet              │
│                                        │
│   Developer ──► Public Endpoint   ──► Control Plane │
│   (CIDR restricted)                    │
└────────────────────────────────────────┘
```

```bash
aws eks update-cluster-config --name my-cluster \
  --resources-vpc-config \
    endpointPublicAccess=true,\
    endpointPrivateAccess=true,\
    publicAccessCidrs='["203.0.113.0/24"]'
```

### Endpoint Decision Matrix

| Configuration | Node Traffic Path | kubectl Access | Security | NAT Dependency |
| :--- | :--- | :--- | :--- | :--- |
| Public only | Node -> NAT -> Internet -> API | Anywhere | Lowest | Yes (critical path) |
| Private only | Node -> ENI -> API (VPC internal) | VPN/bastion only | Highest | No |
| Public + Private | Node -> ENI -> API (VPC internal) | Anywhere (CIDR restrict) | High | No |

*War Story: The fintech failure described in the opening was exactly the "public only" pattern. When they switched to public + private with CIDR restrictions, their node fleet became completely independent of NAT Gateway health for control plane communication. The same data pipeline explosion that previously caused a four-hour outage became a non-event the next time it happened -- nodes never noticed because they were talking to the control plane through the private ENIs.*

---

## Compute Options: Managed Node Groups vs. Self-Managed vs. Fargate

EKS gives you three fundamentally different ways to run your workloads. Each maps to a different point on the control-vs-flexibility spectrum.

### Managed Node Groups

Managed Node Groups (MNGs) are the default and most common choice. AWS manages the EC2 instances lifecycle -- provisioning, AMI updates, draining, and termination -- while you control the instance type, scaling parameters, and labels.

```bash
# Create a managed node group
aws eks create-nodegroup \
  --cluster-name my-cluster \
  --nodegroup-name standard-workers \
  --node-role arn:aws:iam::123456789012:role/EKSNodeRole \
  --subnets subnet-aaa111 subnet-bbb222 \
  --instance-types m6i.xlarge m6a.xlarge m5.xlarge \
  --scaling-config minSize=2,maxSize=10,desiredSize=3 \
  --capacity-type ON_DEMAND \
  --ami-type AL2023_x86_64_STANDARD \
  --labels environment=production,team=platform
```

Key features of MNGs:

- **Graceful updates**: When you update the AMI or instance type, MNGs cordon and drain nodes one by one, respecting PodDisruptionBudgets
- **Multiple instance types**: Specify a list and MNGs will use the cheapest available (critical for Spot)
- **Automatic scaling**: Integrates with Cluster Autoscaler or Karpenter
- **Launch templates**: Customize with user data, additional security groups, or custom AMIs via launch templates

### Self-Managed Node Groups

Self-managed nodes are EC2 instances you provision yourself (usually via an Auto Scaling Group and a Launch Template) and register with the EKS cluster using the bootstrap script.

```bash
#!/bin/bash
# User data script for self-managed nodes
/etc/eks/bootstrap.sh my-cluster \
  --kubelet-extra-args '--node-labels=workload=gpu --register-with-taints=nvidia.com/gpu=:NoSchedule' \
  --container-runtime containerd
```

When to use self-managed nodes:

- You need a custom AMI with pre-baked software (e.g., GPU drivers, compliance agents)
- You require instance types not yet supported by MNGs
- You need Windows nodes with specific configurations
- You want full control over the update/drain process

The trade-off is clear: you own the entire lifecycle, including security patches, AMI updates, and drain orchestration.

### AWS Fargate

Fargate provides serverless compute for Kubernetes pods. You define a **Fargate Profile** that specifies which pods (by namespace and labels) should run on Fargate. When a matching pod is scheduled, AWS provisions a dedicated microVM for it.

```bash
# Create a Fargate profile
aws eks create-fargate-profile \
  --cluster-name my-cluster \
  --fargate-profile-name backend-services \
  --pod-execution-role-arn arn:aws:iam::123456789012:role/EKSFargatePodRole \
  --subnets subnet-aaa111 subnet-bbb222 \
  --selectors '[{"namespace":"backend","labels":{"compute":"fargate"}}]'
```

Fargate characteristics:

- **No nodes to manage**: No patching, no AMI updates, no SSH access
- **Per-pod isolation**: Each pod runs in its own Firecracker microVM
- **Cold start**: Pods take 30-90 seconds longer to start compared to node-based scheduling
- **Limitations**: No DaemonSets, no privileged containers, no GPUs, no persistent local storage
- **Cost**: Typically 20-40% more expensive than equivalent EC2 for sustained workloads, but eliminates operational overhead

### Compute Decision Matrix

| Feature | Managed Node Groups | Self-Managed Nodes | Fargate |
| :--- | :--- | :--- | :--- |
| **AMI updates** | AWS-managed (rolling) | You manage | N/A (serverless) |
| **DaemonSets** | Yes | Yes | No |
| **GPU support** | Yes | Yes | No |
| **Spot instances** | Yes | Yes | No |
| **Startup time** | Seconds (node exists) | Seconds (node exists) | 30-90s cold start |
| **SSH access** | Optional | Yes | No |
| **Cost model** | EC2 pricing | EC2 pricing | Per-pod vCPU+memory/sec |
| **Best for** | Most workloads | Custom/GPU/special | Batch, burstable, low-ops |

Most production clusters use a hybrid approach: Managed Node Groups for the core workload, with Fargate profiles for specific namespaces that benefit from serverless isolation (like batch jobs or tenant-isolated services).

---

## EKS Add-ons: Managed Component Lifecycle

Every Kubernetes cluster needs certain components to function: a CNI plugin for networking, a DNS service for service discovery, and a kube-proxy for Service routing. EKS Add-ons provide a managed way to install, configure, and update these components.

### Why Add-ons Matter

Before EKS Add-ons, teams installed these components using Helm charts or raw manifests. This led to version drift, forgotten upgrades, and configuration inconsistencies. EKS Add-ons solve this by:

- Tracking compatible versions for your cluster's Kubernetes version
- Providing one-click (or one-API-call) upgrades
- Preserving your custom configuration during updates
- Surfacing health status in the EKS console and API

### Core Add-ons

```bash
# List available add-ons and their versions
aws eks describe-addon-versions \
  --kubernetes-version 1.32 \
  --query 'addons[*].{Name:addonName, Latest:addonVersions[0].addonVersion}' \
  --output table
```

The essential add-ons for any EKS cluster:

| Add-on | Purpose | Default? |
| :--- | :--- | :--- |
| `vpc-cni` | Pod networking (assigns VPC IPs to pods) | Yes |
| `coredns` | Cluster DNS resolution | Yes |
| `kube-proxy` | Kubernetes Service routing rules | Yes |
| `eks-pod-identity-agent` | Pod Identity credential injection | No (but recommended) |
| `aws-ebs-csi-driver` | EBS volume provisioning | No (required for EBS PVs) |
| `aws-efs-csi-driver` | EFS volume provisioning | No (required for EFS PVs) |
| `aws-mountpoint-s3-csi-driver` | S3 mount as filesystem | No |
| `adot` | AWS Distro for OpenTelemetry | No |
| `amazon-cloudwatch-observability` | Container Insights | No |

### Installing and Updating Add-ons

```bash
# Install the EBS CSI driver add-on
aws eks create-addon \
  --cluster-name my-cluster \
  --addon-name aws-ebs-csi-driver \
  --addon-version v1.38.1-eksbuild.2 \
  --service-account-role-arn arn:aws:iam::123456789012:role/EBS-CSI-DriverRole \
  --resolve-conflicts OVERWRITE

# Check add-on status
aws eks describe-addon \
  --cluster-name my-cluster \
  --addon-name aws-ebs-csi-driver \
  --query 'addon.{Name:addonName, Version:addonVersion, Status:status, Health:health.issues}'

# Update an add-on
aws eks update-addon \
  --cluster-name my-cluster \
  --addon-name vpc-cni \
  --addon-version v1.19.2-eksbuild.1 \
  --resolve-conflicts PRESERVE
```

The `--resolve-conflicts` flag is important:

- `NONE`: Fail if your custom configuration conflicts with the add-on defaults
- `OVERWRITE`: Replace any custom configuration with add-on defaults
- `PRESERVE`: Keep your custom configuration and only update what the add-on manages

For production, always use `PRESERVE` unless you specifically want to reset to defaults.

---

## Authentication: From aws-auth to EKS Access Entries

How do humans and services authenticate to an EKS cluster? This is one of the most confusing aspects of EKS, and it has undergone a major transformation. Understanding both the legacy and modern systems is essential because you will encounter both in production.

### The Legacy System: aws-auth ConfigMap

For years, EKS used a ConfigMap called `aws-auth` in the `kube-system` namespace to map AWS IAM principals (users, roles) to Kubernetes RBAC identities. This was always a fragile arrangement.

```yaml
# The legacy aws-auth ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: aws-auth
  namespace: kube-system
data:
  mapRoles: |
    - rolearn: arn:aws:iam::123456789012:role/EKSNodeRole
      username: system:node:{{EC2PrivateDNSName}}
      groups:
        - system:bootstrappers
        - system:nodes
    - rolearn: arn:aws:iam::123456789012:role/DevTeamRole
      username: dev-user
      groups:
        - dev-namespace-admin
  mapUsers: |
    - userarn: arn:aws:iam::123456789012:user/admin
      username: cluster-admin
      groups:
        - system:masters
```

Problems with `aws-auth`:

1. **Single point of failure**: One YAML syntax error in this ConfigMap locks everyone out of the cluster (except the cluster creator)
2. **No audit trail**: Changes to a ConfigMap are not logged in AWS CloudTrail
3. **Race conditions**: Multiple engineers editing simultaneously can overwrite each other's changes
4. **No API management**: You cannot manage it through the AWS API -- only through `kubectl`
5. **Easy to break**: A misplaced space in YAML can corrupt the entire mapping

*War Story: A platform team lost cluster access for six hours after a junior engineer ran `kubectl edit configmap aws-auth -n kube-system` and accidentally deleted the `mapRoles` section entirely. All nodes lost their RBAC bindings and began reporting `Unauthorized`. The only recovery path was to use the cluster creator's IAM credentials (which had been rotated months ago) to restore the ConfigMap. They implemented GitOps for the aws-auth ConfigMap the next day, but the real fix was migrating to Access Entries.*

### The Modern System: EKS Access Entries

Introduced in late 2023, EKS Access Entries move authentication configuration out of a fragile ConfigMap and into the EKS API itself. This means you manage access using AWS API calls, with CloudTrail logging, IAM policy guardrails, and no risk of YAML-induced lockouts.

```bash
# Create an access entry for an IAM role
aws eks create-access-entry \
  --cluster-name my-cluster \
  --principal-arn arn:aws:iam::123456789012:role/DevTeamRole \
  --type STANDARD

# Associate an access policy (predefined RBAC)
aws eks associate-access-policy \
  --cluster-name my-cluster \
  --principal-arn arn:aws:iam::123456789012:role/DevTeamRole \
  --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonEKSViewPolicy \
  --access-scope type=namespace,namespaces=dev,staging
```

### Access Policy Types

EKS provides several predefined access policies that map to common Kubernetes RBAC configurations:

| Access Policy | Equivalent RBAC | Scope |
| :--- | :--- | :--- |
| `AmazonEKSClusterAdminPolicy` | `cluster-admin` ClusterRole | Cluster-wide |
| `AmazonEKSAdminPolicy` | `admin` ClusterRole | Namespace or cluster |
| `AmazonEKSEditPolicy` | `edit` ClusterRole | Namespace or cluster |
| `AmazonEKSViewPolicy` | `view` ClusterRole | Namespace or cluster |

### Authentication Modes

EKS clusters support three authentication modes:

```bash
# Check current authentication mode
aws eks describe-cluster --name my-cluster \
  --query 'cluster.accessConfig.authenticationMode'
```

| Mode | aws-auth | Access Entries | Migration Path |
| :--- | :--- | :--- | :--- |
| `CONFIG_MAP` | Active | Disabled | Legacy only |
| `API_AND_CONFIG_MAP` | Active | Active | Transitional (recommended first step) |
| `API` | Disabled | Active | Target state |

### Migration Path: aws-auth to Access Entries

The migration is non-destructive and can be done incrementally:

```bash
# Step 1: Switch to API_AND_CONFIG_MAP mode (both systems active)
aws eks update-cluster-config --name my-cluster \
  --access-config authenticationMode=API_AND_CONFIG_MAP

# Step 2: Create access entries for all existing aws-auth mappings
# For each role in your aws-auth ConfigMap:
aws eks create-access-entry \
  --cluster-name my-cluster \
  --principal-arn arn:aws:iam::123456789012:role/DevTeamRole \
  --type STANDARD

aws eks associate-access-policy \
  --cluster-name my-cluster \
  --principal-arn arn:aws:iam::123456789012:role/DevTeamRole \
  --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonEKSEditPolicy \
  --access-scope type=namespace,namespaces=dev

# Step 3: Test that access works through the new system
# (Users should be able to authenticate without aws-auth)

# Step 4: Once verified, switch to API-only mode
aws eks update-cluster-config --name my-cluster \
  --access-config authenticationMode=API

# Step 5: Clean up the aws-auth ConfigMap
k delete configmap aws-auth -n kube-system
```

> **Important**: You cannot go backwards. Once you switch from `API_AND_CONFIG_MAP` to `API`, you cannot re-enable the ConfigMap. Test thoroughly in the transitional mode before making the final switch.

---

## Did You Know?

1. The EKS control plane runs in an AWS-owned account, not yours. The $0.10/hour cluster fee covers at least two API server instances and three etcd nodes spread across three Availability Zones. AWS auto-scales the control plane based on the number of nodes and API request rate -- you never need to "right-size" the control plane. A cluster with 5 nodes and one with 5,000 nodes both cost $0.10/hour for the control plane itself.

2. The cross-account ENIs that EKS places in your VPC use IP addresses from your subnet CIDR range. Each ENI consumes one IP address per subnet. If you create a cluster with 2 subnets, you lose 2 IPs to control plane ENIs. In tightly sized subnets (like a `/28` with only 11 usable IPs), this can matter. AWS recommends subnets with at least a `/24` (251 usable IPs) for EKS.

3. When you enable the private endpoint, EKS creates a Route 53 private hosted zone associated with your VPC. The cluster's DNS name (e.g., `ABCDEF1234.gr7.us-east-1.eks.amazonaws.com`) resolves to the private ENI IP addresses when queried from within the VPC, and to the public IP addresses when queried from the internet. This split-horizon DNS is automatic and invisible to most users.

4. The original `aws-auth` ConfigMap was created as a "temporary" solution in 2018 when EKS launched. It took AWS over five years to replace it with Access Entries. During those five years, the `aws-auth` ConfigMap became the single most common cause of EKS cluster lockouts, with AWS Support handling thousands of recovery tickets per quarter. The lesson: temporary solutions in infrastructure have a habit of becoming permanent.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
| :--- | :--- | :--- |
| **Public endpoint only with no CIDR restriction** | It is the default configuration and "just works" for getting started. | Enable the private endpoint and add CIDR allowlists to the public endpoint. At minimum, restrict to your corporate IP ranges. |
| **Deleting or modifying cross-account ENIs** | Engineers see unfamiliar ENIs in their VPC and clean them up. | Tag-based policies to prevent deletion. Educate the team that ENIs tagged `kubernetes.io/cluster/<name>` are critical infrastructure. |
| **Editing aws-auth ConfigMap without backup** | Quick changes under pressure. One typo and the entire cluster is inaccessible. | Migrate to Access Entries. If still using aws-auth, always `kubectl get configmap aws-auth -n kube-system -o yaml > aws-auth-backup.yaml` before editing. |
| **Using a single node group for all workloads** | Simplicity bias. One size fits all seems easier to manage. | Create purpose-specific node groups: general (m-type), memory-optimized (r-type), compute (c-type). Use node selectors and taints to route pods correctly. |
| **Fargate for DaemonSet-dependent workloads** | Not understanding Fargate limitations before choosing it. | Check if your workloads need DaemonSets (logging agents, monitoring, service mesh sidecars). If yes, use MNGs or self-managed nodes for those workloads. |
| **Not setting up the EKS Pod Identity agent** | Assuming IRSA is sufficient, not knowing the newer option exists. | Install the `eks-pod-identity-agent` add-on. Pod Identity is simpler to configure and eliminates OIDC provider management. See Module 5.3 for the full migration. |
| **Forgetting to update add-ons after cluster upgrade** | Upgrading the Kubernetes version but leaving add-ons on old versions. | After every cluster version upgrade, check and update all add-ons to compatible versions. Incompatible add-on versions can cause networking or DNS failures. |
| **Cluster subnets too small** | Using `/28` or `/27` subnets for EKS without accounting for ENI consumption. | Use at least `/24` subnets for EKS clusters. Account for cross-account ENIs, pod IPs (VPC CNI), and node IPs. |

---

## Quiz

<details>
<summary>Question 1: Your EKS cluster has both public and private endpoints enabled. A worker node in a private subnet needs to communicate with the Kubernetes API server. Which endpoint does it use, and why does this matter for cost?</summary>

The worker node uses the **private endpoint** via the cross-account ENIs inside the VPC. The cluster DNS name resolves to the private ENI IP addresses when queried from within the VPC (split-horizon DNS). This matters for cost because the traffic stays entirely within the VPC and does not traverse the NAT Gateway. With a public-only endpoint, the same traffic would go through the NAT Gateway, incurring data processing charges ($0.045/GB) and creating a dependency on NAT Gateway availability.
</details>

<details>
<summary>Question 2: You are migrating from aws-auth to EKS Access Entries. Can you switch directly from CONFIG_MAP mode to API mode?</summary>

**No.** You must first transition to `API_AND_CONFIG_MAP` mode, which enables both systems simultaneously. In this transitional mode, you create Access Entries for all your existing IAM-to-Kubernetes mappings and verify they work correctly. Only after thorough testing should you switch to `API` mode. This is a one-way migration -- once you move to `API` mode, you cannot re-enable the ConfigMap. Skipping the transitional step risks locking users out of the cluster.
</details>

<details>
<summary>Question 3: What happens if you accidentally delete the cross-account ENIs that EKS places in your VPC?</summary>

Deleting the cross-account ENIs severs the network connection between the EKS control plane (in the AWS-managed account) and your worker nodes. Nodes will be unable to reach the API server, kubelet will stop receiving pod scheduling instructions, and existing pods will continue running but cannot be managed. The cluster will appear healthy in the EKS console (the control plane is fine), but `kubectl` commands through the private endpoint will time out. AWS will eventually re-create the ENIs, but the disruption can last several minutes. To prevent this, implement IAM policies that deny `ec2:DeleteNetworkInterface` on ENIs tagged with `kubernetes.io/cluster`.
</details>

<details>
<summary>Question 4: A team wants zero-operational-overhead Kubernetes. They plan to run their entire application (15 microservices) on Fargate. Their architecture includes a Datadog agent DaemonSet, Istio service mesh, and a Redis StatefulSet with local SSD storage. Will this work?</summary>

**No, this will not work.** Fargate does not support DaemonSets (so the Datadog agent cannot run), does not support privileged containers (required by some Istio components), and does not provide local persistent storage (Redis with local SSD is not possible). The team should use Managed Node Groups for the core workload and potentially use Fargate for specific stateless microservices that do not depend on DaemonSets. A sidecar-based approach for Datadog (injected per-pod) could work on Fargate, but it significantly increases resource consumption.
</details>

<details>
<summary>Question 5: You upgrade your EKS cluster from Kubernetes 1.31 to 1.32, but pods start failing DNS resolution. What is the likely cause?</summary>

The most likely cause is that the **CoreDNS add-on was not updated** after the cluster upgrade. When you upgrade the Kubernetes version, add-ons are not automatically updated. If the CoreDNS version becomes incompatible with the new Kubernetes version, DNS resolution can fail or degrade. The fix is to update the CoreDNS add-on to a version compatible with Kubernetes 1.32 using `aws eks update-addon --cluster-name my-cluster --addon-name coredns --addon-version <compatible-version>`. Always update all add-ons immediately after a cluster version upgrade.
</details>

<details>
<summary>Question 6: What is the difference between the "cluster security group" and "additional security groups" in EKS?</summary>

The **cluster security group** is automatically created by EKS and attached to both the cross-account ENIs (control plane side) and managed node groups. It allows unrestricted communication between the control plane and nodes. You should not modify or delete it. **Additional security groups** are ones you optionally specify during cluster creation -- they are attached only to the cross-account ENIs, not to nodes. They provide extra control over what non-node traffic (like from a bastion host) can reach the control plane ENIs. In practice, the cluster security group handles node-to-control-plane traffic, while additional security groups handle everything else.
</details>

<details>
<summary>Question 7: Your company requires that the Kubernetes API server is never accessible from the public internet. However, your CI/CD pipeline runs on GitHub Actions (outside your VPC). How can you satisfy both requirements?</summary>

Enable only the **private endpoint** on the EKS cluster, then establish connectivity from GitHub Actions to your VPC. Options include: (1) Run GitHub Actions self-hosted runners inside your VPC on EC2 instances, (2) Use AWS PrivateLink with a VPC endpoint service to expose the cluster API through a private channel, (3) Set up a site-to-site VPN between GitHub's network and your VPC (GitHub supports OIDC but not VPN natively, so self-hosted runners are the most common approach). The key insight is that "private endpoint only" means you must bring your CI/CD compute into the VPC, not expose the cluster to the internet.
</details>

---

## Hands-On Exercise: Private Endpoint Cluster with Bastion and Access Entries Migration

In this exercise, you will create a production-grade EKS cluster with a private endpoint, set up a bastion host for access, and migrate authentication from `aws-auth` to EKS Access Entries.

**What you will build:**

```text
┌────────────────────────────────────────────────────────────────┐
│  VPC: 10.0.0.0/16                                              │
│                                                                │
│  ┌────── Public Subnet (10.0.1.0/24) ──────┐                  │
│  │  Bastion Host (SSM-enabled)              │                  │
│  │  NAT Gateway                             │                  │
│  └──────────────────────────────────────────┘                  │
│                                                                │
│  ┌────── Private Subnet (10.0.10.0/24) ────┐                  │
│  │  EKS Control Plane ENIs                  │                  │
│  │  Managed Node Group (2x m6i.large)       │                  │
│  └──────────────────────────────────────────┘                  │
│                                                                │
│  ┌────── Private Subnet (10.0.20.0/24) ────┐                  │
│  │  EKS Control Plane ENIs                  │                  │
│  │  Managed Node Group (2x m6i.large)       │                  │
│  └──────────────────────────────────────────┘                  │
│                                                                │
│  Endpoint: Private only                                        │
│  Auth: Access Entries (API mode)                               │
└────────────────────────────────────────────────────────────────┘
```

### Task 1: Create the VPC Infrastructure

Set up the networking foundation for the private cluster.

<details>
<summary>Solution</summary>

```bash
# Create VPC
VPC_ID=$(aws ec2 create-vpc --cidr-block 10.0.0.0/16 --query 'Vpc.VpcId' --output text)
aws ec2 create-tags --resources $VPC_ID --tags Key=Name,Value=EKS-Private-VPC
aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-hostnames '{"Value":true}'
aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-support '{"Value":true}'

# Create subnets
PUB_SUB=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.1.0/24 \
  --availability-zone us-east-1a --query 'Subnet.SubnetId' --output text)
PRIV_SUB1=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.10.0/24 \
  --availability-zone us-east-1a --query 'Subnet.SubnetId' --output text)
PRIV_SUB2=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.20.0/24 \
  --availability-zone us-east-1b --query 'Subnet.SubnetId' --output text)

# Tag subnets for EKS
aws ec2 create-tags --resources $PUB_SUB --tags Key=Name,Value=Public-Subnet
aws ec2 create-tags --resources $PRIV_SUB1 --tags Key=Name,Value=Private-Subnet-AZ1 \
  Key=kubernetes.io/role/internal-elb,Value=1
aws ec2 create-tags --resources $PRIV_SUB2 --tags Key=Name,Value=Private-Subnet-AZ2 \
  Key=kubernetes.io/role/internal-elb,Value=1

# Internet Gateway for public subnet
IGW_ID=$(aws ec2 create-internet-gateway --query 'InternetGateway.InternetGatewayId' --output text)
aws ec2 attach-internet-gateway --vpc-id $VPC_ID --internet-gateway-id $IGW_ID

# Public route table
PUB_RT=$(aws ec2 create-route-table --vpc-id $VPC_ID --query 'RouteTable.RouteTableId' --output text)
aws ec2 create-route --route-table-id $PUB_RT --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW_ID
aws ec2 associate-route-table --subnet-id $PUB_SUB --route-table-id $PUB_RT
aws ec2 modify-subnet-attribute --subnet-id $PUB_SUB --map-public-ip-on-launch

# NAT Gateway for private subnets
EIP_ALLOC=$(aws ec2 allocate-address --domain vpc --query 'AllocationId' --output text)
NAT_ID=$(aws ec2 create-nat-gateway --subnet-id $PUB_SUB --allocation-id $EIP_ALLOC \
  --query 'NatGateway.NatGatewayId' --output text)
aws ec2 wait nat-gateway-available --nat-gateway-ids $NAT_ID

# Private route table
PRIV_RT=$(aws ec2 create-route-table --vpc-id $VPC_ID --query 'RouteTable.RouteTableId' --output text)
aws ec2 create-route --route-table-id $PRIV_RT --destination-cidr-block 0.0.0.0/0 --nat-gateway-id $NAT_ID
aws ec2 associate-route-table --subnet-id $PRIV_SUB1 --route-table-id $PRIV_RT
aws ec2 associate-route-table --subnet-id $PRIV_SUB2 --route-table-id $PRIV_RT

echo "VPC: $VPC_ID | Public: $PUB_SUB | Private: $PRIV_SUB1, $PRIV_SUB2"
```

</details>

### Task 2: Create the EKS Cluster with Private Endpoint

Create the cluster with only the private API endpoint enabled.

<details>
<summary>Solution</summary>

```bash
# Create the EKS cluster role (if not already exists)
cat > /tmp/eks-trust-policy.json << 'POLICY'
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "eks.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
POLICY

EKS_ROLE_ARN=$(aws iam create-role \
  --role-name EKS-Cluster-Role \
  --assume-role-policy-document file:///tmp/eks-trust-policy.json \
  --query 'Role.Arn' --output text)
aws iam attach-role-policy --role-name EKS-Cluster-Role \
  --policy-arn arn:aws:iam::aws:policy/AmazonEKSClusterPolicy

# Create the EKS cluster with private endpoint
aws eks create-cluster \
  --name dojo-private-cluster \
  --role-arn $EKS_ROLE_ARN \
  --resources-vpc-config \
    subnetIds=$PRIV_SUB1,$PRIV_SUB2,\
endpointPublicAccess=false,\
endpointPrivateAccess=true \
  --kubernetes-version 1.32 \
  --access-config authenticationMode=API_AND_CONFIG_MAP

echo "Cluster creation initiated. This takes 10-15 minutes."
aws eks wait cluster-active --name dojo-private-cluster
echo "Cluster is active."
```

</details>

### Task 3: Deploy a Bastion Host with SSM Access

Since the API server is private, you need a way to reach it from within the VPC.

<details>
<summary>Solution</summary>

```bash
# Create an IAM role for the bastion with SSM access
cat > /tmp/bastion-trust.json << 'POLICY'
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "ec2.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
POLICY

aws iam create-role --role-name EKS-Bastion-Role \
  --assume-role-policy-document file:///tmp/bastion-trust.json
aws iam attach-role-policy --role-name EKS-Bastion-Role \
  --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore
aws iam create-instance-profile --instance-profile-name EKS-Bastion-Profile
aws iam add-role-to-instance-profile \
  --instance-profile-name EKS-Bastion-Profile \
  --role-name EKS-Bastion-Role

# Create a security group for the bastion (no inbound SSH needed with SSM)
BASTION_SG=$(aws ec2 create-security-group \
  --group-name Bastion-SG \
  --description "Bastion host - SSM only, no SSH" \
  --vpc-id $VPC_ID \
  --query 'GroupId' --output text)

# Launch the bastion in the public subnet
BASTION_ID=$(aws ec2 run-instances \
  --image-id resolve:ssm:/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-6.1-x86_64 \
  --instance-type t3.small \
  --subnet-id $PUB_SUB \
  --security-group-ids $BASTION_SG \
  --iam-instance-profile Name=EKS-Bastion-Profile \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=EKS-Bastion}]' \
  --user-data '#!/bin/bash
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl && mv kubectl /usr/local/bin/
curl -LO "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_Linux_amd64.tar.gz"
tar xzf eksctl_Linux_amd64.tar.gz && mv eksctl /usr/local/bin/
' \
  --query 'Instances[0].InstanceId' --output text)

echo "Bastion instance: $BASTION_ID"
echo "Connect via: aws ssm start-session --target $BASTION_ID"
```

</details>

### Task 4: Configure Access Entries for Multiple Teams

Create access entries that give different teams appropriate permissions.

<details>
<summary>Solution</summary>

```bash
CLUSTER_NAME="dojo-private-cluster"

# Grant the bastion role cluster-admin access
aws eks create-access-entry \
  --cluster-name $CLUSTER_NAME \
  --principal-arn arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/EKS-Bastion-Role \
  --type STANDARD

aws eks associate-access-policy \
  --cluster-name $CLUSTER_NAME \
  --principal-arn arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/EKS-Bastion-Role \
  --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy \
  --access-scope type=cluster

# Create a dev team entry with namespace-scoped edit access
aws eks create-access-entry \
  --cluster-name $CLUSTER_NAME \
  --principal-arn arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/DevTeamRole \
  --type STANDARD

aws eks associate-access-policy \
  --cluster-name $CLUSTER_NAME \
  --principal-arn arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/DevTeamRole \
  --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonEKSEditPolicy \
  --access-scope type=namespace,namespaces=dev,staging

# Create a read-only entry for the security team
aws eks create-access-entry \
  --cluster-name $CLUSTER_NAME \
  --principal-arn arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/SecurityAuditRole \
  --type STANDARD

aws eks associate-access-policy \
  --cluster-name $CLUSTER_NAME \
  --principal-arn arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/SecurityAuditRole \
  --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonEKSViewPolicy \
  --access-scope type=cluster

# List all access entries
aws eks list-access-entries --cluster-name $CLUSTER_NAME --output table
```

</details>

### Task 5: Complete the Migration to API-Only Authentication

Switch the cluster to use only Access Entries, removing the aws-auth dependency.

<details>
<summary>Solution</summary>

```bash
# Verify all access entries are working by connecting via bastion
aws ssm start-session --target $BASTION_ID

# (On the bastion host)
aws eks update-kubeconfig --name dojo-private-cluster --region us-east-1
kubectl get nodes  # Should return the managed node group nodes
kubectl auth whoami  # Should show the bastion role identity

# Exit the bastion session, then switch to API-only mode
aws eks update-cluster-config \
  --name dojo-private-cluster \
  --access-config authenticationMode=API

# Wait for the update to complete
aws eks wait cluster-active --name dojo-private-cluster

# Verify the authentication mode
aws eks describe-cluster --name dojo-private-cluster \
  --query 'cluster.accessConfig.authenticationMode'
# Expected output: "API"

echo "Migration complete. aws-auth ConfigMap is no longer used."
```

</details>

### Task 6: Verify and Audit the Configuration

Confirm the cluster is correctly configured and document the setup.

<details>
<summary>Solution</summary>

```bash
CLUSTER_NAME="dojo-private-cluster"

# Verify endpoint configuration
aws eks describe-cluster --name $CLUSTER_NAME \
  --query 'cluster.resourcesVpcConfig.{PublicAccess:endpointPublicAccess, PrivateAccess:endpointPrivateAccess, SecurityGroupIds:securityGroupIds, SubnetIds:subnetIds}' \
  --output table

# Verify authentication mode
aws eks describe-cluster --name $CLUSTER_NAME \
  --query 'cluster.accessConfig'

# List all access entries with their policies
for arn in $(aws eks list-access-entries --cluster-name $CLUSTER_NAME --query 'accessEntries[]' --output text); do
  echo "=== $arn ==="
  aws eks list-associated-access-policies \
    --cluster-name $CLUSTER_NAME \
    --principal-arn "$arn" \
    --query 'associatedAccessPolicies[*].{Policy:policyArn, Scope:accessScope.type}' \
    --output table
done

# Check the cross-account ENIs
aws ec2 describe-network-interfaces \
  --filters "Name=tag:kubernetes.io/cluster/$CLUSTER_NAME,Values=owned" \
  --query 'NetworkInterfaces[*].{ENI:NetworkInterfaceId, PrivateIp:PrivateIpAddress, Subnet:SubnetId}' \
  --output table
```

</details>

### Clean Up

```bash
# Delete in reverse order
aws eks delete-nodegroup --cluster-name dojo-private-cluster --nodegroup-name standard-workers
aws eks wait nodegroup-deleted --cluster-name dojo-private-cluster --nodegroup-name standard-workers
aws eks delete-cluster --name dojo-private-cluster
aws eks wait cluster-deleted --name dojo-private-cluster
aws ec2 terminate-instances --instance-ids $BASTION_ID
# Then clean up VPC resources (NAT GW, subnets, IGW, VPC) as in the VPC module
```

### Success Criteria

- [ ] I created an EKS cluster with the private API endpoint only
- [ ] I deployed a bastion host with SSM access (no SSH key required)
- [ ] I connected to the cluster from the bastion using `kubectl`
- [ ] I created Access Entries for three different team roles with appropriate scope
- [ ] I migrated the cluster from `API_AND_CONFIG_MAP` to `API` authentication mode
- [ ] I verified the cross-account ENIs exist in my private subnets
- [ ] I can explain why private endpoint eliminates NAT Gateway dependency for control plane traffic

---

## Next Module

With the EKS architecture foundation in place, it is time to dive deep into how pods get their IP addresses and how traffic flows. Head to [Module 5.2: EKS Networking Deep Dive (VPC CNI)](module-5.2-eks-networking/) to master prefix delegation, IP exhaustion solutions, and the AWS Load Balancer Controller.

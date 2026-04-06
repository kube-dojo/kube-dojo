---
title: "Module 1.2: Cloud Provider Security"
slug: k8s/kcsa/part1-cloud-native-security/module-1.2-cloud-provider-security
sidebar:
  order: 3
---
> **Complexity**: `[MEDIUM]` - Foundational knowledge
>
> **Time to Complete**: 25-30 minutes
>
> **Prerequisites**: [Module 1.1: The 4 Cs of Cloud Native Security](../module-1.1-four-cs/)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Explain** the shared responsibility model and what you own vs. what the cloud provider owns
2. **Evaluate** cloud provider security controls (IAM, VPCs, encryption) relevant to Kubernetes
3. **Assess** the risk of misconfigured cloud-level security boundaries on cluster workloads
4. **Compare** managed Kubernetes (EKS, GKE, AKS) security defaults across providers

---

## Why This Module Matters

Every Kubernetes cluster runs on infrastructure—whether it's AWS, GCP, Azure, or your own data center. The security of that infrastructure is the foundation for everything else. Understanding the shared responsibility model is critical because it defines **what you're responsible for securing** versus what your cloud provider handles.

Misunderstanding this boundary is one of the most common causes of cloud security breaches.

---

## The Shared Responsibility Model

Cloud security is a partnership. You and your cloud provider each have responsibilities:

```
┌─────────────────────────────────────────────────────────────┐
│              SHARED RESPONSIBILITY MODEL                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  "Security OF the cloud" vs "Security IN the cloud"        │
│                                                             │
│  ┌──────────────────────┬────────────────────────────────┐ │
│  │   CLOUD PROVIDER     │         YOU (CUSTOMER)         │ │
│  │   RESPONSIBILITY     │         RESPONSIBILITY         │ │
│  ├──────────────────────┼────────────────────────────────┤ │
│  │                      │                                │ │
│  │  Physical security   │  Data                         │ │
│  │  Hardware            │  Identity & access management  │ │
│  │  Network infra       │  Application configuration    │ │
│  │  Hypervisor          │  Network configuration        │ │
│  │  Compute/storage     │  OS patches (IaaS)            │ │
│  │  Global network      │  Firewall/security groups     │ │
│  │                      │  Encryption choices           │ │
│  │                      │  Client-side data integrity   │ │
│  │                      │                                │ │
│  └──────────────────────┴────────────────────────────────┘ │
│                                                             │
│  The boundary shifts based on service type (IaaS/PaaS)     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

> **Stop and think**: If your company moves from self-managed Kubernetes to EKS, which security tasks can you stop worrying about, and which new responsibilities emerge that didn't exist before?

### How Responsibility Shifts

```
┌─────────────────────────────────────────────────────────────┐
│              RESPONSIBILITY BY SERVICE MODEL                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│              ON-PREM    IaaS      PaaS      SaaS           │
│              ────────   ────      ────      ────           │
│  Data          YOU      YOU       YOU       YOU            │
│  Application   YOU      YOU       YOU       Provider       │
│  Runtime       YOU      YOU       Provider  Provider       │
│  OS            YOU      YOU       Provider  Provider       │
│  Virtualization YOU     Provider  Provider  Provider       │
│  Hardware      YOU      Provider  Provider  Provider       │
│  Network       YOU      Provider  Provider  Provider       │
│  Physical      YOU      Provider  Provider  Provider       │
│                                                             │
│  More managed = less responsibility, but also less control │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Managed Kubernetes Security

Managed Kubernetes services (EKS, GKE, AKS) change the responsibility model:

### What the Provider Manages

```
┌─────────────────────────────────────────────────────────────┐
│              MANAGED KUBERNETES - PROVIDER SCOPE            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CONTROL PLANE                                              │
│  ├── API server availability and patching                  │
│  ├── etcd availability and backups                         │
│  ├── Controller manager                                    │
│  ├── Scheduler                                             │
│  └── Control plane network security                        │
│                                                             │
│  INFRASTRUCTURE                                             │
│  ├── Physical security of data centers                     │
│  ├── Network backbone                                      │
│  ├── Hardware maintenance                                  │
│  └── Hypervisor security                                   │
│                                                             │
│  COMPLIANCE                                                 │
│  ├── SOC 2 Type II                                         │
│  ├── ISO 27001                                             │
│  └── Various regulatory certifications                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### What You Manage

```
┌─────────────────────────────────────────────────────────────┐
│              MANAGED KUBERNETES - YOUR SCOPE                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CLUSTER CONFIGURATION                                      │
│  ├── RBAC policies                                         │
│  ├── Network policies                                      │
│  ├── Pod Security Standards                                │
│  ├── Admission controllers                                 │
│  └── Audit policy configuration                            │
│                                                             │
│  WORKLOADS                                                  │
│  ├── Container images                                      │
│  ├── Pod security contexts                                 │
│  ├── Application configuration                             │
│  └── Secrets management                                    │
│                                                             │
│  WORKER NODES (varies by provider)                         │
│  ├── Node OS security                                      │
│  ├── Node group configuration                              │
│  └── Node patching (often automated)                       │
│                                                             │
│  DATA                                                       │
│  ├── Your application data                                 │
│  ├── Encryption key management                             │
│  └── Backup and recovery                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Default Security Postures: EKS vs. GKE vs. AKS

While all major cloud providers offer managed Kubernetes, their out-of-the-box security defaults differ significantly:

| Security Feature | Amazon EKS | Google GKE | Azure AKS |
|------------------|------------|------------|-----------|
| **API Server Endpoint** | Public by default (can be restricted) | Public by default (Private clusters recommended) | Public by default (Private clusters available) |
| **Node OS** | Amazon Linux 2 / Bottlerocket | Container-Optimized OS (COS) | Ubuntu / Azure Linux |
| **Workload Identity** | IAM Roles for Service Accounts (IRSA/Pod Identity) | Workload Identity (enabled by default on Autopilot) | Microsoft Entra Workload ID |
| **Network Policies** | Requires add-on (e.g., Calico or VPC CNI) | Dataplane V2 (Cilium) built-in | Azure Network Policies or Calico |

> **Pause and predict**: If you provision a default cluster on your chosen provider without specifying security parameters, which critical boundaries (like the API server or pod networking) might be exposed to the public internet or lack internal segmentation?

---

## Cloud IAM for Kubernetes

Identity and Access Management (IAM) is critical for cloud security:

### IAM Fundamentals

```
┌─────────────────────────────────────────────────────────────┐
│              IAM CORE CONCEPTS                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  PRINCIPAL         WHO is requesting access?               │
│  ├── Users         Human identities                        │
│  ├── Groups        Collections of users                    │
│  ├── Roles         Assumable identities                    │
│  └── Service Accts Machine identities                      │
│                                                             │
│  ACTION            WHAT are they trying to do?             │
│  ├── Read          Get, List, Describe                     │
│  ├── Write         Create, Update, Delete                  │
│  └── Admin         Full control, IAM changes               │
│                                                             │
│  RESOURCE          WHICH resource is involved?             │
│  ├── Specific      arn:aws:s3:::my-bucket/file.txt        │
│  ├── Pattern       arn:aws:s3:::my-bucket/*               │
│  └── All           * (dangerous!)                          │
│                                                             │
│  CONDITION         UNDER WHAT circumstances?               │
│  ├── Time-based    Only during business hours             │
│  ├── IP-based      Only from corporate network            │
│  └── MFA-required  Only with second factor                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Kubernetes IAM Integration

Cloud IAM integrates with Kubernetes in two key ways:

```
┌─────────────────────────────────────────────────────────────┐
│              IAM + KUBERNETES INTEGRATION                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. CLUSTER ACCESS                                          │
│     Cloud IAM controls who can access the cluster          │
│                                                             │
│     User → Cloud IAM → API Server → Kubernetes RBAC        │
│                                                             │
│     Example (AWS EKS):                                      │
│     - IAM user/role authenticates to AWS                   │
│     - aws-auth ConfigMap maps IAM to K8s groups            │
│     - RBAC authorizes actions in cluster                   │
│                                                             │
│  2. WORKLOAD IDENTITY                                       │
│     Pods can assume cloud IAM roles                        │
│                                                             │
│     Pod → ServiceAccount → Cloud IAM Role → AWS API        │
│                                                             │
│     Example (GKE Workload Identity):                        │
│     - K8s ServiceAccount annotated with GCP SA             │
│     - Pod automatically gets GCP credentials               │
│     - No static credentials needed                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Worked Example: The IAM Pivot Attack

To understand why workload identity is critical, consider what happens when cloud IAM and Kubernetes boundaries are misconfigured. This is how an attacker turns a minor application bug into a cloud account compromise:

1. **Initial Access**: An attacker exploits a Server-Side Request Forgery (SSRF) vulnerability in your web application pod.
2. **The Over-Permission**: The pod is running on a worker node that was granted an overly permissive IAM instance profile (e.g., `AmazonS3FullAccess`) to read some configuration files.
3. **The Pivot**: Because the pod shares the underlying node's identity, the attacker uses the SSRF vulnerability to query the cloud provider's instance metadata service (e.g., `169.254.169.254`).
4. **Cloud Compromise**: The metadata service returns the node's highly privileged, short-lived IAM credentials. The attacker extracts these credentials and uses them outside the cluster to download sensitive data from entirely unrelated storage buckets in your cloud account.

By implementing strict Workload Identity, the pod would only have an identity scoped exactly to what it needs, and access to the node's metadata service would be blocked, neutralizing the pivot.

> **Pause and predict**: A pod needs to read from an S3 bucket. Your team stores the AWS access key as a Kubernetes Secret. What could go wrong with this approach, and what alternative would be more secure?

### Workload Identity Benefits

Why use workload identity instead of static credentials?

| Static Credentials | Workload Identity |
|-------------------|-------------------|
| Long-lived secrets | Short-lived tokens |
| Stored in cluster | Automatically rotated |
| Same creds for all pods | Per-pod identity |
| Manual rotation | Provider-managed |
| Risk of exposure | Minimal blast radius |

---

## Infrastructure Security Controls

### Network Security

```
┌─────────────────────────────────────────────────────────────┐
│              CLOUD NETWORK SECURITY                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  VPC (Virtual Private Cloud)                               │
│  ├── Isolated network space                                │
│  ├── Your own IP address range                             │
│  └── Foundation for other network controls                 │
│                                                             │
│  SUBNETS                                                    │
│  ├── Public subnets  → Internet-facing resources           │
│  ├── Private subnets → Internal resources                  │
│  └── Control plane   → Often in provider-managed subnet    │
│                                                             │
│  SECURITY GROUPS                                            │
│  ├── Stateful firewalls                                    │
│  ├── Allow rules only (implicit deny)                      │
│  └── Applied to instances/ENIs                             │
│                                                             │
│  NETWORK ACLs                                               │
│  ├── Stateless firewalls                                   │
│  ├── Allow and deny rules                                  │
│  └── Applied to subnets                                    │
│                                                             │
│  Best Practice: Private subnets for worker nodes,          │
│  public only for load balancers if needed                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Encryption

```
┌─────────────────────────────────────────────────────────────┐
│              ENCRYPTION LAYERS                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ENCRYPTION IN TRANSIT                                      │
│  ├── TLS for API server communication                      │
│  ├── TLS between nodes and control plane                   │
│  ├── TLS for etcd peer communication                       │
│  └── Service mesh for pod-to-pod encryption                │
│                                                             │
│  ENCRYPTION AT REST                                         │
│  ├── EBS/disk encryption (provider-managed keys)           │
│  ├── etcd encryption (Kubernetes secrets)                  │
│  ├── Object storage encryption (S3, GCS)                   │
│  └── Customer-managed keys (CMK) for more control          │
│                                                             │
│  KEY MANAGEMENT                                             │
│  ├── Cloud KMS for key storage                             │
│  ├── Envelope encryption pattern                           │
│  ├── Key rotation policies                                 │
│  └── Audit logging of key usage                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Multi-Tenancy Considerations

When multiple teams or applications share infrastructure:

```
┌─────────────────────────────────────────────────────────────┐
│              MULTI-TENANCY ISOLATION LEVELS                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  STRONGEST: Separate Cloud Accounts                        │
│  ├── Complete blast radius isolation                       │
│  ├── Separate IAM boundaries                               │
│  ├── Independent billing                                   │
│  └── Use for: Production vs non-prod, different customers  │
│                                                             │
│  STRONG: Separate Clusters                                  │
│  ├── Cluster-level isolation                               │
│  ├── Separate RBAC                                         │
│  ├── No shared control plane                               │
│  └── Use for: Different security levels, teams             │
│                                                             │
│  MODERATE: Namespace Isolation                              │
│  ├── RBAC per namespace                                    │
│  ├── Network policies between namespaces                   │
│  ├── Resource quotas                                       │
│  └── Use for: Different applications, environments         │
│                                                             │
│  WEAK: Same Namespace (not recommended)                     │
│  └── No isolation between workloads                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **85% of cloud breaches** involve human error—usually misconfigured IAM or exposed storage buckets, not sophisticated attacks.

- **Workload Identity** eliminates the need for static credentials entirely. GKE Workload Identity, EKS IAM Roles for Service Accounts (IRSA), and AKS Workload Identity all implement this pattern.

- **The shared responsibility model** was first popularized by AWS but is now industry-standard across all major cloud providers.

- **Private clusters** (no public API endpoint) are increasingly the default for production Kubernetes deployments, requiring VPN or bastion access.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Assuming cloud provider secures everything | You're responsible for configuration | Know the shared responsibility model |
| Using static credentials for pods | Long-lived secrets can be leaked | Use workload identity |
| Public API server endpoint | Exposed to internet attacks | Use private clusters |
| Overly permissive IAM policies | Blast radius too large | Apply least privilege |
| Not encrypting etcd | Secrets stored in plain text | Enable etcd encryption |

---

## Quiz

1. **During a security review, you discover that a development team has been storing AWS access keys as Kubernetes Secrets to give their pods S3 access. The keys were created 18 months ago and have never been rotated. What risks does this create, and what should replace this approach?**
   <details>
   <summary>Answer</summary>
   This approach creates multiple severe risks because the long-lived static credentials could be leaked through etcd access, RBAC over-permission, backup exposure, or accidental logging. If compromised, the attacker has persistent S3 access until the keys are manually revoked, which is often difficult to detect. The replacement is workload identity (such as AWS IRSA for EKS), where you annotate the Kubernetes ServiceAccount with an IAM role ARN. By doing this, pods automatically receive short-lived, auto-rotated credentials with no static secrets stored in the cluster, completely eliminating key management overhead and limiting the blast radius to a per-pod identity.
   </details>

2. **Your organization uses EKS with a public API server endpoint. A security consultant recommends switching to a private endpoint. What threat does this mitigate, and what operational changes are required?**
   <details>
   <summary>Answer</summary>
   A public endpoint exposes the API server to internet-based attacks, such as brute force authentication attempts, credential stuffing, API exploitation, and unauthorized reconnaissance. Switching to a private endpoint mitigates this by ensuring the API server is only accessible from within your VPC or connected networks. However, this requires operational changes: developers will need VPN or bastion host access to run `kubectl` commands. Furthermore, CI/CD pipelines must run within the VPC or use VPC peering, and monitoring tools will need specific network access to reach the private endpoint.
   </details>

3. **A multi-tenant SaaS platform runs all customer workloads in a single Kubernetes cluster using namespace isolation. A security audit flags this as insufficient. Using the multi-tenancy isolation levels, explain why and suggest alternatives.**
   <details>
   <summary>Answer</summary>
   Namespace isolation is considered a "moderate" strength boundary because it relies entirely on software controls like RBAC, network policies, and resource quotas, while all tenants still share the same control plane and underlying node resources. A vulnerability in the API server or a container escape exploit could allow an attacker to compromise all tenants across the cluster. For stronger isolation, you should implement separate clusters per tenant to provide independent control planes and separate RBAC domains. Alternatively, for the highest security, use separate cloud accounts per tenant to achieve complete blast radius isolation and independent IAM boundaries.
   </details>

4. **Encryption at rest is enabled for your EKS cluster's etcd, but a colleague says "our secrets are safe now." What assumption are they making that could be wrong?**
   <details>
   <summary>Answer</summary>
   They are making the dangerous assumption that encryption at rest is the only protection secrets need, ignoring how Kubernetes actually serves those secrets. Encryption at rest only protects the secrets if the underlying storage media or database backups are physically stolen or improperly exposed. While the cluster is running, secrets are transparently decrypted when read by the API server and are delivered in plaintext to any user or pod with sufficient RBAC permissions. To truly secure secrets, you must minimize RBAC access, utilize external secret managers for rotation, and enable API audit logging to track exactly who or what is accessing them.
   </details>

5. **Your company operates in a hybrid model: some workloads run on-premises and others on GKE. From a shared responsibility perspective, what security tasks differ between these two environments?**
   <details>
   <summary>Answer</summary>
   In an on-premises environment, your team is fully responsible for securing every layer, including physical security, network hardware, the host OS, and the entire Kubernetes control plane. Conversely, on a managed service like GKE, the cloud provider assumes responsibility for physical security, the network backbone, and control plane operations like etcd backups and API server patching. However, in both environments, you remain fully responsible for workload security, RBAC configuration, network policies, and application secrets. The key difference is that managed Kubernetes abstracts away the underlying infrastructure security, allowing your team to focus exclusively on securing the workloads and cluster configurations.
   </details>

---

## Hands-On Exercise: Responsibility Mapping

**Scenario**: You're deploying a new application to managed Kubernetes (e.g., EKS). Classify each security task:

| Security Task | Provider or Customer? |
|--------------|----------------------|
| Patching the Kubernetes API server | ? |
| Creating RBAC roles for developers | ? |
| Enabling etcd encryption | ? |
| Securing physical access to data center | ? |
| Configuring network policies | ? |
| Patching worker node OS | ? |
| Managing your application secrets | ? |
| Ensuring API server high availability | ? |

<details>
<summary>Answers</summary>

| Security Task | Responsibility |
|--------------|----------------|
| Patching the Kubernetes API server | **Provider** - They manage control plane |
| Creating RBAC roles for developers | **Customer** - You configure access |
| Enabling etcd encryption | **Customer** (usually) - You decide encryption settings |
| Securing physical access to data center | **Provider** - Physical security |
| Configuring network policies | **Customer** - You configure workload networking |
| Patching worker node OS | **Customer** (but often automated) |
| Managing your application secrets | **Customer** - Your application data |
| Ensuring API server high availability | **Provider** - Control plane availability |

</details>

---

## Summary

Cloud provider security is about understanding boundaries:

| Concept | Key Points |
|---------|------------|
| **Shared Responsibility** | Provider secures "of the cloud," you secure "in the cloud" |
| **Managed Kubernetes** | Provider handles control plane, you handle workloads |
| **IAM** | Foundation for all cloud access, integrate with Kubernetes |
| **Workload Identity** | Eliminate static credentials for pods |
| **Network Security** | Private subnets, security groups, encryption in transit |
| **Multi-Tenancy** | Account > Cluster > Namespace isolation strength |

Remember: The cloud provider gives you secure building blocks. Assembling them securely is your job.

---

## Next Module

[Module 1.3: Security Principles](../module-1.3-security-principles/) - Defense in depth, least privilege, and other foundational security principles.
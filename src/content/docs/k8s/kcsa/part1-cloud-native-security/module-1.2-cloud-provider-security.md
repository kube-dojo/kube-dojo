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

1. **In the shared responsibility model, who is responsible for Kubernetes RBAC configuration in managed Kubernetes?**
   <details>
   <summary>Answer</summary>
   The customer (you). Cloud providers manage the control plane infrastructure, but you configure how it's used (RBAC, network policies, etc.).
   </details>

2. **What is workload identity?**
   <details>
   <summary>Answer</summary>
   A feature that allows Kubernetes pods to assume cloud IAM roles without static credentials. The pod's ServiceAccount is mapped to a cloud identity, providing short-lived, automatically rotated credentials.
   </details>

3. **Why should worker nodes be in private subnets?**
   <details>
   <summary>Answer</summary>
   To reduce attack surface. Worker nodes don't need direct internet access (they can use NAT for outbound). Private subnets prevent direct inbound access from the internet.
   </details>

4. **What encryption should be enabled for Kubernetes secrets stored in etcd?**
   <details>
   <summary>Answer</summary>
   Encryption at rest for etcd. By default, secrets are base64 encoded but not encrypted. Enabling encryption at rest protects secrets if the etcd storage is compromised.
   </details>

5. **In a multi-tenant environment, what provides the strongest isolation?**
   <details>
   <summary>Answer</summary>
   Separate cloud accounts provide the strongest isolation, with independent IAM boundaries and complete blast radius separation. Separate clusters provide strong isolation within an account.
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

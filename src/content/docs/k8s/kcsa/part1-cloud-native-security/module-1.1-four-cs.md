---
title: "Module 1.1: The 4 Cs of Cloud Native Security"
slug: k8s/kcsa/part1-cloud-native-security/module-1.1-four-cs
sidebar:
  order: 2
---
> **Complexity**: `[MEDIUM]` - Core framework
>
> **Time to Complete**: 25-30 minutes
>
> **Prerequisites**: [Module 0.2: Security Mindset](../part0-introduction/module-0.2-security-mindset/)

---

## Why This Module Matters

The 4 Cs is the foundational mental model for cloud native security. Every security decision in Kubernetes maps back to one of these layers. Master this framework, and you'll have a structured way to think about any security question on the KCSA exam.

The Kubernetes documentation itself uses this model, and it appears directly in exam questions. This isn't just theory—it's the official way to categorize cloud native security.

---

## The 4 Cs Model

```
┌─────────────────────────────────────────────────────────────┐
│                    THE 4 Cs OF SECURITY                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│      Each layer builds on the security of the layer        │
│      below it. A breach at any layer compromises all       │
│      layers above it.                                      │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                     CLOUD                            │   │
│  │  The infrastructure foundation                       │   │
│  │  ┌─────────────────────────────────────────────┐   │   │
│  │  │                  CLUSTER                     │   │   │
│  │  │  Kubernetes components and configuration     │   │   │
│  │  │  ┌─────────────────────────────────────┐   │   │   │
│  │  │  │             CONTAINER               │   │   │   │
│  │  │  │  Image and runtime security         │   │   │   │
│  │  │  │  ┌─────────────────────────────┐   │   │   │   │
│  │  │  │  │           CODE             │   │   │   │   │
│  │  │  │  │  Application security      │   │   │   │   │
│  │  │  │  └─────────────────────────────┘   │   │   │   │
│  │  │  └─────────────────────────────────────┘   │   │   │
│  │  └─────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Security at one layer CANNOT compensate for insecurity    │
│  at a layer below it.                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### The Critical Insight

**You can only be as secure as your weakest layer.**

If your Cloud layer is compromised (someone has your AWS root credentials), it doesn't matter how well you've configured Kubernetes RBAC or container security—the attacker owns everything.

---

## Layer 1: Cloud (Infrastructure)

The outermost layer—your infrastructure foundation.

### What It Includes

| Component | Security Concerns |
|-----------|------------------|
| **Cloud Provider** | AWS, GCP, Azure, on-premises |
| **Compute** | VMs, bare metal servers |
| **Network** | VPCs, subnets, firewalls |
| **Identity** | IAM roles, service accounts |
| **Storage** | Block storage, object storage |

### Key Security Controls

```
┌─────────────────────────────────────────────────────────────┐
│              CLOUD LAYER SECURITY                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  IDENTITY & ACCESS                                         │
│  ├── IAM policies (least privilege)                        │
│  ├── MFA for privileged accounts                           │
│  └── Service account key rotation                          │
│                                                             │
│  NETWORK                                                    │
│  ├── VPC isolation                                         │
│  ├── Security groups / firewalls                           │
│  ├── Private subnets for control plane                     │
│  └── TLS for all external traffic                          │
│                                                             │
│  COMPUTE                                                    │
│  ├── Encrypted root volumes                                │
│  ├── Immutable infrastructure                              │
│  └── Regular patching / updates                            │
│                                                             │
│  DATA                                                       │
│  ├── Encryption at rest                                    │
│  ├── Encryption in transit                                 │
│  └── Access logging                                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Cloud Shared Responsibility

Who is responsible for what depends on your deployment model:

```
┌─────────────────────────────────────────────────────────────┐
│              SHARED RESPONSIBILITY MODEL                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  MANAGED KUBERNETES (EKS, GKE, AKS)                        │
│  ├── Cloud Provider: Control plane, infrastructure         │
│  └── You: Workloads, RBAC, network policies, pods          │
│                                                             │
│  SELF-MANAGED KUBERNETES                                    │
│  ├── Cloud Provider: Physical infrastructure only          │
│  └── You: Everything else (control plane, nodes, etc.)     │
│                                                             │
│  ON-PREMISES                                                │
│  └── You: Everything (physical security to application)    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Layer 2: Cluster (Kubernetes)

The Kubernetes platform layer—components and configuration.

### What It Includes

| Component | Security Concerns |
|-----------|------------------|
| **Control Plane** | API server, etcd, scheduler, controller-manager |
| **Nodes** | kubelet, kube-proxy, container runtime |
| **Authentication** | User and service account identity |
| **Authorization** | RBAC, admission control |
| **Secrets** | Kubernetes secrets management |

### Key Security Controls

```
┌─────────────────────────────────────────────────────────────┐
│              CLUSTER LAYER SECURITY                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  API SERVER                                                 │
│  ├── TLS for all API communication                         │
│  ├── Strong authentication (OIDC, certificates)            │
│  ├── RBAC authorization                                    │
│  └── Audit logging enabled                                 │
│                                                             │
│  ETCD                                                       │
│  ├── Encryption at rest                                    │
│  ├── TLS for peer/client communication                     │
│  └── Restricted network access                             │
│                                                             │
│  NODES                                                      │
│  ├── Secure kubelet configuration                          │
│  ├── Read-only ports disabled                              │
│  └── Node authorization mode                               │
│                                                             │
│  WORKLOADS                                                  │
│  ├── Pod Security Standards                                │
│  ├── Network Policies                                      │
│  └── Resource quotas                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Layer 3: Container (Runtime)

The container layer—images and runtime isolation.

### What It Includes

| Component | Security Concerns |
|-----------|------------------|
| **Images** | Base images, vulnerabilities, provenance |
| **Runtime** | containerd, CRI-O, gVisor |
| **Isolation** | Namespaces, cgroups, seccomp |
| **Capabilities** | Linux capabilities, privileged mode |

### Key Security Controls

```
┌─────────────────────────────────────────────────────────────┐
│              CONTAINER LAYER SECURITY                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  IMAGES                                                     │
│  ├── Use minimal base images (distroless, alpine)          │
│  ├── Scan for vulnerabilities                              │
│  ├── Sign and verify images                                │
│  └── Use immutable tags (not :latest)                      │
│                                                             │
│  RUNTIME                                                    │
│  ├── Run as non-root user                                  │
│  ├── Read-only root filesystem                             │
│  ├── Drop all capabilities, add only needed                │
│  └── Use seccomp/AppArmor profiles                         │
│                                                             │
│  ISOLATION                                                  │
│  ├── Avoid privileged containers                           │
│  ├── Disable hostPID, hostNetwork, hostIPC                 │
│  └── Consider sandboxed runtimes (gVisor, Kata)            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Container Escape Risk

Why container security matters:

```
┌─────────────────────────────────────────────────────────────┐
│              CONTAINER ESCAPE PATH                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Misconfigured Container                                   │
│  │                                                          │
│  ├── privileged: true                                      │
│  │   └── Full access to host devices and kernel            │
│  │                                                          │
│  ├── hostPID: true                                         │
│  │   └── Can see and signal host processes                 │
│  │                                                          │
│  ├── hostNetwork: true                                     │
│  │   └── Can access node network and services              │
│  │                                                          │
│  └── All of these → CONTAINER ESCAPE → NODE COMPROMISE     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Layer 4: Code (Application)

The innermost layer—your application and its dependencies.

### What It Includes

| Component | Security Concerns |
|-----------|------------------|
| **Dependencies** | Libraries, packages, supply chain |
| **Authentication** | User authentication, tokens |
| **Authorization** | Application-level access control |
| **Data handling** | Input validation, encryption |
| **Secrets** | API keys, database credentials |

### Key Security Controls

```
┌─────────────────────────────────────────────────────────────┐
│              CODE LAYER SECURITY                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  SECURE CODING                                              │
│  ├── Input validation                                      │
│  ├── Output encoding                                       │
│  ├── Parameterized queries (prevent SQL injection)         │
│  └── Safe memory handling                                  │
│                                                             │
│  DEPENDENCIES                                               │
│  ├── Scan for known vulnerabilities (SCA)                  │
│  ├── Pin versions                                          │
│  ├── Verify integrity (checksums, signatures)              │
│  └── Minimize dependencies                                 │
│                                                             │
│  SECRETS                                                    │
│  ├── Never hardcode secrets                                │
│  ├── Use environment variables or secret stores            │
│  ├── Rotate credentials regularly                          │
│  └── Use short-lived tokens                                │
│                                                             │
│  AUTHENTICATION/AUTHORIZATION                               │
│  ├── Strong authentication mechanisms                      │
│  ├── Session management                                    │
│  └── Principle of least privilege                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## How the Layers Interact

### Security Cascades Downward

A breach at a lower layer compromises all layers above:

```
┌─────────────────────────────────────────────────────────────┐
│              BREACH IMPACT CASCADE                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CLOUD breach (AWS credentials leaked)                     │
│  └── Attacker can:                                         │
│      ├── Access any Cluster                                │
│      ├── Modify any Container                              │
│      └── Read any Code/Data                                │
│                                                             │
│  CLUSTER breach (Kubernetes admin access)                  │
│  └── Attacker can:                                         │
│      ├── Deploy malicious Containers                       │
│      └── Access Code secrets                               │
│      (but Cloud infrastructure remains protected)          │
│                                                             │
│  CONTAINER breach (container escape)                       │
│  └── Attacker can:                                         │
│      └── Access Code on same node                          │
│      (but other nodes may be safe)                         │
│                                                             │
│  CODE breach (application vulnerability)                   │
│  └── Attacker can:                                         │
│      └── Access data/secrets in that application           │
│      (other containers are protected)                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Defense in Depth Applied

Secure each layer independently:

```
Even if an attacker compromises your Code layer through
a vulnerability, proper Container security (non-root,
dropped capabilities) limits what they can do.

Even if they escape the Container, proper Cluster
security (RBAC, network policies) limits lateral
movement.

Each layer provides a security boundary that slows
attackers and limits blast radius.
```

---

## Did You Know?

- **The 4 Cs model** is from official Kubernetes documentation. It's not just a study framework—it's how the Kubernetes project thinks about security.

- **Cloud is the foundation** for a reason. In 2023, misconfigurations in cloud IAM were responsible for more breaches than any other single factor.

- **Container escapes** are surprisingly common when containers run privileged. The runc CVE-2019-5736 vulnerability allowed container escape through a malicious image.

- **Code vulnerabilities** like Log4Shell (CVE-2021-44228) showed how a single dependency can compromise millions of systems, regardless of infrastructure security.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| Focusing only on Cluster layer | Ignores Cloud and Container risks | Secure all four layers |
| Assuming Cloud provider handles everything | Shared responsibility varies | Know your responsibilities |
| Running privileged containers | Easy container escape | Use Pod Security Standards |
| Not scanning dependencies | Code vulnerabilities propagate | Implement SCA scanning |
| Treating layers as independent | Breaches cascade | Design defense in depth |

---

## Quiz

1. **What are the 4 Cs of cloud native security in order from outermost to innermost?**
   <details>
   <summary>Answer</summary>
   Cloud, Cluster, Container, Code. From infrastructure to application.
   </details>

2. **If an attacker compromises the Cluster layer, which layers are affected?**
   <details>
   <summary>Answer</summary>
   Container and Code layers above it. The Cloud layer below remains protected (though the attacker may be able to request cloud resources through the cluster).
   </details>

3. **Which layer includes Kubernetes RBAC?**
   <details>
   <summary>Answer</summary>
   Cluster layer. RBAC is a Kubernetes authorization mechanism.
   </details>

4. **What does "security cascades downward" mean in the 4 Cs model?**
   <details>
   <summary>Answer</summary>
   A breach at a lower layer (like Cloud) compromises all layers above it (Cluster, Container, Code). You can only be as secure as your weakest layer.
   </details>

5. **In the shared responsibility model for managed Kubernetes, what is the customer typically responsible for?**
   <details>
   <summary>Answer</summary>
   Workloads, RBAC configuration, network policies, pod security, secrets management, and application security. The cloud provider manages the control plane infrastructure.
   </details>

---

## Hands-On Exercise: Mapping Security Controls

**Scenario**: Your team is securing a new Kubernetes deployment. Categorize each security control into the correct layer.

| Security Control | Layer (Cloud/Cluster/Container/Code) |
|-----------------|--------------------------------------|
| VPC firewall rules | ? |
| RBAC roles and bindings | ? |
| Running as non-root user | ? |
| Input validation in API | ? |
| etcd encryption | ? |
| Image vulnerability scanning | ? |
| IAM role for service account | ? |
| Network policies | ? |

<details>
<summary>Answers</summary>

| Security Control | Layer |
|-----------------|-------|
| VPC firewall rules | **Cloud** - Infrastructure network |
| RBAC roles and bindings | **Cluster** - Kubernetes authorization |
| Running as non-root user | **Container** - Runtime security |
| Input validation in API | **Code** - Application security |
| etcd encryption | **Cluster** - Kubernetes data store |
| Image vulnerability scanning | **Container** - Image security |
| IAM role for service account | **Cloud** - Infrastructure identity |
| Network policies | **Cluster** - Kubernetes network |

</details>

---

## Summary

The 4 Cs of Cloud Native Security:

| Layer | Scope | Key Controls |
|-------|-------|--------------|
| **Cloud** | Infrastructure | IAM, VPC, encryption, firewalls |
| **Cluster** | Kubernetes | RBAC, PSS, etcd, audit logging |
| **Container** | Runtime | Images, non-root, capabilities |
| **Code** | Application | Auth, dependencies, secrets |

Key principles:
- **Security cascades** - lower layer breaches compromise upper layers
- **Defense in depth** - secure each layer independently
- **Shared responsibility** - know what you're responsible for
- **Weakest link** - you're only as secure as your weakest layer

---

## Next Module

[Module 1.2: Cloud Provider Security](../module-1.2-cloud-provider-security/) - Deep dive into the Cloud layer, shared responsibility, and infrastructure security.

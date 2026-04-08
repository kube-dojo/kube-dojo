---
title: "Security Tools Toolkit"
sidebar:
  order: 0
  label: "Security Tools"
---
> **Toolkit Track** | 6 Modules | ~5 hours total

## Overview

The Security Tools Toolkit covers the essential tools for securing Kubernetes clusters and workloads. From secrets management to runtime detection to supply chain integrity—these tools form the defense-in-depth security stack that production clusters require.

This toolkit applies concepts from [Security Principles](../../../foundations/security-principles/) and [DevSecOps Discipline](../../../disciplines/reliability-security/devsecops/).

## Prerequisites

Before starting this toolkit:
- [DevSecOps Discipline](../../../disciplines/reliability-security/devsecops/) — Security concepts and practices
- [Security Principles Foundations](../../../foundations/security-principles/)
- Kubernetes RBAC basics
- Container fundamentals

## Modules

| # | Module | Complexity | Time |
|---|--------|------------|------|
| 4.1 | [Vault & External Secrets](module-4.1-vault-eso/) | `[COMPLEX]` | 45-50 min |
| 4.2 | [OPA & Gatekeeper](module-4.2-opa-gatekeeper/) | `[COMPLEX]` | 45-50 min |
| 4.3 | [Falco](module-4.3-falco/) | `[COMPLEX]` | 45-50 min |
| 4.4 | [Supply Chain Security](module-4.4-supply-chain/) | `[COMPLEX]` | 45-50 min |
| 4.5 | [Tetragon](module-4.5-tetragon/) | `[MEDIUM]` | 90 min |
| 4.6 | [KubeArmor](module-4.6-kubearmor/) | `[MEDIUM]` | 90 min |
| 4.7 | [Kyverno](module-4.7-kyverno/) | `[MEDIUM]` | 35-40 min |
| 4.8 | [SPIFFE/SPIRE](module-4.8-spiffe-spire/) | `[COMPLEX]` | 50 min |

## Learning Outcomes

After completing this toolkit, you will be able to:

1. **Manage secrets securely** — Vault + ESO for centralized, audited secrets
2. **Enforce policies at admission** — Gatekeeper/OPA for policy-as-code
3. **Detect runtime threats** — Falco for syscall-based intrusion detection
4. **Secure the supply chain** — Signing, SBOMs, vulnerability scanning
5. **Prevent attacks with Tetragon** — eBPF-based kernel-level enforcement
6. **Implement least privilege with KubeArmor** — Allow-listing for containers

## Tool Selection Guide

```
WHICH SECURITY TOOL?
─────────────────────────────────────────────────────────────────

"I need to manage secrets across multiple apps"
└──▶ Vault + External Secrets Operator
     • Centralized secrets
     • Automatic rotation
     • Audit trail

"I need to enforce security policies at deploy time"
└──▶ OPA/Gatekeeper (or Kyverno)
     • Block privileged containers
     • Require resource limits
     • Enforce image policies

"I need to detect attacks on running containers"
└──▶ Falco
     • Syscall monitoring
     • Container escape detection
     • Cryptominer detection

"I need to secure my container images"
└──▶ Sigstore + Trivy + Harbor
     • Image signing
     • Vulnerability scanning
     • SBOM generation

SECURITY LAYERS:
─────────────────────────────────────────────────────────────────
                    Build        Deploy       Runtime
─────────────────────────────────────────────────────────────────
Secrets             Vault        ESO          Vault Agent
Policy              n/a          Gatekeeper   n/a
Scanning            Trivy        Admission    Falco
Signing             Cosign       Verify       n/a
```

## The Security Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                   KUBERNETES SECURITY STACK                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  SUPPLY CHAIN SECURITY                                          │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Sigstore (Cosign)  │  Trivy  │  Harbor  │  SBOM          │ │
│  │  Image signing       Vuln scan  Registry   Bill of matls  │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              │                                   │
│                              ▼                                   │
│  ADMISSION CONTROL                                              │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  OPA/Gatekeeper  │  Kyverno  │  Image Policy Webhook      │ │
│  │  Policy-as-code   Alt policy   Signature verification     │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              │                                   │
│                              ▼                                   │
│  SECRETS MANAGEMENT                                             │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Vault  │  External Secrets Operator  │  Sealed Secrets   │ │
│  │  Source   K8s sync                      GitOps secrets     │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              │                                   │
│                              ▼                                   │
│  RUNTIME SECURITY                                               │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Falco  │  NetworkPolicies  │  Seccomp  │  AppArmor       │ │
│  │  Detection  Network isolation  Syscall     Process restrict │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Study Path

```
Module 4.1: Vault & External Secrets
     │
     │  Secrets foundation—get this right first
     ▼
Module 4.2: OPA & Gatekeeper
     │
     │  Prevent bad configs from deploying
     ▼
Module 4.3: Falco
     │
     │  Detect threats in running workloads
     ▼
Module 4.4: Supply Chain Security
     │
     │  Secure images from build to deploy
     ▼
[Toolkit Complete] → Networking Toolkit
```

## Key Concepts

### Defense in Depth

| Layer | Tool | What It Prevents |
|-------|------|------------------|
| **Build** | Trivy, Cosign | Vulnerable images, unsigned artifacts |
| **Deploy** | Gatekeeper | Misconfigurations, policy violations |
| **Secrets** | Vault + ESO | Credential exposure, sprawl |
| **Runtime** | Falco | Active attacks, cryptominers, shells |

### Zero Trust Principles

```
ZERO TRUST IN KUBERNETES
─────────────────────────────────────────────────────────────────

TRADITIONAL: "Inside the cluster = trusted"
ZERO TRUST:  "Never trust, always verify"

Applied:
┌───────────────────────────────────────────────────────────────┐
│ Workload Identity  │  Don't use shared service accounts      │
│ Secret Access      │  Audit every access, rotate regularly   │
│ Network            │  Default deny, explicit allow           │
│ Images             │  Verify signatures, scan continuously   │
│ API Access         │  RBAC, audit logging, admission control │
└───────────────────────────────────────────────────────────────┘
```

## Tool Ecosystem

### Alternatives Considered

| This Toolkit | Alternatives | Why We Chose It |
|--------------|--------------|-----------------|
| Vault | AWS Secrets Manager, GCP Secret Manager | Cloud-agnostic, most features |
| ESO | Sealed Secrets, SOPS | Multi-provider, active development |
| Gatekeeper | Kyverno | Mature, OPA ecosystem, library |
| Falco | Tetragon, Sysdig | CNCF graduated, largest community |
| Cosign | Notary v2 | Simpler, keyless support |

### Integration Points

```
HOW THE TOOLS WORK TOGETHER
─────────────────────────────────────────────────────────────────

1. Developer pushes code
        │
        ▼
2. CI builds image, scans with Trivy
        │
        ▼
3. CI signs with Cosign, generates SBOM
        │
        ▼
4. Push to Harbor (scans again)
        │
        ▼
5. Deploy to K8s → Gatekeeper checks:
   • Is image signed?
   • Does it have resource limits?
   • Is it from allowed registry?
        │
        ▼
6. ESO syncs secrets from Vault
        │
        ▼
7. Pod runs → Falco monitors syscalls
        │
        ▼
8. Falcosidekick alerts on suspicious activity
```

## Hands-On Focus

Each module includes practical exercises:

| Module | Key Exercise |
|--------|--------------|
| Vault & ESO | Sync secrets from Vault to Kubernetes |
| OPA/Gatekeeper | Write policy to block privileged pods |
| Falco | Detect shell execution in container |
| Supply Chain | Sign image, generate SBOM, scan vulns |

## Related Tracks

- **Before**: [DevSecOps Discipline](../../../disciplines/reliability-security/devsecops/) — Security concepts
- **Before**: [Security Principles](../../../foundations/security-principles/) — Theory
- **Related**: [GitOps & Deployments](../../cicd-delivery/gitops-deployments/) — Secure deployments
- **Related**: [IaC Tools](../../infrastructure-networking/iac-tools/) — IaC security scanning with Checkov, tfsec
- **After**: [Networking Toolkit](../../infrastructure-networking/networking/) — Network security

---

*"Security isn't a feature—it's a property. These tools make security a property of your platform, not an afterthought."*

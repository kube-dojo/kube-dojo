---
title: "Security & Compliance"
sidebar:
  order: 1
---

On-premises Kubernetes gives you physical control that cloud never can -- but that control comes with responsibility. You own the hardware, the network perimeter, the key material, and every audit artifact. These four modules cover the security and compliance concerns unique to self-hosted infrastructure.

---

## Modules

| Module | Topics | Complexity |
|--------|--------|------------|
| [Module 6.1: Physical Security & Air-Gapped Environments](module-6.1-air-gapped/) | Datacenter controls, disconnected clusters, Harbor registry, image mirroring, sneakernet updates, air-gapped GitOps | Advanced |
| [Module 6.2: Hardware Security (HSM/TPM)](module-6.2-hardware-security/) | HSMs for key management, TPM measured boot, Vault + PKCS#11, on-prem KMS replacement, LUKS + TPM disk encryption | Advanced |
| [Module 6.3: Enterprise Identity (AD/LDAP/OIDC)](module-6.3-enterprise-identity/) | Active Directory integration, LDAP, Keycloak, Dex OIDC, RBAC group mapping, SSO for dashboards | Medium |
| [Module 6.4: Compliance for Regulated Industries](module-6.4-compliance/) | HIPAA physical controls, SOC 2, PCI DSS scope isolation, data sovereignty, K8s audit policy, evidence collection | Advanced |

---

## Prerequisites

- [Fundamentals](../../prerequisites/) -- Cloud Native 101, Kubernetes Basics
- [CKS](../../k8s/cks/) -- Kubernetes security concepts
- [Planning & Economics](../planning/) -- Datacenter planning context
- [Networking](../networking/) -- Network segmentation and BGP

---

## Who This Section Is For

- **Security engineers** responsible for hardening on-premises Kubernetes clusters
- **Compliance officers** mapping regulatory frameworks to Kubernetes infrastructure
- **Platform teams** integrating enterprise identity systems with Kubernetes RBAC
- **Infrastructure architects** designing air-gapped or classified environments

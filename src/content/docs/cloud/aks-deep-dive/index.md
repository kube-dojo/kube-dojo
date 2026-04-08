---
title: "Azure AKS Deep Dive"
sidebar:
  order: 0
---
**Production-grade Kubernetes on Azure -- from node pools to KEDA-driven scaling.**

AKS is the fastest-growing managed Kubernetes service, tightly integrated with the Azure ecosystem. This track covers node pool architecture and Entra ID integration, the four CNI networking models (Kubenet, Azure CNI, CNI Overlay, Cilium), credential-free security with Workload Identity and Key Vault, and production operations with Container Insights, Managed Prometheus, and KEDA autoscaling.

---

## Modules

| # | Module | Time | What You'll Learn |
|---|--------|------|-------------------|
| 1 | [AKS Architecture & Node Management](module-7.1-aks-architecture/) | 2h | System/user node pools, VMSS, availability zones, Entra ID RBAC |
| 2 | [AKS Advanced Networking](module-7.2-aks-networking/) | 3.5h | Kubenet vs Azure CNI vs Overlay vs Cilium, network policies, Private Link |
| 3 | [AKS Workload Identity & Security](module-7.3-aks-identity/) | 1.5h | Entra Workload Identity, Secrets Store CSI, Azure Policy, Defender |
| 4 | [AKS Storage, Observability & Scaling](module-7.4-aks-production/) | 2.5h | Azure Disks/Files, Container Insights, Managed Prometheus, KEDA |

**Total time**: ~9.5 hours

---

## Prerequisites

- [Azure DevOps Essentials](../azure-essentials/) -- Entra ID, VNets, VMs, Storage fundamentals
- [Cloud Architecture Patterns](../architecture-patterns/) -- managed K8s trade-offs, multi-cluster, IAM integration

## What's Next

After AKS Deep Dive, explore multi-cloud patterns or the [Platform Engineering Track](../../platform/).

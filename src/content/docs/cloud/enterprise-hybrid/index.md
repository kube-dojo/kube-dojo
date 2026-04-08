---
title: "Enterprise & Hybrid Cloud"
sidebar:
  order: 0
  label: "Enterprise & Hybrid"
---
**Landing zones, governance, compliance, hybrid connectivity, fleet management, and multi-cloud operations for organizations running Kubernetes at scale.**

Enterprise Kubernetes is not a technology problem -- it is an organizational one. The hardest challenges are not "how do I deploy a pod" but "how do I provision 50 production-ready clusters for 160 teams with consistent security, compliance, and cost controls." This part covers the architecture and automation that separates companies where a new team waits 14 weeks for a cluster from companies where they get one in 30 minutes. You will learn landing zones, policy as code, continuous compliance, hybrid cloud connectivity, fleet management, and zero trust -- the building blocks of enterprise-grade Kubernetes operations.

---

## Modules

| # | Module | Complexity | Time | What You'll Learn |
|---|--------|------------|------|-------------------|
| 1 | [Enterprise Landing Zones & Account Vending](module-10.1-landing-zones/) | `[COMPLEX]` | 3h | Control Tower, Azure Landing Zones, GCP Org Hierarchy, automated account vending |
| 2 | [Cloud Governance & Policy as Code](module-10.2-governance/) | `[COMPLEX]` | 2.5h | SCPs, Azure Policy, GCP Org Policies, Kyverno, OPA Gatekeeper, unified governance |
| 3 | [Continuous Compliance & CSPM](module-10.3-compliance/) | `[COMPLEX]` | 2h | SOC 2/PCI-DSS/HIPAA mapping, automated evidence collection, compliance drift detection |
| 4 | [Hybrid Cloud Architecture (On-Prem to Cloud)](module-10.4-hybrid/) | `[COMPLEX]` | 3h | VPN/dedicated connections, EKS Anywhere, Anthos, unified identity, data replication |
| 5 | [Multi-Cloud Fleet Management (Azure Arc / GKE Fleet)](module-10.5-fleet-management/) | `[COMPLEX]` | 2.5h | Fleet inventory, centralized policy, configuration management, multi-cloud GitOps |
| 6 | [Multi-Cloud Provisioning with Cluster API](module-10.6-cluster-api/) | `[COMPLEX]` | 3h | CAPI architecture, provider ecosystem (CAPA/CAPZ/CAPG), declarative cluster lifecycle |
| 7 | [Multi-Cloud Service Mesh (Istio Multi-Cluster)](module-10.7-multi-cloud-mesh/) | `[COMPLEX]` | 3h | Istio multi-cluster topologies, SPIFFE/SPIRE trust, cross-cloud routing, mTLS |
| 8 | [Enterprise GitOps & Platform Engineering](module-10.8-enterprise-gitops/) | `[COMPLEX]` | 2.5h | Backstage IDP, ArgoCD at scale, ApplicationSets, multi-tenant Git strategies, RBAC |
| 9 | [Zero Trust Architecture in Hybrid Cloud](module-10.9-zero-trust/) | `[COMPLEX]` | 2.5h | BeyondCorp, Identity-Aware Proxies, micro-segmentation, VPN replacement, SLSA |
| 10 | [FinOps at Enterprise Scale](module-10.10-enterprise-finops/) | `[COMPLEX]` | 2h | Enterprise discounts, forecasting, chargeback models, multi-cloud cost, FinOps culture |

**Total time**: ~26 hours

---

## Prerequisites

- [Cloud Architecture Patterns](../architecture-patterns/) -- managed vs self-managed, multi-cluster theory, cloud IAM, VPC topologies
- [Advanced Cloud Operations](../advanced-operations/) -- multi-account architecture, networking, DR fundamentals
- Experience with at least one hyperscaler and Kubernetes in production

## What's Next

After Enterprise & Hybrid Cloud, continue with:

- [Cloud-Native Managed Services](../managed-services/) -- databases, messaging, serverless, caching, and more
- [Advanced Cloud Operations](../advanced-operations/) -- cross-cluster networking, active-active, cost optimization

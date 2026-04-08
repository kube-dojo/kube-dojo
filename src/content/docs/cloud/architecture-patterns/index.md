---
title: "Cloud Architecture Patterns"
sidebar:
  order: 0
  label: "Architecture Patterns"
---
**Vendor-neutral theory for designing Kubernetes on any cloud provider.**

Before diving into EKS, GKE, or AKS, you need to understand the architectural decisions that apply everywhere: managed vs self-managed trade-offs, multi-cluster strategies, cloud IAM integration patterns, and VPC network topologies. These concepts transfer across all three hyperscalers.

---

## Modules

| # | Module | Time | What You'll Learn |
|---|--------|------|-------------------|
| 1 | [Managed vs Self-Managed Kubernetes](module-4.1-managed-vs-selfmanaged/) | 2h | Trade-offs, decision frameworks, TCO analysis |
| 2 | [Multi-Cluster and Multi-Region Architectures](module-4.2-multi-cluster/) | 3h | Topology patterns, failover, service mesh, federation |
| 3 | [Cloud IAM Integration for Kubernetes](module-4.3-cloud-iam/) | 2.5h | Pod-level identity, OIDC federation, least privilege |
| 4 | [Cloud-Native Networking and VPC Topologies](module-4.4-vpc-topologies/) | 3.5h | CIDR planning, CNI models, IP exhaustion, peering |

**Total time**: ~11 hours

---

## Prerequisites

- [Cloud Native 101](../../prerequisites/cloud-native-101/) -- containers, Docker basics
- Basic Kubernetes knowledge (Pods, Deployments, Services)

## What's Next

After Architecture Patterns, pick your cloud provider deep dive:

- [AWS EKS Deep Dive](../eks-deep-dive/)
- [GCP GKE Deep Dive](../gke-deep-dive/)
- [Azure AKS Deep Dive](../aks-deep-dive/)

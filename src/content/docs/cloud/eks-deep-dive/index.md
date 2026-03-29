---
title: "AWS EKS Deep Dive"
sidebar:
  order: 1
---
**Production-grade Kubernetes on AWS -- from architecture to cost optimization.**

EKS is the most widely deployed managed Kubernetes service. This track covers the full production journey: control plane architecture, VPC CNI networking (and how to avoid IP exhaustion), pod-level IAM with IRSA and Pod Identity, storage with EBS/EFS/S3, and production operations with Karpenter, observability, and cost management.

---

## Modules

| # | Module | Time | What You'll Learn |
|---|--------|------|-------------------|
| 1 | [EKS Architecture & Control Plane](module-5.1-eks-architecture/) | 2.5h | API endpoints, node groups vs Fargate, EKS Add-ons, Access Entries |
| 2 | [EKS Networking Deep Dive (VPC CNI)](module-5.2-eks-networking/) | 3.5h | IP allocation, Prefix Delegation, Custom Networking, Security Groups for Pods |
| 3 | [EKS Identity: IRSA vs Pod Identity](module-5.3-eks-identity/) | 1.5h | Pod-level IAM, OIDC federation, IRSA-to-Pod Identity migration |
| 4 | [EKS Storage & Data Management](module-5.4-eks-storage/) | 2h | EBS CSI, EFS CSI, Mountpoint for S3, StatefulSet AZ resilience |
| 5 | [EKS Production: Scaling, Observability & Cost](module-5.5-eks-production/) | 3h | Karpenter, Spot instances, Container Insights, Kubecost |

**Total time**: ~12.5 hours

---

## Prerequisites

- [AWS DevOps Essentials](../aws-essentials/) -- IAM, VPC, EC2, S3 fundamentals
- [Cloud Architecture Patterns](../architecture-patterns/) -- managed K8s trade-offs, multi-cluster, IAM integration

## What's Next

After EKS Deep Dive, explore multi-cloud patterns or the [Platform Engineering Track](../../platform/).

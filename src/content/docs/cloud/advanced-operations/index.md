---
title: "Advanced Cloud Operations"
sidebar:
  order: 1
  label: "Advanced Operations"
---
**Scaling Kubernetes beyond a single cluster -- multi-account strategies, cross-region networking, disaster recovery, and operational excellence at enterprise scale.**

When your organization grows beyond a handful of clusters, the operational challenges change fundamentally. Single-cluster skills are necessary but insufficient. You need multi-account isolation, transit hub networking, cross-cluster service discovery, enterprise identity federation, and cost optimization strategies that work across hundreds of workloads. This part teaches you how to operate Kubernetes at the scale where things get interesting -- and where mistakes get expensive.

---

## Modules

| # | Module | Complexity | Time | What You'll Learn |
|---|--------|------------|------|-------------------|
| 1 | [Multi-Account Architecture & Org Design](module-8.1-multi-account/) | `[COMPLEX]` | 2.5h | Account structure, OU hierarchy, guardrails, blast radius isolation |
| 2 | [Advanced Cloud Networking & Transit Hubs](module-8.2-transit-hubs/) | `[COMPLEX]` | 3h | Transit Gateways, hub-spoke topologies, cross-VPC routing, CIDR planning |
| 3 | [Cross-Cluster & Cross-Region Networking](module-8.3-cross-cluster-networking/) | `[COMPLEX]` | 3h | Multi-cluster service discovery, cross-region load balancing, DNS strategies |
| 4 | [Cross-Account IAM & Enterprise Identity](module-8.4-enterprise-identity/) | `[COMPLEX]` | 2.5h | Identity federation, cross-account roles, OIDC integration, least privilege at scale |
| 5 | [Disaster Recovery: RTO/RPO for Kubernetes](module-8.5-disaster-recovery/) | `[COMPLEX]` | 2.5h | DR strategies, backup/restore, Velero, RTO/RPO trade-offs |
| 6 | [Multi-Region Active-Active Deployments](module-8.6-active-active/) | `[COMPLEX]` | 3h | Active-active architecture, data replication, conflict resolution, global load balancing |
| 7 | [Stateful Workload Migration & Data Gravity](module-8.7-stateful-migration/) | `[COMPLEX]` | 2.5h | Database migration, storage replication, data gravity, lift-and-shift patterns |
| 8 | [Cloud Cost Optimization (Advanced)](module-8.8-cloud-cost/) | `[MEDIUM]` | 2h | Reserved instances, spot/preemptible, right-sizing, cost allocation |
| 9 | [Large-Scale Observability & Telemetry](module-8.9-observability-scale/) | `[COMPLEX]` | 2.5h | Multi-cluster monitoring, federated Prometheus, centralized logging, telemetry pipelines |
| 10 | [Scaling IaC & State Management](module-8.10-iac-scale/) | `[MEDIUM]` | 2h | Terraform at scale, state splitting, module architecture, CI/CD for infrastructure |

**Total time**: ~25.5 hours

---

## Prerequisites

- [Cloud Architecture Patterns](../architecture-patterns/) -- managed vs self-managed, multi-cluster theory, cloud IAM, VPC topologies
- Familiarity with at least one hyperscaler (AWS, GCP, or Azure)
- Experience operating at least one Kubernetes cluster

## What's Next

After Advanced Operations, continue with:

- [Cloud-Native Managed Services](../managed-services/) -- databases, messaging, serverless, caching, and more
- [Enterprise & Hybrid Cloud](../enterprise-hybrid/) -- landing zones, governance, compliance, fleet management

# GCP GKE Deep Dive

**Production-grade Kubernetes on Google Cloud -- from Autopilot to Fleet management.**

GKE is the most opinionated managed Kubernetes service, with features like Autopilot, Dataplane V2 (eBPF), and Fleet management that go well beyond vanilla Kubernetes. This track covers architecture decisions (Standard vs Autopilot), networking with Dataplane V2 and Gateway API, Workload Identity and Binary Authorization, storage options, and multi-cluster operations with Fleet and Managed Prometheus.

---

## Modules

| # | Module | Time | What You'll Learn |
|---|--------|------|-------------------|
| 1 | [GKE Architecture: Standard vs Autopilot](module-1-gke-architecture.md) | 2h | Cluster modes, release channels, regional vs zonal, auto-upgrades |
| 2 | [GKE Networking: Dataplane V2 and Gateway API](module-2-gke-networking.md) | 3h | VPC-native clusters, eBPF, Cloud Load Balancing, Gateway API canary |
| 3 | [GKE Workload Identity and Security](module-3-gke-identity.md) | 2.5h | Workload Identity Federation, Binary Authorization, Shielded Nodes |
| 4 | [GKE Storage](module-4-gke-storage.md) | 2h | Persistent Disks (zonal/regional), Filestore, Cloud Storage FUSE, Backup for GKE |
| 5 | [GKE Observability and Fleet Management](module-5-gke-fleet.md) | 3h | Cloud Operations, Managed Prometheus, Fleet, Multi-Cluster Services, cost allocation |

**Total time**: ~12.5 hours

---

## Prerequisites

- [GCP DevOps Essentials](../gcp-essentials/README.md) -- IAM, VPC, Compute Engine fundamentals
- [Cloud Architecture Patterns](../architecture-patterns/README.md) -- managed K8s trade-offs, multi-cluster, IAM integration

## What's Next

After GKE Deep Dive, explore multi-cloud patterns or the [Platform Engineering Track](../../platform/README.md).

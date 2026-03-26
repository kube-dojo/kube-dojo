---
title: "Resilience & Migration"
sidebar:
  order: 1
---

Production on-premises Kubernetes does not end at deployment. You need disaster recovery across sites, secure connectivity to cloud environments, and a strategy for moving workloads between cloud and on-prem. This section covers the full resilience lifecycle -- from multi-site failover to hybrid cloud networking to cloud repatriation.

## Modules

| Module | Description | Time |
|--------|-------------|------|
| [8.1 Multi-Site & Disaster Recovery](module-8.1-multi-site-dr/) | Active-active vs active-passive, stretched clusters, Velero backups, etcd snapshots, DNS failover | 60 min |
| [8.2 Hybrid Cloud Connectivity](module-8.2-hybrid-connectivity/) | VPN tunnels, direct interconnects, Submariner, cross-environment service mesh, unified policy | 60 min |
| [8.3 Cloud Repatriation & Migration](module-8.3-cloud-repatriation/) | Moving workloads from cloud to on-prem, service translation, storage migration, phased cutover | 60 min |

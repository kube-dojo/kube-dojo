---
title: "Resilience & Migration"
sidebar:
  order: 0
---

Production on-premises Kubernetes does not end at deployment. True resilience requires preparing for catastrophic failures, spanning geographical locations, and integrating seamlessly with external environments. When you manage your own infrastructure, you are solely responsible for ensuring that a network outage or hardware failure in one data center does not bring down your entire application stack.

To achieve this level of reliability, you need robust disaster recovery strategies across multiple sites, secure and high-performance connectivity to cloud environments, and a well-tested methodology for moving workloads between cloud and on-premises infrastructure. This section covers the full resilience lifecycle, equipping you with the architectural patterns and operational techniques required to maintain continuous availability under adverse conditions.

Whether you are designing active-active multi-site failover, establishing hybrid cloud networking for burst capacity, or executing a strategic cloud repatriation, these modules provide the foundational knowledge and hands-on expertise needed to safeguard your clusters and stateful data.

## Modules

| Module | Description | Time |
|--------|-------------|------|
| [Module 8.1: Multi-Site & Disaster Recovery](module-8.1-multi-site-dr/) | Active-active vs active-passive, stretched clusters, Velero backups, etcd snapshots, DNS failover | 60 min |
| [Module 8.2: Hybrid Cloud Connectivity](module-8.2-hybrid-connectivity/) | VPN tunnels, direct interconnects, Submariner, cross-environment service mesh, unified policy | 60 min |
| [Module 8.3: Cloud Repatriation & Migration](module-8.3-cloud-repatriation/) | Moving workloads from cloud to on-prem, service translation, storage migration, phased cutover | 90 min |
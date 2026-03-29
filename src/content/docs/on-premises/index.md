---
title: "On-Premises Kubernetes"
sidebar:
  order: 1
---

**Run Kubernetes where the cloud can't go.**

Not every workload belongs in the cloud. Data sovereignty, latency requirements, regulatory constraints, and economics drive enterprises to run Kubernetes on their own hardware. This track covers everything from datacenter planning to day-2 operations — the knowledge that most free resources skip because it's not glamorous, but it's where a massive share of production Kubernetes actually runs.

---

## Learning Path

```
Planning & Economics (4 modules)
        │
        ▼
Bare Metal Provisioning (4 modules)
        │
        ├── Networking (4 modules)
        ├── Storage (3 modules)
        └── Multi-Cluster & Platform (3 modules)
                │
                ▼
        Security & Compliance (4 modules)
                │
                ▼
        Day-2 Operations (5 modules)
                │
                ▼
        Resilience & Migration (3 modules)
```

## Sections

| Section | Modules | Focus |
|---------|---------|-------|
| [Planning & Economics](planning/) | 4 | Server sizing, cluster topology, TCO, cloud vs on-prem |
| [Bare Metal Provisioning](provisioning/) | 4 | PXE, MAAS, Talos, Sidero/Metal3 |
| [Networking](networking/) | 4 | Spine-leaf, BGP, MetalLB, internal DNS/certs |
| [Storage](storage/) | 3 | Ceph/Rook, local storage, architecture decisions |
| [Multi-Cluster & Platform](multi-cluster/) | 3 | vSphere/OpenStack, vCluster/Kamaji, Cluster API |
| [Security & Compliance](security/) | 4 | Air-gapped, HSM/TPM, AD/LDAP, regulated industries |
| [Day-2 Operations](operations/) | 5 | Upgrades, firmware, node failure, observability, capacity |
| [Resilience & Migration](resilience/) | 3 | Multi-site DR, hybrid connectivity, cloud repatriation |

**30 modules total.** From "should we go on-prem?" to "how do we run it at scale across two datacenters."

---

## Prerequisites

- [Fundamentals](../prerequisites/) — Cloud Native 101, K8s Basics
- [Linux](../linux/) — networking, storage, security hardening (includes LFCS)
- [Certifications](../k8s/) — [CKA](../k8s/cka/) (cluster architecture, kubeadm) is required
- Recommended: [CKS](../k8s/cks/) for security modules
- Recommended: [Platform Engineering](../platform/) for SRE and operations modules

## Who This Is For

- **Infrastructure engineers** building private Kubernetes platforms
- **Platform teams** evaluating on-prem vs cloud for their organization
- **SREs** operating bare metal or private cloud Kubernetes clusters
- **Architects** designing multi-site, air-gapped, or hybrid environments
- **Budget owners** calculating TCO and making build-vs-buy decisions

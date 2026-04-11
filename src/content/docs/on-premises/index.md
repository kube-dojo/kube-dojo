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
Planning & Economics (5 modules)
        │
        ▼
Bare Metal Provisioning (4 modules)
        │
        ├── Networking (6 modules)
        ├── Storage (5 modules)
        └── Multi-Cluster & Platform (5 modules)
                │
                ▼
        Security & Compliance (8 modules)
                │
                ▼
        Day-2 Operations (9 modules)
                │
                ▼
        Resilience & Migration (3 modules)
                │
                ▼
        AI/ML Infrastructure (6 modules)
```

## Sections

| Section | Modules | Focus |
|---------|---------|-------|
| [Planning & Economics](planning/) | 5 | Server sizing, cluster topology, TCO, cloud vs on-prem, FinOps & chargeback |
| [Bare Metal Provisioning](provisioning/) | 4 | PXE, MAAS, Talos, Sidero/Metal3 |
| [Networking](networking/) | 6 | Spine-leaf, BGP, MetalLB, DNS/certs, cross-cluster, service mesh |
| [Storage](storage/) | 5 | Ceph/Rook, local storage, object storage (MinIO), database operators |
| [Multi-Cluster & Platform](multi-cluster/) | 5 | vSphere/OpenStack, vCluster/Kamaji, Cluster API, fleet management, active-active |
| [Security & Compliance](security/) | 8 | Air-gapped, HSM/TPM, AD/LDAP, SPIFFE, Vault, policy-as-code, zero-trust |
| [Day-2 Operations](operations/) | 9 | Upgrades, firmware, observability, capacity, self-hosted CI/CD & registry, serverless |
| [Resilience & Migration](resilience/) | 3 | Multi-site DR, hybrid connectivity, cloud repatriation |
| [AI/ML Infrastructure](ai-ml-infrastructure/) | 6 | GPU nodes, private training, LLM serving, MLOps, AIOps, HPC storage |

**51 modules total** (30 existing + 21 new from [#197](https://github.com/kube-dojo/kube-dojo.github.io/issues/197)). From "should we go on-prem?" to "how do we train LLMs on our own GPUs."

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

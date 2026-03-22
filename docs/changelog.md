# Changelog

## March 2026 — Ecosystem Update + Quality Review

**The biggest update since KubeDojo launched.** 18 new modules, 30+ modules updated, and every single module reviewed for quality.

### Kubernetes 1.35 "Timbernetes" Support

KubeDojo is now fully aligned with **Kubernetes 1.35** (released December 2025):

- **Version bump**: All cluster setup, kubeadm, and upgrade examples updated from 1.31 to 1.35
- **cgroup v2 required**: Cluster setup module now covers the cgroup v2 requirement (v1 disabled by default)
- **containerd 2.0**: Updated container runtime guidance for containerd 2.0+
- **In-Place Pod Resize (GA)**: New section in Resource Management covering live CPU/memory adjustments
- **Gateway API is the standard**: Reframed from "future" to current recommended approach
- **Ingress-NGINX retirement**: Added migration guidance across CKA, CKAD, and CKS tracks
- **IPVS deprecation**: Updated networking modules to recommend nftables
- **WebSocket RBAC change**: Critical breaking change documented in RBAC module

### New Modules

#### Certification Tracks
| Module | Track | Description |
|--------|-------|-------------|
| Autoscaling (HPA/VPA) | CKA | Horizontal and Vertical Pod Autoscaling with hands-on load testing |
| etcd-operator v0.2.0 | Platform | Official etcd operator — TLS management, managed upgrades |
| CNPE Learning Path | CNPE | Maps 60+ existing modules to the new CNPE certification domains |

#### Platform Engineering Toolkit — 15 New Modules
| Module | Category | Description |
|--------|----------|-------------|
| **FinOps & OpenCost** | Scaling | K8s cost optimization, resource right-sizing, idle cleanup |
| **Kyverno** | Security | YAML-native policy engine — validate, mutate, generate |
| **Chaos Engineering** | Scaling | LitmusChaos + Chaos Mesh hands-on with GameDay planning |
| **Building Operators** | Platforms | Kubebuilder from scratch — build a WebApp operator |
| **Continuous Profiling** | Observability | Parca + Pyroscope — the 4th pillar of observability |
| **SLO Tooling** | Observability | Sloth + Pyrra — bridging SRE theory to practice |
| **Cluster API** | Platforms | Declarative K8s cluster lifecycle management (CAPI) |
| **vCluster** | Platforms | Virtual K8s clusters for multi-tenancy at 1/10th the cost |
| **Rook/Ceph** | Storage | Distributed storage — block, filesystem, and object from one cluster |
| **MinIO** | Storage | S3-compatible object storage on K8s |
| **Longhorn** | Storage | Lightweight distributed block storage with backup/DR |
| **GPU Scheduling** | ML Platforms | NVIDIA GPU Operator, time-slicing, MIG, monitoring |
| **DNS Deep Dive** | Networking | CoreDNS customization, external-dns, ndots optimization |
| **MetalLB** | Networking | Bare-metal load balancing — L2 and BGP modes |
| **SPIFFE/SPIRE** | Security | Cryptographic workload identity for zero-trust networking |

### CKS Exam Alignment

Verified our CKS modules against the CNCF's October 2024 exam overhaul and filled identified gaps:
- Added **Cilium Pod-to-Pod encryption** (WireGuard/IPsec) to Network Policies module
- Added **KubeLinter** section to Static Analysis module
- Updated CKS prerequisite: CKA no longer needs to be active — just passed at any point

### Quality Review ("The KubeDojo Gauntlet")

Every module in KubeDojo was reviewed by **Gemini AI** as an adversary reviewer:

- **329 modules reviewed** across 4 phases
- **95%+ scored 9.5-10/10** on the "Dojo Scale" (Vibe Check, Junior-Proof, Live Test, Sticky Factor)
- **7 modules improved** with dramatic openings, fixing dry "academic" tone
- **1 stub expanded** from 43 lines to 788 lines (CKA Networking Data Path)
- Older Prerequisites modules upgraded to match the quality of newer Platform modules

### Claude-Gemini Collaboration

This update was produced through a novel **multi-AI collaboration**:
- **Claude** (Opus 4.6) handled implementation — writing modules, updating content, managing issues
- **Gemini** (3 Flash) served as adversary reviewer — catching technical errors, flagging dry content, suggesting improvements
- Communication via **ai_agent_bridge** — an SQLite-based message broker enabling structured review workflows
- Every issue was Gemini-reviewed before closing
- Gemini caught 2 technical inaccuracies (StatefulSet versioning, trafficDistribution values) that were fixed before merge

### By the Numbers

| Metric | Count |
|--------|-------|
| New modules | 18 |
| Modules updated | 30+ |
| Modules quality-reviewed | 329 |
| GitHub issues created & closed | 25 |
| Lines of new content | ~12,000 |
| Total curriculum modules | 329 |
| Tracks | 10 (CKA, CKAD, CKS, KCNA, KCSA, CNPE, Platform, Linux, IaC, Prerequisites) |

---

## December 2025 — Initial Release

KubeDojo launched with 311 modules covering all 5 Kubestronaut certifications plus Platform Engineering, Linux, and IaC deep dives. See the [full project history](https://github.com/krisztiankoos/kubedojo/commits/main) for details.

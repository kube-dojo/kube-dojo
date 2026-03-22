# CCA - Cilium Certified Associate

> **Multiple-choice exam** | 90 minutes | Passing score: 66% | $250 USD | **Launched 2024**

## Overview

The CCA (Cilium Certified Associate) validates foundational knowledge of Cilium, eBPF-based networking, network policy, observability, and multi-cluster connectivity. It's a **theory exam** with multiple-choice questions -- no hands-on tasks, but deep understanding of Cilium concepts is essential.

**KubeDojo covers ~90%+ of CCA topics** through our existing Platform Engineering toolkit modules plus a dedicated advanced Cilium module. This page maps CCA domains to existing modules.

> **Cilium is now the default CNI** for GKE, EKS, and AKS. Understanding Cilium isn't just exam prep -- it's a core skill for any Kubernetes engineer.

---

## Exam Domains

| Domain | Weight | KubeDojo Coverage | Status |
|--------|--------|-------------------|--------|
| Architecture | 20% | Partial -- deepened in Module 1 | Covered |
| Network Policy | 18% | Partial -- deepened in Module 1 | Covered |
| Service Mesh | 16% | Good (Gateway API covered in Module 1) | Covered |
| Observability | 10% | Good (Hubble module) | Covered |
| Installation & Configuration | 10% | Partial -- deepened in Module 1 | Covered |
| Cluster Mesh | 10% | GAP -- covered in Module 1 | Covered |
| eBPF | 10% | Good (multiple existing modules) | Covered |
| BGP & External Networking | 6% | GAP -- covered in Module 1 | Covered |

---

## Domain 1: Architecture (20%)

### Competencies
- Understanding Cilium's component architecture (agent, operator, Hubble, relay)
- Knowing how Cilium integrates with the Linux kernel via eBPF
- Understanding identity-based security and how it differs from IP-based
- IPAM modes and data path options

### KubeDojo Learning Path

| Module | Topic | Relevance |
|--------|-------|-----------|
| [Cilium Toolkit](../../platform/toolkits/networking/module-5.1-cilium.md) | Cilium overview, eBPF foundations, architecture diagram, identity-based security | Direct |
| [CCA Module 1](module-1-advanced-cilium.md) | Agent, Operator, Hubble deep dive, IPAM modes (cluster-pool, kubernetes, multi-pool) | Direct |
| [eBPF Foundations](../../platform/toolkits/networking/module-5.1-cilium.md#part-2-enter-ebpf---programming-the-unprogrammable) | eBPF verifier, program types, maps | Direct |

---

## Domain 2: Network Policy (18%)

### Competencies
- Writing CiliumNetworkPolicy and CiliumClusterwideNetworkPolicy
- Understanding L3/L4 and L7 (HTTP-aware) policy enforcement
- Identity-based vs IP-based policy models
- Policy enforcement modes (default, always, never)
- DNS-based (FQDN) egress policies

### KubeDojo Learning Path

| Module | Topic | Relevance |
|--------|-------|-----------|
| [Cilium Toolkit](../../platform/toolkits/networking/module-5.1-cilium.md#part-5-network-policies---from-basic-to-wow) | Standard NetworkPolicy, CiliumNetworkPolicy, L7 rules, DNS-based egress, cluster-wide policies | Direct |
| [CCA Module 1](module-1-advanced-cilium.md) | CiliumNetworkPolicy vs K8s NetworkPolicy comparison, policy enforcement modes, L7 HTTP-aware rules, entity-based policies | Direct |
| [CKS Network Policies](../../k8s/cks/) | Standard K8s NetworkPolicy (baseline knowledge) | Supporting |

---

## Domain 3: Service Mesh (16%)

### Competencies
- Understanding Cilium's sidecar-free service mesh model
- Gateway API integration
- mTLS with Cilium (SPIFFE identities)
- Load balancing and traffic management

### KubeDojo Learning Path

| Module | Topic | Relevance |
|--------|-------|-----------|
| [Service Mesh Toolkit](../../platform/toolkits/networking/module-5.2-service-mesh.md) | Service mesh patterns, sidecar vs sidecar-free, Gateway API | Direct |
| [Cilium Toolkit](../../platform/toolkits/networking/module-5.1-cilium.md#part-8-transparent-encryption-with-wireguard) | WireGuard encryption, kube-proxy replacement | Partial |
| [SPIFFE/SPIRE](../../platform/toolkits/security-tools/module-4.8-spiffe-spire.md) | Workload identity, mTLS concepts | Supporting |

> Cilium-specific Gateway API configuration (HTTPRoute, GRPCRoute with Cilium as the Gateway controller) is now covered in [CCA Module 1](module-1-advanced-cilium.md). For additional depth, see the [Cilium Gateway API docs](https://docs.cilium.io/en/stable/network/servicemesh/gateway-api/).

---

## Domain 4: Observability (10%)

### Competencies
- Using Hubble CLI for flow observation and filtering
- Understanding Hubble Relay and UI architecture
- Configuring Hubble metrics for Prometheus
- Interpreting network flow data for troubleshooting

### KubeDojo Learning Path

| Module | Topic | Relevance |
|--------|-------|-----------|
| [Hubble Toolkit](../../platform/toolkits/observability/module-1.7-hubble.md) | Hubble architecture, CLI usage, flow filtering, UI, Prometheus metrics, troubleshooting scenarios | Direct |
| [Cilium Toolkit](../../platform/toolkits/networking/module-5.1-cilium.md#part-6-hubble---seeing-the-invisible) | Hubble CLI commands, output anatomy, debugging scenarios, metrics configuration | Direct |

---

## Domain 5: Installation & Configuration (10%)

### Competencies
- Installing Cilium using the Cilium CLI and Helm
- Configuring kube-proxy replacement
- Validating installations with `cilium status` and `cilium connectivity test`
- Upgrading Cilium

### KubeDojo Learning Path

| Module | Topic | Relevance |
|--------|-------|-----------|
| [Cilium Toolkit](../../platform/toolkits/networking/module-5.1-cilium.md#installation-your-first-cilium-cluster) | Cilium CLI installation, install with Helm values, connectivity test | Direct |
| [CCA Module 1](module-1-advanced-cilium.md) | Cilium CLI deep dive (install, status, connectivity test, config), Helm-based install | Direct |

---

## Domain 6: Cluster Mesh (10%)

### Competencies
- Understanding multi-cluster connectivity with Cluster Mesh
- Configuring global services and service affinity
- Cross-cluster service discovery
- Cluster Mesh requirements and limitations

### KubeDojo Learning Path

| Module | Topic | Relevance |
|--------|-------|-----------|
| [CCA Module 1](module-1-advanced-cilium.md) | Cluster Mesh architecture, global services, affinity annotations, multi-cluster service discovery, hands-on setup | Direct |

> **This was a GAP** in our existing content. Module 1 provides full coverage.

---

## Domain 7: eBPF (10%)

### Competencies
- Understanding eBPF fundamentals (programs, maps, verifier)
- How Cilium uses eBPF for networking, policy, and observability
- eBPF vs iptables for packet processing
- XDP (eXpress Data Path) basics

### KubeDojo Learning Path

| Module | Topic | Relevance |
|--------|-------|-----------|
| [Cilium Toolkit](../../platform/toolkits/networking/module-5.1-cilium.md#part-2-enter-ebpf---programming-the-unprogrammable) | eBPF mental model, verifier, packet flow comparison, kernel programming | Direct |
| [CCA Module 1](module-1-advanced-cilium.md) | eBPF in the context of Cilium architecture, dataplane | Supporting |

---

## Domain 8: BGP & External Networking (6%)

### Competencies
- Understanding BGP peering with CiliumBGPPeeringPolicy
- Advertising pod CIDRs and service VIPs to external routers
- LoadBalancer IP advertisement
- Basic BGP concepts (ASN, peering, route advertisement)

### KubeDojo Learning Path

| Module | Topic | Relevance |
|--------|-------|-----------|
| [CCA Module 1](module-1-advanced-cilium.md) | CiliumBGPPeeringPolicy, ASN configuration, route advertisement, LoadBalancer integration | Direct |

> **This was a GAP** in our existing content. Module 1 provides full coverage.

---

## Study Strategy

```
CCA PREPARATION PATH (recommended order)
══════════════════════════════════════════════════════════════

Week 1: Foundations (eBPF + Architecture = 30%)
├── Cilium Toolkit module (full read-through)
├── CCA Module 1: Architecture deep dive
├── Focus on: agent vs operator roles, identity model, IPAM
└── Lab: Install Cilium on kind cluster, run connectivity test

Week 2: Network Policy (18%)
├── Cilium Toolkit: Network Policy sections
├── CCA Module 1: Policy enforcement modes
├── Practice writing CiliumNetworkPolicy YAML
└── Lab: Default deny + allow rules, L7 HTTP policies

Week 3: Service Mesh + Observability (26%)
├── Service Mesh toolkit module
├── Hubble toolkit module (full)
├── Cilium Toolkit: Hubble sections
└── Lab: Hubble observe with --verdict DROPPED, Prometheus metrics

Week 4: Cluster Mesh + BGP + Review (16%)
├── CCA Module 1: Cluster Mesh section
├── CCA Module 1: BGP section
├── Review all quiz questions
└── Practice: End-to-end troubleshooting scenarios
```

---

## Exam Tips

- **This is a theory exam** -- no hands-on terminal, but conceptual depth is key
- **Know the architecture cold** -- which component does what, where it runs, how many instances
- **CiliumNetworkPolicy vs K8s NetworkPolicy** -- understand exactly what Cilium adds (L7, FQDN, entities, cluster-wide)
- **Identity model** -- the exam loves questions about why identity-based security beats IP-based
- **Hubble CLI flags** -- know the common filters (`--verdict`, `--from-pod`, `--to-pod`, `--protocol`)
- **Cluster Mesh** -- understand requirements (shared CA, unique pod CIDRs, connectivity between clusters)
- **BGP** -- know what CiliumBGPPeeringPolicy does and when you'd use it (advertising LoadBalancer IPs)
- **Policy enforcement modes** -- `default`, `always`, `never` and when each applies

---

## Gap Analysis

| Topic | Status | Notes |
|-------|--------|-------|
| Cilium Gateway API (HTTPRoute, GRPCRoute) | Covered | Covered in [CCA Module 1](module-1-advanced-cilium.md) alongside the Service Mesh module |
| Cilium Bandwidth Manager | Covered | Covered in [CCA Module 1](module-1-advanced-cilium.md); niche topic, low exam weight |
| Cilium Egress Gateway | Covered | Covered in [CCA Module 1](module-1-advanced-cilium.md); advanced feature, unlikely to be heavily tested |
| CiliumL2AnnouncementPolicy | Covered | Covered in [CCA Module 1](module-1-advanced-cilium.md); Layer 2 advertisement, rare in exam |

The existing toolkit modules plus CCA Module 1 provide comprehensive CCA preparation.

---

## Module Index

| # | Module | Topics | Complexity |
|---|--------|--------|------------|
| 1 | [Advanced Cilium for CCA](module-1-advanced-cilium.md) | Architecture depth, CiliumNetworkPolicy, Cluster Mesh, BGP, Cilium CLI | `[COMPLEX]` |

---

## Related Certifications

```
CERTIFICATION PATH
══════════════════════════════════════════════════════════════

Entry Level:
├── KCNA (Cloud Native Associate) -- K8s fundamentals
├── KCSA (Security Associate) -- Security fundamentals
└── CCA (Cilium Certified Associate) <-- YOU ARE HERE

Professional Level:
├── CKA (K8s Administrator) -- Cluster operations
├── CKAD (K8s Developer) -- Application deployment
├── CKS (K8s Security Specialist) -- Security hardening
└── CNPE (Platform Engineer) -- Platform engineering

Specialist:
└── CKNE (K8s Network Engineer) -- Advanced networking (covers Cilium at depth)
```

The CCA pairs well with KCNA (general K8s knowledge) and KCSA (security foundations). If you plan to pursue CKNE later, CCA gives you a strong head start on the Cilium-specific portions.

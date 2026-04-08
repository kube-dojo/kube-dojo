---
title: "Networking Toolkit"
sidebar:
  order: 0
  label: "Networking"
---
> **Toolkit Track** | 5 Modules | ~4.5 hours total

## Overview

The Networking Toolkit covers advanced Kubernetes networking beyond basic Services and Ingress. Cilium brings eBPF-powered networking with identity-based security and deep observability. Service mesh adds traffic management and mTLS for complex microservice architectures.

This toolkit builds on [Security Principles](../../../foundations/security-principles/) and complements the [Security Tools Toolkit](../../security-quality/security-tools/).

## Prerequisites

Before starting this toolkit:
- Kubernetes Services, Pods, and basic networking
- [Security Principles Foundations](../../../foundations/security-principles/)
- Linux networking basics (TCP/IP, DNS)
- Container fundamentals

## Modules

| # | Module | Complexity | Time |
|---|--------|------------|------|
| 5.1 | [Cilium](module-5.1-cilium/) | `[COMPLEX]` | 50-60 min |
| 5.2 | [Service Mesh](module-5.2-service-mesh/) | `[COMPLEX]` | 50-60 min |
| 5.3 | [DNS Deep Dive](module-5.3-dns-deep-dive/) | `[MEDIUM]` | 40 min |
| 5.4 | [MetalLB](module-5.4-metallb/) | `[MEDIUM]` | 35 min |
| 5.5 | [Flannel](module-5.5-flannel/) | `[MEDIUM]` | 45-50 min |
| 5.6 | [Calico](module-5.6-calico/) | `[COMPLEX]` | 55-65 min |
| 5.7 | [kube-router](module-5.7-kube-router/) | `[MEDIUM]` | 40-45 min |
| 5.8 | [Multus](module-5.8-multus/) | `[MEDIUM]` | 40-45 min |

## Learning Outcomes

After completing this toolkit, you will be able to:

1. **Deploy Cilium as CNI** — Replace kube-proxy, enable eBPF networking
2. **Write network policies** — Identity-based L3-L7 policies
3. **Observe network traffic** — Hubble for flow visibility
4. **Understand service mesh** — When to use Istio/Linkerd and when not to
5. **Configure mTLS** — Zero-trust service-to-service communication
6. **Deploy Calico** — BGP networking, policy tiers, WireGuard encryption, IPAM

## Tool Selection Guide

```
WHICH NETWORKING APPROACH?
─────────────────────────────────────────────────────────────────

"I need basic network policies and a modern CNI"
└──▶ Cilium (without service mesh)
     • Identity-based policies
     • eBPF performance
     • Hubble observability
     • Replaces kube-proxy

"I need mTLS and traffic management (canary, retries)"
└──▶ Decide based on complexity:
     │
     ├── Simple needs ──▶ Cilium Service Mesh (sidecar-free)
     │
     ├── Medium needs ──▶ Linkerd (lightweight, Rust proxy)
     │
     └── Complex needs ──▶ Istio (most features, most overhead)

COMPARISON:
─────────────────────────────────────────────────────────────────
                     Cilium        Linkerd       Istio
─────────────────────────────────────────────────────────────────
Proxy               eBPF (kernel) Rust sidecar  Envoy sidecar
Memory/pod          ~0 MB         ~10 MB        ~50-100 MB
Latency overhead    Minimal       ~1ms          ~2ms
Complexity          Low           Medium        High
mTLS                ✓             ✓             ✓
L7 policies         ✓             Limited       Advanced
Traffic mgmt        Basic         Basic         Advanced
Learning curve      Medium        Low           High
```

## The Networking Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                KUBERNETES NETWORKING STACK                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  LAYER 7 - APPLICATION                                          │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Ingress Controller (nginx, traefik)                      │ │
│  │  API Gateway                                              │ │
│  │  Service Mesh L7 policies (HTTP routing, auth)            │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              │                                   │
│  LAYER 4 - TRANSPORT                                            │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Services (ClusterIP, NodePort, LoadBalancer)             │ │
│  │  Service Mesh mTLS                                        │ │
│  │  Network Policies (TCP/UDP rules)                         │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              │                                   │
│  LAYER 3 - NETWORK                                              │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  CNI Plugin (Cilium, Calico, Flannel)                     │ │
│  │  Pod-to-Pod networking                                    │ │
│  │  IP address management                                    │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Study Path

```
Module 5.1: Cilium
     │
     │  CNI + eBPF fundamentals
     │  Network policies
     │  Hubble observability
     ▼
Module 5.2: Service Mesh
     │
     │  When to use service mesh
     │  Istio core concepts
     │  mTLS and traffic management
     ▼
[Toolkit Complete] → Scaling & Reliability Toolkit
```

## Key Concepts

### eBPF vs Traditional Networking

| Aspect | Traditional (iptables) | eBPF (Cilium) |
|--------|----------------------|---------------|
| **Performance** | O(n) rule matching | O(1) hash lookup |
| **Visibility** | Packet capture | Rich flow metadata |
| **Updates** | Slow, disruptive | Atomic, live |
| **Identity** | IP-based | Label-based |

### Service Mesh Trade-offs

```
THE SERVICE MESH SPECTRUM
─────────────────────────────────────────────────────────────────

No Mesh          Cilium Mesh       Linkerd           Istio
────────────────────────────────────────────────────────────────
Simple           Low overhead      Balanced          Full featured
NetworkPolicies  eBPF-based        Rust proxy        Envoy proxy
Basic observ.    Good observ.      Great observ.     Best observ.
No mTLS          mTLS              mTLS              mTLS + AuthZ
No traffic mgmt  Basic             Basic             Advanced

← Less complexity                    More features →
← Less overhead                      More overhead →
```

## Common Decisions

### Do I Need Cilium?

| Scenario | Recommendation |
|----------|----------------|
| Modern K8s, want best CNI | Yes, replaces default CNI |
| Need L7 policies | Yes, CiliumNetworkPolicy |
| Want to replace kube-proxy | Yes, eBPF handles Services |
| Using managed K8s with good CNI | Maybe, depends on requirements |

### Do I Need Service Mesh?

| Scenario | Recommendation |
|----------|----------------|
| < 10 services | Probably not |
| Need mTLS for compliance | Yes, or use Cilium mesh |
| Complex traffic management | Yes, Istio |
| Cost-sensitive, many pods | Avoid heavy meshes, consider Linkerd/Cilium |

## Hands-On Focus

| Module | Key Exercise |
|--------|--------------|
| Cilium | Deploy CNI, implement network policies, use Hubble |
| Service Mesh | Deploy Istio, enable mTLS, traffic routing |
| Calico | Deploy Calico on kind, tiered policies, BGP peering |

## Related Tracks

- **Before**: [Security Tools Toolkit](../../security-quality/security-tools/) — Security context
- **Before**: [Security Principles](../../../foundations/security-principles/) — Theory
- **Related**: [IaC Tools Toolkit](../iac-tools/) — Terraform modules for Cilium, Istio
- **Related**: [DevSecOps Discipline](../../../disciplines/reliability-security/devsecops/) — Security practices
- **After**: [Scaling & Reliability](../../developer-experience/scaling-reliability/) — Autoscaling

---

*"Network security isn't about blocking traffic—it's about understanding traffic. Cilium and service mesh give you that understanding."*

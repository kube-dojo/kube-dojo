---
title: "Kubernetes Networking"
sidebar:
  order: 0
  label: "Kubernetes Networking"
---
> **Discipline Track** | 5 Modules | ~5-6 hours total

## Overview

Kubernetes networking is deceptively simple on the surface — every Pod gets an IP, Services provide stable endpoints, and Ingress handles external traffic. Underneath, a complex web of CNI plugins, iptables/eBPF rules, DNS resolution, and overlay networks makes it all work. When it breaks, the blast radius is everything.

This discipline covers the applied networking decisions platform engineers face daily: choosing and operating CNI plugins, designing network policies for zero-trust segmentation, evaluating service mesh trade-offs, configuring Gateway API for traffic management, and connecting clusters across regions and clouds.

**This is NOT general networking theory.** For DNS fundamentals, CDN architecture, WAF concepts, BGP routing, and zero-trust networking principles, see the [Advanced Networking foundation track](../../../foundations/advanced-networking/). This discipline assumes you understand those concepts and focuses on how they manifest inside Kubernetes.

## Prerequisites

Before starting this track:
- [Kubernetes Basics](../../../../prerequisites/kubernetes-basics/) — Pods, Services, Deployments, Namespaces
- [Advanced Networking foundations](../../../foundations/advanced-networking/) — DNS, load balancing, TLS, network models
- Container networking basics (network namespaces, veth pairs, bridges)
- Comfort with `kubectl`, YAML manifests, and Helm charts

## Modules

| # | Module | Complexity | Time |
|---|--------|------------|------|
| 1.1 | [CNI Architecture & Selection](module-1.1-cni-architecture/) | `[COMPLEX]` | 55-65 min |
| 1.2 | [Network Policy Design Patterns](module-1.2-network-policy-design/) | `[COMPLEX]` | 60-70 min |
| 1.3 | [Service Mesh Architecture & Strategy](module-1.3-service-mesh-strategy/) | `[COMPLEX]` | 60-75 min |
| 1.4 | [Ingress, Gateway API & Traffic Management](module-1.4-ingress-gateway/) | `[COMPLEX]` | 55-65 min |
| 1.5 | [Multi-Cluster & Hybrid Networking](module-1.5-multi-cluster-networking/) | `[COMPLEX]` | 60-70 min |

**Total Time**: ~5-6 hours

## Learning Outcomes

After completing this track, you will be able to:

1. **Select and operate CNI plugins** — Evaluate Calico, Cilium, Flannel based on your performance, security, and operational requirements
2. **Design network policies** — Implement default-deny, namespace isolation, and zero-trust microsegmentation
3. **Make service mesh decisions** — Know when you need a mesh, which to choose, and how to operate it without drowning in complexity
4. **Configure modern traffic management** — Use Gateway API, choose ingress controllers, implement rate limiting and circuit breaking
5. **Connect clusters** — Design multi-cluster and hybrid networking with DNS discovery, mesh federation, and cross-cluster connectivity

## Learning Path

```
Module 1.1: CNI Architecture & Selection
    |
    ├── How CNI plugins work under the hood
    ├── Compare Calico vs Cilium vs Flannel
    └── Choose the right CNI for your cluster
          |
          v
Module 1.2: Network Policy Design Patterns
    |
    ├── Default-deny and namespace isolation
    ├── K8s vs Cilium vs Calico policies
    └── Zero-trust microsegmentation
          |
          v
Module 1.3: Service Mesh Architecture & Strategy
    |
    ├── When you need a mesh (and when you don't)
    ├── Istio vs Linkerd vs Cilium mesh
    └── Sidecar vs ambient (sidecarless)
          |
          v
Module 1.4: Ingress, Gateway API & Traffic Management
    |
    ├── Ingress controllers compared
    ├── Gateway API HTTPRoute, GRPCRoute, TLSRoute
    └── Rate limiting, circuit breaking, retries
          |
          v
Module 1.5: Multi-Cluster & Hybrid Networking
    |
    ├── Flat vs overlay across clusters
    ├── Submariner, ClusterMesh, Skupper
    └── DNS discovery and hybrid connectivity
```

## Key Concepts

### The Kubernetes Networking Model

Every Kubernetes networking implementation must satisfy three fundamental requirements:

1. **Pod-to-Pod** — Every Pod can communicate with every other Pod without NAT
2. **Pod-to-Service** — Pods can reach Services via ClusterIP, and kube-proxy (or eBPF) handles routing
3. **External-to-Service** — External traffic reaches Pods via NodePort, LoadBalancer, or Ingress/Gateway API

```
┌──────────────────────────────────────────────────────────────┐
│                     External Traffic                          │
│              (Ingress / Gateway API / LB)                     │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       v
┌──────────────────────────────────────────────────────────────┐
│                  Service Layer                                │
│          (ClusterIP, NodePort, LoadBalancer)                  │
│          kube-proxy / eBPF / IPVS                            │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       v
┌──────────────────────────────────────────────────────────────┐
│                    CNI Layer                                   │
│        Pod-to-Pod networking (bridge, vxlan, eBPF)           │
│        Network Policies (deny/allow rules)                   │
│        IPAM (IP address management)                          │
└──────────────────────────────────────────────────────────────┘
```

### Decision Matrix: What To Use When

| Need | Solution | Module |
|------|----------|--------|
| Pod networking and IP management | CNI plugin | 1.1 |
| East-west traffic control | Network Policies | 1.2 |
| mTLS, observability, traffic shaping | Service Mesh | 1.3 |
| External HTTP/HTTPS routing | Gateway API / Ingress | 1.4 |
| Cross-cluster communication | Multi-cluster networking | 1.5 |

## Related Tracks

**Foundations** (Start here if new to these concepts):
- [Advanced Networking](../../../foundations/advanced-networking/) — DNS, CDN, WAF, BGP, load balancing, zero trust
- [Security Principles](../../../foundations/security-principles/) — Defense in depth, least privilege

**Disciplines** (Apply networking in context):
- [DevSecOps Discipline](../devsecops/) — Network security in CI/CD
- [SRE Discipline](../../core-platform/sre/) — Network reliability and incident response
- [Platform Engineering](../../core-platform/platform-engineering/) — Self-service networking abstractions

**Toolkits** (Deep dive into specific tools):
- [Networking Toolkit](../../../toolkits/infrastructure-networking/networking/) — Cilium, service mesh, DNS, and more

## Tools You'll Encounter

| Tool | Purpose |
|------|---------|
| **Calico** | CNI with BGP routing and rich network policy |
| **Cilium** | eBPF-based CNI with L7 policies and service mesh |
| **Flannel** | Simple overlay CNI for basic clusters |
| **Istio** | Full-featured service mesh with Envoy sidecar |
| **Linkerd** | Lightweight, Rust-based service mesh |
| **Gateway API** | Kubernetes-native traffic routing (successor to Ingress) |
| **NGINX Ingress** | Most widely deployed ingress controller |
| **Submariner** | Cross-cluster L3 connectivity |
| **CoreDNS** | Cluster DNS with plugin architecture |

## Progress Checklist

- [ ] Module 1.1: CNI Architecture & Selection
- [ ] Module 1.2: Network Policy Design Patterns
- [ ] Module 1.3: Service Mesh Architecture & Strategy
- [ ] Module 1.4: Ingress, Gateway API & Traffic Management
- [ ] Module 1.5: Multi-Cluster & Hybrid Networking

## Further Reading

- [Kubernetes Networking Model](https://kubernetes.io/docs/concepts/services-networking/)
- [CNI Specification](https://github.com/containernetworking/cni/blob/main/SPEC.md)
- [Gateway API Documentation](https://gateway-api.sigs.k8s.io/)
- [Cilium Documentation](https://docs.cilium.io/)
- [Network Policy Editor](https://editor.networkpolicy.io/) — Visual network policy builder

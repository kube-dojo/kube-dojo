---
title: "Networking"
sidebar:
  order: 0
---

On-premises networking is fundamentally different from cloud networking. There is no VPC wizard, no managed load balancer, and no automatic DNS to rely on. You must design the physical topology, configure the switches, and run the protocols that make Kubernetes networking function efficiently and securely on bare metal.

In a cloud environment, software-defined networking abstracts away the complexities of the underlying physical infrastructure. On bare metal, you are responsible for bridging the gap between the physical data center network and the overlay networks used by your clusters. This requires a deep understanding of Layer 2 and Layer 3 constructs, routing protocols like BGP, and hardware-level considerations such as MTU and VLAN isolation.

This section covers the end-to-end networking stack required to run Kubernetes in your own data center. You will learn how to design a resilient spine-leaf architecture, implement dynamic routing, provision highly available load balancers without cloud provider APIs, and secure cross-cluster communication using service meshes and automated certificate authorities.

## Modules

| Module | Description | Time |
|--------|-------------|------|
| [Module 3.1: Datacenter Network Architecture](module-3.1-datacenter-networking/) | Spine-leaf topology, ToR, L2/L3, MTU, VLAN design | 60 min |
| [Module 3.2: BGP & Routing for Kubernetes](module-3.2-bgp-routing/) | BGP peering, Calico BGP, route reflectors, multi-site | 60 min |
| [Module 3.3: Load Balancing Without Cloud](module-3.3-load-balancing/) | MetalLB, kube-vip, HAProxy/Keepalived | 60 min |
| [Module 3.4: DNS & Certificate Infrastructure](module-3.4-dns-certs/) | Internal DNS, split-horizon, cert-manager with Vault CA | 45 min |
| [Cross-Cluster Networking](module-3.5-cross-cluster-networking/) | Inter-cluster routing, network policies, and stretched overlays | 45 min |
| [Service Mesh on Bare Metal](module-3.6-service-mesh-bare-metal/) | Istio, Linkerd, mTLS, and ingress gateway architectures | 60 min |
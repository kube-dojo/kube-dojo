---
title: "Advanced Networking"
sidebar:
  order: 0
  label: "Advanced Networking"
---
**Networking beyond Kubernetes — what happens when traffic hits the real world.**

Kubernetes networking gets you pod-to-pod communication. But production traffic crosses DNS resolvers, CDN edges, WAF rules, BGP peering points, and load balancers before it ever reaches your cluster. These modules cover the infrastructure that connects your clusters to the internet.

---

## Modules

| # | Module | Time | What You'll Learn |
|---|--------|------|-------------------|
| 1.1 | [DNS at Scale & Global Traffic Management](module-1.1-dns-at-scale/) | 3h | Anycast, GeoDNS, DNSSEC, latency-based routing |
| 1.2 | [CDN & Edge Computing](module-1.2-cdn-edge/) | 2.5h | PoP architecture, cache invalidation, edge functions |
| 1.3 | [WAF & DDoS Mitigation](module-1.3-waf-ddos/) | 2.5h | OWASP rules, rate limiting, bot management |
| 1.4 | [BGP & Core Routing](module-1.4-bgp-routing/) | 3.5h | AS peering, path selection, Direct Connect |
| 1.5 | [Cloud Load Balancing Deep Dive](module-1.5-load-balancing/) | 3h | L4/L7, Proxy Protocol, session affinity |
| 1.6 | [Zero Trust Networking & VPN Alternatives](module-1.6-zero-trust/) | 2.5h | BeyondCorp, IAP, Tailscale, mTLS |
| 1.7 | [IPv6 Fundamentals](module-1.7-ipv6-fundamentals/) | 3.5h | Address families, SLAAC, NDP, DNS, hands-on IPv6 troubleshooting |
| 1.8 | [Dual-Stack Kubernetes Setup & Operations](module-1.8-dual-stack-k8s/) | 3.5h | Control-plane flags, CNI dual-stack setup, Service IP families, EndpointSlices |

**Total time**: ~24 hours

---

## Prerequisites

- Basic DNS and HTTP knowledge
- Kubernetes Ingress/Services (from CKA or Fundamentals)
- Linux networking basics (from Linux Deep Dive)

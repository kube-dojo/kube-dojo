# Networking

> **The network stack that powers container and Kubernetes networking.**

## Overview

Linux networking is the foundation for everything in Kubernetes—pod-to-pod communication, services, ingress, network policies. Understanding it helps you debug networking issues and understand how Kubernetes abstractions actually work.

## Modules

| # | Module | Description | Time |
|---|--------|-------------|------|
| 3.1 | [TCP/IP Essentials](module-3.1-tcp-ip-essentials.md) | OSI model, TCP vs UDP, subnetting, routing | 30-35 min |
| 3.2 | [DNS in Linux](module-3.2-dns-linux.md) | resolv.conf, dig, DNS debugging | 25-30 min |
| 3.3 | [Network Namespaces](module-3.3-network-namespaces.md) | veth pairs, bridges, pod networking | 30-35 min |
| 3.4 | [iptables & netfilter](module-3.4-iptables-netfilter.md) | Packet filtering, NAT, kube-proxy internals | 35-40 min |

## Why This Section Matters

Almost every Kubernetes issue eventually involves networking:

- **Pod can't reach service?** Understand routing and iptables
- **DNS resolution failing?** Know how Linux resolves names
- **Network policy not working?** Understand how netfilter works
- **Performance issues?** Could be network namespace or iptables overhead

## Prerequisites

- [System Essentials](../system-essentials/README.md) — Processes, filesystem
- [Container Primitives](../container-primitives/README.md) — Namespaces concept

## Key Takeaways

After completing this section, you'll understand:

1. How TCP/IP works and how to troubleshoot connectivity
2. How Linux resolves DNS and why containers have DNS issues
3. How network namespaces create isolated network stacks (pod networking)
4. How iptables/netfilter powers Kubernetes services and policies

## Related Sections

- **Previous**: [Container Primitives](../container-primitives/README.md)
- **Next**: [Security/Hardening](../../security/hardening/README.md)
- **Applies to**: Every network-related Kubernetes concept

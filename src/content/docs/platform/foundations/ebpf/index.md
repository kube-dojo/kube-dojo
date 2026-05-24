---
title: "eBPF Fundamentals"
sidebar:
  order: 8
  label: "eBPF"
---
eBPF Fundamentals explains the kernel-programmability model behind Cilium, Tetragon, Pixie, KubeArmor, and other modern platform tools. Read it after Linux and Kubernetes basics, then use it as the shared vocabulary for networking, observability, and runtime security modules that depend on BPF programs, maps, helpers, the verifier, and BTF-based portability.

## Modules

| # | Module | Time | What You'll Learn |
|---|--------|------|-------------------|
| 1.1 | [eBPF Fundamentals](module-1.1-ebpf-fundamentals/) | 55-65 min | Kernel hooks, programs, maps, helpers, verifier, CO-RE, and operating risks |

## Best Next Steps

After this foundation, apply the same mental model in [Cilium](/platform/toolkits/infrastructure-networking/networking/module-5.1-cilium/), [Tetragon](/platform/toolkits/security-quality/security-tools/module-4.5-tetragon/), [KubeArmor](/platform/toolkits/security-quality/security-tools/module-4.6-kubearmor/), and [Pixie](/platform/toolkits/observability-intelligence/observability/module-1.6-pixie/). Those modules assume you can already explain why verified kernel programs are powerful, where they attach, and what can go wrong when maps, privileges, or kernel compatibility are misunderstood.

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
| 1.2 | [eBPF Security & Networking Deep-Dive](module-1.2-ebpf-security-networking-deepdive/) | 70-85 min | Cilium datapath (XDP/tc/socket, kube-proxy replacement maps), L3/L4 vs L7 split, Tetragon kprobe/LSM enforcement, migration playbook |

## Best Next Steps

After 1.1 and 1.2, apply the mental model in toolkit overviews: [Cilium](/platform/toolkits/infrastructure-networking/networking/module-5.1-cilium/) (operations and policies), [Tetragon](/platform/toolkits/security-quality/security-tools/module-4.5-tetragon/) (TracingPolicy catalog), [KubeArmor](/platform/toolkits/security-quality/security-tools/module-4.6-kubearmor/), and [Hubble](/platform/toolkits/observability-intelligence/observability/module-1.7-hubble/). Module 1.2 is the kernel-datapath companion; 5.1 and 4.5 stay at the tool-overview layer.

---
title: "Module 6.2: Runtime Security with Falco"
slug: k8s/cks/part6-runtime-security/module-6.2-falco
sidebar:
  order: 2
lab:
  id: cks-6.2-falco
  duration: "40 min"
  difficulty: advanced
  environment: kubernetes
---

> **Complexity**: `[MEDIUM]` - Critical CKS skill
>
> **Time to Complete**: 50-55 minutes
>
> **Prerequisites**: Module 6.1 (Audit Logging), Linux system calls basics

---

## Why This Module Matters

In 2018, Tesla's Kubernetes infrastructure was compromised in a massive cryptojacking attack. Hackers did not use a complex zero-day exploit; they found an unsecured administrative dashboard. From there, they extracted credentials, deployed malicious pods, and spawned cryptocurrency mining processes across the infrastructure. The direct financial impact involved thousands of dollars in stolen cloud compute resources, but the potential risk to intellectual property and customer data was catastrophic. 

If the engineers had deployed runtime security tools like Falco, the exact moment the attacker spawned a shell or launched the `xmrig` mining process, a high-priority alert would have been triggered instantly. Instead, the breach operated in the shadows and was only discovered much later due to skyrocketing infrastructure bills. 

Audit logs are essential for visibility, but they only record what passes through the Kubernetes API. They cannot see what happens *inside* a container once it is running. That is where Falco comes in. By operating at the kernel level and intercepting system calls dynamically, Falco provides real-time threat detection for your running workloads. In this module, you will learn to implement, tune, and diagnose Falco alerts to catch threats the moment they materialize.

---

## What You'll Be Able to Do

After completing this exhaustive module, you will be able to:

1. **Implement** custom Falco rules to detect specific container runtime threats such as unauthorized shell execution and sensitive file access.
2. **Diagnose** complex JSON alerts to trace the lineage of a suspicious process across Kubernetes namespaces and physical nodes.
3. **Design** an exception strategy in `falco_rules.local.yaml` to reduce alert fatigue without compromising cluster security.
4. **Evaluate** the architectural and performance tradeoffs between Falco's eBPF probe and traditional kernel module drivers.

---

## What is Falco?

Falco is an open-source, cloud-native runtime security project. It is the de facto Kubernetes threat detection engine, designed to monitor running containers, hosts, and cluster environments. It functions as a security camera for your internal system calls, constantly matching kernel activity against a powerful, flexible rules engine. 

Kubernetes v1.35 introduces robust baseline security mechanisms, but runtime threats require dedicated tooling. Falco continuously monitors system calls—the fundamental interface between user-space applications and the Linux kernel—looking for deviations from expected behavior.

### Architectural Overview

```mermaid
flowchart TD
    C[Container] -->|syscalls| K[Kernel]
    K -->|syscalls| FD[Falco Driver]
    FD --> FE[Falco Engine]
    FE --> R[(Rules)]
    FE -->|Matches| AL[Alerts/Logs]
    
    subgraph Detects
        D1[Shell spawned in container]
        D2[Sensitive file read]
        D3[Process privilege escalation
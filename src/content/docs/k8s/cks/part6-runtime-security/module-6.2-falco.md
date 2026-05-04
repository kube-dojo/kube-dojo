---
title: "Module 6.2: Runtime Security with Falco"
slug: k8s/cks/part6-runtime-security/module-6.2-falco
sidebar:
  order: 2
lab:
  id: cks-6.2-falco
  url: https://killercoda.com/kubedojo/scenario/cks-6.2-falco
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

Modern cluster compromises escalate from an initial foothold to active workload damage in a matter of seconds. Once an attacker breaches the perimeter, they immediately pivot to extracting sensitive credentials, deploying resource-intensive cryptominers, or exfiltrating proprietary data. These post-exploitation activities occur entirely inside the running pods, operating in a blind spot where the standard Kubernetes API audit log structurally cannot see them. The [2018 Tesla cryptojacking attack](/k8s/cks/part1-cluster-setup/module-1.5-gui-security/) <!-- incident-xref: tesla-2018-cryptojacking --> illustrates how adversaries exploit this lack of internal visibility to run malicious processes undetected for extended periods. Generating the deep, granular signal required to catch these anomalous behaviors — specifically the system call traces of malicious processes spawning — demands a dedicated runtime security tool actively listening at the host operating system's kernel level.

Falco has emerged as the definitive open-source standard for generating this real-time behavioral signal. By instrumenting the kernel's system call path, Falco continuously intercepts and analyzes low-level operating system events against a robust, customizable rules engine. This allows security teams to instantly surface deeply hidden threat indicators that the control plane audit log cannot detect. Within milliseconds, Falco can alert operators to interactive shell spawns inside immutable containers, unauthorized reads of sensitive files, unexpected outbound network connections, and sophisticated privilege escalation attempts, providing the critical visibility necessary to halt an attack in progress.

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
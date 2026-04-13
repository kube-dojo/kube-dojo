---
title: "Module 2.2: ServiceAccount Security"
slug: k8s/cks/part2-cluster-hardening/module-2.2-serviceaccount-security
sidebar:
  order: 2
---

> **Complexity**: `[MEDIUM]` - Critical for workload security
>
> **Time to Complete**: 40-45 minutes
>
> **Prerequisites**: Module 2.1 (RBAC Deep Dive), CKA ServiceAccount knowledge

## What You'll Be Able to Do

After completing this rigorous module, you will be able to:

- **Configure** ServiceAccounts across your cluster with `automountServiceAccountToken: false` and strictly scoped RBAC permissions to enforce least privilege.
- **Audit** default ServiceAccount usage across all namespaces to actively find over-exposed credentials and prioritize remediation.
- **Implement** bound service account tokens with explicit expiration and audience restrictions using projected volumes.
- **Diagnose** pod authentication failures (401 vs 403) caused by ServiceAccount misconfigurations using structured troubleshooting flows.
- **Understand bound vs legacy tokens** and evaluate the critical security differences between them in modern Kubernetes architecture.

## Why This Module Matters

In 2018, Tesla's Kubernetes infrastructure was famously breached by attackers who exploited an exposed dashboard. While the initial vector was an exposed dashboard, the fundamental mechanism that allowed the attackers to escalate privileges and commandeer the cluster for illicit cryptomining was deeply tied to ServiceAccount permissions. When an attacker lands inside a compromised pod—whether through a Server-Side Request Forgery (SSRF) vulnerability, a remote code execution (RCE) flaw in a web framework, or a compromised dependency—their very first action is to search for local credentials. By default, Kubernetes makes this effortless by automatically mounting a highly privileged API token directly into the pod's filesystem.

This default behavior prioritizes developer convenience over cluster security. If you do not actively intervene, every single pod deployed into a namespace shares the exact same `default` ServiceAccount. If a cluster administrator ever grants elevated permissions to that default account (a very common anti-pattern used to "just make things work"), every application in that namespace immediately inherits those elevated privileges. A minor vulnerability in a low-priority internal metrics application can thus instantaneously become a cluster-wide compromise, leading to severe data exfiltration, regulatory fines, and millions of dollars in unexpected compute costs from unauthorized workloads.

In this module, you will learn how to systematically break this dangerous default behavior. We will explore how to implement precise, least-privilege configurations for workloads, how the TokenRequest API radically changes the security landscape by introducing time-bound tokens, and how to rigorously audit your cluster for legacy token risks. Securing ServiceAccounts is not merely a theoretical best practice; it is a fundamental pillar of cluster hardening, a core requirement for regulatory compliance, and a major focus area that you must master for the Certified Kubernetes Security Specialist (CKS) exam.

## The ServiceAccount Problem: Defaults are Dangerous

Since Kubernetes v1.0, the default behavior has been to automatically mount credentials into every pod. When a pod is scheduled, the `ServiceAccount` admission controller automatically mutates the pod specification to inject a volume and a volume mount containing the API token.

<details>
<summary>View ASCII Visualization</summary>

```text
┌─────────────────────────────────────────────────────────────┐
│              DEFAULT SERVICEACCOUNT EXPOSURE                │
├────────────────────────────────────────────────────────
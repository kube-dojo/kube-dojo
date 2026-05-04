---
title: "Module 1.2: CIS Benchmarks and kube-bench"
slug: k8s/cks/part1-cluster-setup/module-1.2-cis-benchmarks
sidebar:
  order: 2
---

> **Complexity**: `[MEDIUM]` - Core security auditing skill
>
> **Time to Complete**: 40-45 minutes
>
> **Prerequisites**: Module 0.3 (Security Tools), basic Kubernetes v1.35 administration

## What You'll Be Able to Do

After rigorously studying and practicing the concepts in this module, you will be well-equipped to:

1. **Audit** a modern Kubernetes v1.35 cluster against industry-standard CIS benchmarks using the `kube-bench` utility.
2. **Diagnose** failing benchmark checks by tracing the console output directly to specific misconfigurations in control plane components.
3. **Implement** precise remediation strategies to harden the API server, etcd datastore, and kubelet settings according to strict security guidelines.
4. **Evaluate** which CIS recommendations are absolute requirements for your environment versus those that might conflict with legitimate operational needs.
5. **Design** an automated security scanning pipeline that continuously monitors the cluster's posture against configuration drift.

## Why This Module Matters

Kubernetes defaults are tuned for ease of bring-up, not for hardening. When components are left in their default states, attackers exploit those permissive configurations rather than relying on complex zero-day vulnerabilities. The [2018 Tesla cryptojacking incident](/k8s/cks/part1-cluster-setup/module-1.5-gui-security/) <!-- incident-xref: tesla-2018-cryptojacking --> exemplifies this reality: an exposed, unauthenticated dashboard provided direct administrative cluster access. The Center for Internet Security (CIS) Kubernetes Benchmark exists to systematically close these operational gaps. It provides a comprehensive, standardized framework for hardening the platform — auditing critical vectors like host file permissions, API server authentication flags, restrictive kubelet settings, and etcd encryption. Applying these benchmarks transforms a vulnerable default cluster into a defensible environment, establishing the foundational security baseline required before deploying any production workloads.

This devastating incident could have been entirely prevented if foundational security baselines had been strictly enforced. The CIS (Center for Internet Security) Kubernetes Benchmark exists precisely to prevent these exact "open door" misconfigurations. It provides a consensus-driven, heavily hardened baseline that transforms Kubernetes from a wildly permissive platform by default into a defensible fortress. By enforcing strict rules on file permissions, API server flags, and kubelet settings, the CIS benchmarks ensure that simple configuration oversights do not cascade into catastrophic breaches.

Auditing your cluster against these rigorous benchmarks is not merely an academic exercise or a mundane compliance checkbox—it is a baseline survival requirement in modern platform engineering. Tools like `kube-bench` automate this complex auditing process, providing a clear, actionable roadmap of exactly which files and flags are exposing your organization to risk. Mastering these audits is a core competency for the CKS exam and an absolutely non-negotiable skill for any platform operator responsible for securing Kubernetes v1.35 environments.

## Deep Dive: The Philosophy of CIS

To understand why `kube-bench` is necessary, you must first understand the organization behind the benchmarks. Kubernetes was originally designed for developer velocity and rapid cluster bootstrapping. Historically, this meant that many security settings were relaxed by default to reduce friction. Over time, as Kubernetes became the dominant orchestration engine, the need for standardized security configurations became paramount. 

The Center for Internet Security stepped in to formalize this standard. They gathered security researchers, cloud providers, and platform engineers to create a consensus document. This document maps every single flag, file permission, and network policy to a specific security outcome. 

Here is the traditional CLI output representing the CIS organization's structure:

```text
┌─────────────────────────────────────────────────────────────┐
│              CENTER
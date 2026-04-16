---
title: "CGOA Exam Strategy and Blueprint Review"
slug: k8s/cgoa/module-1.1-exam-strategy-and-blueprint-review
sidebar:
  order: 101
---

> **CGOA Track** | Multiple-choice exam prep | **90 minutes** | **No prerequisites**

## Why This Module Matters

CGOA is a theory exam about GitOps, not a tool certification. You are not being tested on whether you can memorize every ArgoCD or Flux flag. You are being tested on whether you understand the GitOps operating model well enough to recognize good and bad designs.

The exam has five domains:

| Domain | Weight | What it is really testing |
|---|---:|---|
| GitOps Terminology | 20% | Whether you know the language of desired state and drift |
| GitOps Principles | 30% | Whether you understand the OpenGitOps model |
| Related Practices | 16% | Whether you can place IaC, CaC, DevOps, and CI/CD in context |
| GitOps Patterns | 20% | Whether you can compare promotion, rollout, and reconciliation patterns |
| Tooling | 14% | Whether you can reason about ArgoCD, Flux, Helm, Kustomize, and related tools |

## What You'll Learn

After this module, you will be able to:

- choose a study order based on blueprint weight
- recognize the difference between GitOps as a principle set and GitOps as a tool stack
- focus on the terms the exam uses repeatedly
- prepare for comparison questions instead of isolated fact recall

## The Study Order That Works

1. GitOps terminology
2. GitOps principles
3. Related practices such as IaC and DevOps
4. GitOps patterns
5. Tooling comparisons
6. Full practice sets

That order works because the later domains assume the earlier ones. If you do not understand desired state, drift, and reconciliation, the tool questions become guesswork.

## Core Strategy

### Learn The OpenGitOps Language

The exam uses common GitOps terms repeatedly:

- declarative description
- desired state
- state drift
- state reconciliation
- state store
- feedback loop
- rollback

If you can explain those terms in your own words, you are already ahead of most multiple-choice distractors.

### Learn The Principles As A System

The four OpenGitOps principles are not a slogan list. They describe a control loop:

- declarative
- versioned and immutable
- pulled automatically
- continuously reconciled

The best answers on the exam will reflect the whole loop, not just one principle in isolation.

### Learn The Comparison Patterns

The exam likes to compare:

- pull vs event-driven vs push
- GitOps vs CI/CD
- GitOps vs IaC
- ArgoCD vs Flux
- Helm vs Kustomize vs Jsonnet

The right answer usually emphasizes operational consequences, not branding.

## Recommended KubeDojo Review Path

- [What is GitOps?](../../../platform/disciplines/delivery-automation/gitops/module-3.1-what-is-gitops/)
- [Repository Strategies](../../../platform/disciplines/delivery-automation/gitops/module-3.2-repository-strategies/)
- [Environment Promotion](../../../platform/disciplines/delivery-automation/gitops/module-3.3-environment-promotion/)
- [Drift Detection](../../../platform/disciplines/delivery-automation/gitops/module-3.4-drift-detection/)
- [Secrets in GitOps](../../../platform/disciplines/delivery-automation/gitops/module-3.5-secrets/)
- [Multi-cluster GitOps](../../../platform/disciplines/delivery-automation/gitops/module-3.6-multi-cluster/)
- [IaC Fundamentals](../../../platform/disciplines/delivery-automation/iac/module-6.1-iac-fundamentals/)
- [ArgoCD](../../../platform/toolkits/cicd-delivery/gitops-deployments/module-2.1-argocd/)
- [Flux](../../../platform/toolkits/cicd-delivery/gitops-deployments/module-2.3-flux/)
- [Helm & Kustomize](../../../platform/toolkits/cicd-delivery/gitops-deployments/module-2.4-helm-kustomize/)

## Exam-Day Mindset

Keep a simple rule in mind:
- if the answer removes Git as the source of truth, it is probably wrong
- if the answer turns the model into push-based deployment, it is probably wrong
- if the answer ignores reconciliation, it is probably wrong

## Common Mistakes

| Mistake | Why it hurts | Better answer |
|---|---|---|
| Treating GitOps as "using Git for config" | That is too shallow for the exam | Explain pull-based reconciliation and versioned desired state |
| Mixing GitOps with CI/CD | The two work together but solve different problems | Separate build/test from desired-state management |
| Memorizing tools without the model | Tool names can distract from the actual principle | Start with the control loop |
| Confusing drift with normal dynamic state | Not every cluster change is an error | Identify which state should be managed declaratively |

## Next Module

Continue with [CGOA GitOps Principles Review](./module-1.2-gitops-principles-review/).

---
title: "CGOA GitOps Principles Review"
slug: k8s/cgoa/module-1.2-gitops-principles-review
sidebar:
  order: 102
---

> **CGOA Track** | Multiple-choice exam prep | **OpenGitOps principles**

## Why This Module Matters

This is the heart of CGOA. The exam expects you to know the four OpenGitOps principles and the terminology around them well enough to distinguish GitOps from adjacent practices.

The safest way to think about GitOps is as a control loop:
- desired state is declared in Git
- an agent pulls that desired state
- the agent compares desired and actual state
- the agent continuously reconciles drift

If you can explain that in plain language, you can answer a large portion of the exam.

## The Four Principles

### 1. Declarative

The desired state must be expressed declaratively.

That means:
- state is described as an end result
- the system determines how to get there
- configuration is explicit and reviewable

Declarative is not the same as YAML. YAML is often used to express declarative state, but the idea is about intent, not format.

### 2. Versioned And Immutable

Desired state must live in a versioned and immutable source of truth.

That means:
- every change is recorded
- history is auditable
- rollback is possible
- the source of truth is not overwritten casually

Git is the obvious example, but the exam may test the idea rather than the repository brand.

### 3. Pulled Automatically

Software agents pull desired state automatically.

That means:
- the cluster or controller initiates the fetch
- no external system needs push access into the environment
- security boundaries are simpler
- reconciliation can happen on a schedule or event basis

This is one of the biggest GitOps differentiators from traditional push-based CD.

### 4. Continuously Reconciled

The system must continuously observe actual state and try to bring it back to desired state.

That means:
- drift is detected
- unexpected manual changes can be corrected
- the system is self-healing by default
- the loop runs repeatedly, not once

## Terminology You Must Know

| Term | Meaning |
|---|---|
| Desired state | The intended configuration in Git |
| Actual state | The live configuration in the cluster or environment |
| Drift | A mismatch between desired and actual state |
| Reconciliation | Bringing actual state back to desired state |
| State store | The system of record for desired state |
| Rollback | Returning to a prior known-good state |

## Related Practices

GitOps overlaps with but is not identical to:

- Configuration as Code
- Infrastructure as Code
- DevOps
- DevSecOps
- CI/CD

Recommended study anchors:
- [IaC Fundamentals](../../../platform/disciplines/delivery-automation/iac/module-6.1-iac-fundamentals/)
- [What is GitOps?](../../../platform/disciplines/delivery-automation/gitops/module-3.1-what-is-gitops/)
- [Drift Detection](../../../platform/disciplines/delivery-automation/gitops/module-3.4-drift-detection/)
- [ArgoCD](../../../platform/toolkits/cicd-delivery/gitops-deployments/module-2.1-argocd/)
- [Flux](../../../platform/toolkits/cicd-delivery/gitops-deployments/module-2.3-flux/)

## Exam Traps

| Trap | Why it is wrong |
|---|---|
| "GitOps means we store YAML in Git" | That is incomplete; pull-based reconciliation is central |
| "GitOps is the same as CI/CD" | CI/CD builds and deploys; GitOps manages desired state and drift |
| "Any system with Git is GitOps" | Without the control loop, it is just version control for config |
| "Push-based deployment is equivalent" | The exam usually expects you to understand why pull is the GitOps model |

## Common Mistakes

| Mistake | Better approach |
|---|---|
| Memorizing the four principles as isolated words | Learn the control loop they form together |
| Confusing drift with a planned autoscaling change | Distinguish intended dynamic behavior from unmanaged change |
| Forgetting rollback is part of the model | Versioned history is not just for audits; it supports recovery |

## Next Module

Continue with [CGOA Patterns and Tooling Review](./module-1.3-patterns-and-tooling-review/).

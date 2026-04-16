---
title: "CGOA Patterns and Tooling Review"
slug: k8s/cgoa/module-1.3-patterns-and-tooling-review
sidebar:
  order: 103
---

> **CGOA Track** | Multiple-choice exam prep | **Patterns and tooling**

## Why This Module Matters

The exam goes beyond principles and asks whether you can recognize the common operating patterns around GitOps: how repositories are organized, how promotions work, how delivery changes across environments, and how tools fit the model.

This module is where tool names stop being trivia and start becoming architecture.

## What You'll Learn

After this module, you will be able to:

- compare ArgoCD and Flux at a high level
- explain why Helm and Kustomize are usually about packaging and customization, not reconciliation themselves
- identify promotion, rollout, and multi-cluster patterns
- distinguish GitOps from CI/CD and IaC in practical terms

## Part 1: Repository And Promotion Patterns

The exam may ask about:

- monorepo vs polyrepo
- environment promotion
- app-of-apps and layered configuration
- multi-cluster layouts
- how secrets and overlays fit into the flow

The exact repo structure is less important than the principle:
- one source of truth
- explicit promotion
- repeatable rendering
- controlled reconciliation

## Part 2: Tooling Comparisons

### ArgoCD

ArgoCD is often the easiest way to explain the GitOps application model:
- application-centric
- reconciliation focused
- UI and CLI are part of the product
- strong fit for teams that want a visible app-level control plane

### Flux

Flux is a toolkit of specialized controllers:
- source controller
- kustomize controller
- helm controller
- notification controller
- image automation

That makes Flux a strong fit when you want modular building blocks and controller composition.

### Helm And Kustomize

Helm packages and templates. Kustomize patches and overlays.

The exam usually wants you to understand:
- Helm is useful for reusable app packaging
- Kustomize is useful for environment-specific customization
- they can be used together
- neither is itself a GitOps controller

### Where Jsonnet Fits

Jsonnet is a configuration generation language. It is useful to know that it exists, but the exam is more likely to care that you understand why teams use it: reducing duplication and generating manifests in a programmable way.

## Part 3: Pattern And Tool Links

Recommended study anchors:
- [ArgoCD](../../../platform/toolkits/cicd-delivery/gitops-deployments/module-2.1-argocd/)
- [Argo Rollouts](../../../platform/toolkits/cicd-delivery/gitops-deployments/module-2.2-argo-rollouts/)
- [Flux](../../../platform/toolkits/cicd-delivery/gitops-deployments/module-2.3-flux/)
- [Helm & Kustomize](../../../platform/toolkits/cicd-delivery/gitops-deployments/module-2.4-helm-kustomize/)
- [Repository Strategies](../../../platform/disciplines/delivery-automation/gitops/module-3.2-repository-strategies/)
- [Environment Promotion](../../../platform/disciplines/delivery-automation/gitops/module-3.3-environment-promotion/)
- [Multi-cluster GitOps](../../../platform/disciplines/delivery-automation/gitops/module-3.6-multi-cluster/)
- [CI/CD Security](../../../platform/disciplines/reliability-security/devsecops/module-4.3-security-cicd/)

## Common Comparisons

| Comparison | What to remember |
|---|---|
| GitOps vs CI/CD | GitOps manages desired state; CI/CD builds and ships artifacts |
| GitOps vs IaC | IaC is about provisioning infrastructure; GitOps is about the control loop and reconciliation model |
| ArgoCD vs Flux | ArgoCD is application-centric; Flux is controller-centric and more modular |
| Helm vs Kustomize | Helm templates, Kustomize patches |
| Push vs pull | GitOps prefers pull-based reconciliation from inside the target environment |

## Common Mistakes

| Mistake | Why it hurts | Better answer |
|---|---|---|
| Treating ArgoCD and Flux as the same product | They overlap, but their architectures differ | Explain the different operational models |
| Thinking Helm equals GitOps | Helm is packaging, not the control loop | Separate render-time from reconciliation-time |
| Confusing promotion with deployment | Promotion is the controlled movement of a known artifact/configuration | Use the vocabulary carefully |
| Forgetting notifications and observability | The official CGOA domain includes interoperability with these tools | Mention them as part of the operating model |

## Next Module

Continue with [CGOA Practice Questions Set 1](./module-1.4-practice-questions-set-1/).

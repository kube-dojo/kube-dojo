# CI/CD Pipelines Toolkit

> **Toolkit Track** | 3 Modules | ~2.5 hours total

## Overview

The CI/CD Pipelines Toolkit covers modern pipeline orchestration beyond traditional CI systems. These tools represent the next generation of build and deployment automation—programmable, Kubernetes-native, and designed for complex workflows.

This toolkit builds on concepts from [DevSecOps Discipline](../../disciplines/devsecops/README.md) and complements the [GitOps & Deployments Toolkit](../gitops-deployments/README.md).

## Prerequisites

Before starting this toolkit:
- [DevSecOps Discipline](../../disciplines/devsecops/README.md) — CI/CD concepts
- Container fundamentals
- Kubernetes basics
- Programming experience (for Dagger)

## Modules

| # | Module | Complexity | Time |
|---|--------|------------|------|
| 3.1 | [Dagger](module-3.1-dagger.md) | `[COMPLEX]` | 45-50 min |
| 3.2 | [Tekton](module-3.2-tekton.md) | `[COMPLEX]` | 45-50 min |
| 3.3 | [Argo Workflows](module-3.3-argo-workflows.md) | `[COMPLEX]` | 40-45 min |

## Learning Outcomes

After completing this toolkit, you will be able to:

1. **Write Dagger pipelines** — Programmable, portable CI in Go/Python/TypeScript
2. **Build Tekton pipelines** — Kubernetes-native Tasks and Pipelines
3. **Orchestrate Argo Workflows** — DAG-based parallel job execution
4. **Choose the right tool** — Understand trade-offs between approaches

## Tool Selection Guide

```
WHICH PIPELINE TOOL?
─────────────────────────────────────────────────────────────────

"I want pipelines as code, testable and debuggable locally"
└──▶ Dagger
     • Write in Go/Python/TypeScript
     • Run locally or in any CI
     • IDE support, type safety

"I need Kubernetes-native, YAML-based pipelines"
└──▶ Tekton
     • Tasks and Pipelines as CRDs
     • Integrates with OpenShift
     • Catalog of reusable tasks

"I need complex DAGs and parallel data processing"
└──▶ Argo Workflows
     • Sophisticated dependency graphs
     • ML/data pipeline focus
     • Handles thousands of pods

COMPARISON:
─────────────────────────────────────────────────────────────────
                     Dagger       Tekton        Argo Workflows
─────────────────────────────────────────────────────────────────
Language            Code         YAML          YAML
Runs locally        ✓            ✗             ✗
K8s native          ✗            ✓             ✓
DAG support         Basic        Steps only    Full DAG
Parallel loops      ✓            Limited       ✓✓
ML workflows        ✗            ✗             ✓✓
Catalog/Hub         Modules      Hub           ✗
Learning curve      Medium       Medium        High
```

## The Modern CI/CD Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                   MODERN CI/CD STACK                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  DEVELOPER PUSHES CODE                                           │
│       │                                                          │
│       ▼                                                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                  CI PIPELINE                              │   │
│  │                                                           │   │
│  │  Option 1: DAGGER                                         │   │
│  │  • Portable, runs anywhere                                │   │
│  │  • Write in real programming language                     │   │
│  │  • Test locally before pushing                           │   │
│  │                                                           │   │
│  │  Option 2: TEKTON                                         │   │
│  │  • Kubernetes-native                                      │   │
│  │  • Tasks as pods                                          │   │
│  │  • Triggers for webhooks                                  │   │
│  │                                                           │   │
│  │  Option 3: ARGO WORKFLOWS                                 │   │
│  │  • Complex DAGs                                           │   │
│  │  • Data processing                                        │   │
│  │  • ML pipelines                                          │   │
│  └────────────────────────────┬─────────────────────────────┘   │
│                               │                                  │
│                               │ Build artifact (container)       │
│                               ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                  CD PIPELINE                              │   │
│  │                                                           │   │
│  │  ArgoCD / Flux                                            │   │
│  │  • Syncs from Git                                         │   │
│  │  • Progressive delivery                                   │   │
│  │  • GitOps workflow                                        │   │
│  └────────────────────────────┬─────────────────────────────┘   │
│                               │                                  │
│                               ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                  KUBERNETES                               │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Study Path

```
Module 3.1: Dagger
     │
     │  Programmable, portable pipelines
     ▼
Module 3.2: Tekton
     │
     │  Kubernetes-native CI/CD
     ▼
Module 3.3: Argo Workflows
     │
     │  DAG-based orchestration
     ▼
[Toolkit Complete] → Security Tools Toolkit
```

## Key Concepts

### Pipeline Paradigms

| Paradigm | Example | Best For |
|----------|---------|----------|
| **Declarative YAML** | Tekton, GitHub Actions | Simple, standard pipelines |
| **Programmable** | Dagger | Complex logic, testing locally |
| **DAG-based** | Argo Workflows | Parallel processing, ML |

### Common Patterns

```
PATTERN: Fan-out / Fan-in

       ┌──▶ Process 1 ──┐
Input ─┼──▶ Process 2 ──┼──▶ Aggregate
       └──▶ Process 3 ──┘

Use: Parallel testing, data processing
Tool: Argo Workflows excels here

─────────────────────────────────────────────────────────────────

PATTERN: Sequential with Gates

Lint ──▶ Test ──▶ [Approval] ──▶ Build ──▶ Deploy

Use: Standard CI/CD
Tool: All three support this

─────────────────────────────────────────────────────────────────

PATTERN: Matrix Builds

         ┌──▶ Go 1.20 + Linux
Source ──┼──▶ Go 1.21 + Linux
         └──▶ Go 1.21 + Windows

Use: Cross-platform testing
Tool: Dagger and Argo Workflows
```

## Related Tracks

- **Before**: [DevSecOps Discipline](../../disciplines/devsecops/README.md) — CI/CD concepts
- **Related**: [IaC Tools Toolkit](../iac-tools/README.md) — Terraform for pipeline infrastructure
- **Related**: [GitOps & Deployments Toolkit](../gitops-deployments/README.md) — Deploy what CI builds
- **After**: [Security Tools Toolkit](../security-tools/README.md) — Secure the pipeline

---

*"The best pipeline is invisible—developers push code, users get features. These tools make that magic happen."*

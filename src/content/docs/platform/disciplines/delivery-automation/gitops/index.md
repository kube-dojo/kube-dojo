---
title: "GitOps Discipline"
sidebar:
  order: 1
  label: "GitOps"
---
> Git as the single source of truth for infrastructure and applications.

## Overview

GitOps is an operational framework that applies DevOps best practices for infrastructure automation—version control, collaboration, compliance, and CI/CD—to infrastructure configuration. In GitOps, the entire system is described declaratively in Git, and automated processes ensure the actual state matches the desired state.

## Learning Objectives

After completing this track, you will be able to:

- Explain GitOps principles and the reconciliation model
- Design repository strategies for different team structures
- Implement environment promotion workflows
- Configure drift detection and automated remediation
- Manage secrets securely in GitOps workflows
- Architect multi-cluster GitOps for fleet management

## Prerequisites

Before starting this track, you should:

- Understand Kubernetes fundamentals (deployments, services, namespaces)
- Be comfortable with Git workflows (branches, PRs, merges)
- Have experience with YAML configuration files
- Complete the **Systems Thinking** foundation track (recommended)

## Modules

| # | Module | Complexity | Time | Description |
|---|--------|------------|------|-------------|
| 3.1 | [What is GitOps?](module-3.1-what-is-gitops/) | MEDIUM | 35-45 min | GitOps principles, pull vs push, reconciliation |
| 3.2 | [Repository Strategies](module-3.2-repository-strategies/) | MEDIUM | 35-45 min | Monorepo vs polyrepo, app vs config repos |
| 3.3 | [Environment Promotion](module-3.3-environment-promotion/) | MEDIUM | 40-50 min | Directory-based promotion, progressive delivery |
| 3.4 | [Drift Detection](module-3.4-drift-detection/) | MEDIUM | 40-50 min | Types of drift, auto-heal vs alert strategies |
| 3.5 | [Secrets in GitOps](module-3.5-secrets/) | COMPLEX | 50-60 min | Sealed Secrets, SOPS, External Secrets Operator |
| 3.6 | [Multi-Cluster GitOps](module-3.6-multi-cluster/) | COMPLEX | 55-65 min | Fleet management, bootstrapping, hub-spoke patterns |

**Total Time**: ~4-5 hours

## Learning Path

```
Module 3.1: What is GitOps?
    │
    ├── Understand the four principles
    ├── Learn pull vs push models
    └── See reconciliation in action
          │
          ▼
Module 3.2: Repository Strategies
    │
    ├── Choose monorepo vs polyrepo
    ├── Separate app and config repos
    └── Design directory structures
          │
          ▼
Module 3.3: Environment Promotion
    │
    ├── Directory-based promotion
    ├── Image tag strategies
    └── Progressive delivery patterns
          │
          ▼
Module 3.4: Drift Detection
    │
    ├── Identify drift types
    ├── Configure detection
    └── Choose remediation strategy
          │
          ▼
Module 3.5: Secrets in GitOps
    │
    ├── Understand the secrets problem
    ├── Implement encryption patterns
    └── Use external secrets stores
          │
          ▼
Module 3.6: Multi-Cluster GitOps
    │
    ├── Design fleet architectures
    ├── Automate cluster bootstrapping
    └── Implement configuration inheritance
```

## Key Concepts

### The Four GitOps Principles (OpenGitOps)

1. **Declarative** - System state is expressed declaratively
2. **Versioned and Immutable** - Desired state is stored in a way that enforces immutability and versioning
3. **Pulled Automatically** - Agents automatically pull desired state from the source
4. **Continuously Reconciled** - Agents continuously observe and reconcile system state

### Pull vs Push

| Aspect | Push Model | Pull Model (GitOps) |
|--------|------------|---------------------|
| Who deploys | CI/CD pipeline | Agent in cluster |
| Credentials | Pipeline needs cluster access | Cluster only needs Git access |
| Drift | Can occur undetected | Automatically corrected |
| Audit | Scattered in pipeline logs | Centralized in Git history |

### The Reconciliation Loop

```
┌─────────────────────────────────────────────────────────┐
│                    Git Repository                        │
│                   (Desired State)                        │
└────────────────────────┬────────────────────────────────┘
                         │
                         │ 1. Agent polls for changes
                         ▼
┌─────────────────────────────────────────────────────────┐
│                   GitOps Agent                           │
│              (ArgoCD, Flux, etc.)                        │
│                                                          │
│  2. Compare desired state vs actual state                │
│  3. If different, reconcile                              │
└────────────────────────┬────────────────────────────────┘
                         │
                         │ 4. Apply changes to cluster
                         ▼
┌─────────────────────────────────────────────────────────┐
│                  Kubernetes Cluster                      │
│                   (Actual State)                         │
└─────────────────────────────────────────────────────────┘
```

## Related Tracks

**Foundations** (Start here if new to these concepts):
- [Systems Thinking](../../foundations/systems-thinking/) - Feedback loops and emergent behavior
- [Reliability Engineering](../../foundations/reliability-engineering/) - Change management principles

**Disciplines** (Apply GitOps in context):
- [SRE Discipline](../sre/) - Operationalizing GitOps for reliability
- [DevSecOps Discipline](../devsecops/) - Security in GitOps pipelines
- [Platform Engineering](../platform-engineering/) - Self-service GitOps platforms
- [IaC Discipline](../iac/) - Infrastructure as Code with GitOps delivery

**Toolkits** (Deep dive into specific tools):
- [GitOps Tools](../../toolkits/cicd-delivery/gitops-deployments/) - ArgoCD, Flux, and related tools

## Tools You'll Encounter

| Tool | Purpose |
|------|---------|
| **ArgoCD** | Kubernetes-native GitOps controller |
| **Flux** | CNCF GitOps toolkit |
| **Kustomize** | Configuration customization |
| **Helm** | Package management |
| **Sealed Secrets** | Encrypt secrets for Git |
| **SOPS** | Secrets encryption |
| **External Secrets Operator** | Sync from external stores |

## Progress Checklist

- [ ] Module 3.1: What is GitOps? - Understand principles
- [ ] Module 3.2: Repository Strategies - Design repo structure
- [ ] Module 3.3: Environment Promotion - Implement promotion flow
- [ ] Module 3.4: Drift Detection - Configure detection and remediation
- [ ] Module 3.5: Secrets in GitOps - Secure secret management
- [ ] Module 3.6: Multi-Cluster GitOps - Scale to fleet management

## Quick Reference

### GitOps Workflow

```bash
# Developer workflow
1. git checkout -b feature/new-config
2. # Make changes to desired state
3. git commit -m "Update replica count"
4. git push && open PR
5. # PR reviewed and merged
6. # GitOps agent automatically deploys
```

### Common Commands

```bash
# ArgoCD
argocd app list
argocd app sync <app>
argocd app diff <app>

# Flux
flux get kustomizations
flux reconcile kustomization <name>
flux diff kustomization <name>

# Sealed Secrets
kubeseal --format yaml < secret.yaml > sealed-secret.yaml
```

### Key Patterns

| Pattern | When to Use |
|---------|-------------|
| **App-of-Apps** | Managing multiple related applications |
| **Directory-per-environment** | Clear environment separation |
| **Base + Overlays** | Configuration inheritance |
| **External Secrets** | Integration with secret managers |
| **Hub-Spoke** | Centralized fleet management |

## Further Reading

- [OpenGitOps Principles](https://opengitops.dev/)
- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [Flux Documentation](https://fluxcd.io/flux/)
- [GitOps: Theory and Practice](https://www.weave.works/technologies/gitops/)

---
title: "Developer Experience Toolkit"
sidebar:
  order: 1
  label: "Developer Experience"
---
> **Toolkit Track** | 5 Modules | ~3.5 hours total

## Overview

The Developer Experience Toolkit covers tools that make daily Kubernetes work faster and more productive. k9s provides a terminal UI for rapid cluster navigation, Telepresence and Tilt enable local development against remote clusters, and local Kubernetes options (kind, minikube) give you disposable environments for testing.

These tools apply concepts from [Platform Engineering Discipline](../../disciplines/core-platform/platform-engineering/) to improve developer productivity.

## Prerequisites

Before starting this toolkit:
- Basic kubectl familiarity
- Docker installed
- Terminal/CLI basics
- Kubernetes resource concepts

## Modules

| # | Module | Complexity | Time |
|---|--------|------------|------|
| 8.1 | [k9s & CLI Tools](module-8.1-k9s-cli/) | `[QUICK]` | 30-35 min |
| 8.2 | [Telepresence & Tilt](module-8.2-telepresence-tilt/) | `[MEDIUM]` | 40-45 min |
| 8.3 | [Local Kubernetes](module-8.3-local-kubernetes/) | `[QUICK]` | 30-35 min |
| 8.4 | [DevPod](module-8.4-devpod/) | `[MEDIUM]` | 45-50 min |
| 8.5 | [Gitpod & Codespaces](module-8.5-gitpod-codespaces/) | `[MEDIUM]` | 45-50 min |

## Learning Outcomes

After completing this toolkit, you will be able to:

1. **Navigate clusters efficiently** — k9s, kubectl plugins, aliases
2. **Develop locally with remote clusters** — Telepresence intercepts
3. **Automate development workflows** — Tilt for live updates
4. **Run local Kubernetes** — kind, minikube, Docker Desktop
5. **Use cloud development environments** — DevPod, Gitpod, Codespaces

## Tool Selection Guide

```
WHICH DEVELOPER TOOL?
─────────────────────────────────────────────────────────────────

"I want faster kubectl / visual cluster navigation"
└──▶ k9s
     • Terminal UI for Kubernetes
     • Instant resource navigation
     • Built-in logs, shell, port-forward
     • No more long kubectl commands

"I need to test my local code against a remote cluster"
└──▶ Telepresence
     • Route cluster traffic to local process
     • Debug production issues locally
     • No container builds needed
     • Real cluster services available

"I want automatic rebuilds when code changes"
└──▶ Tilt
     • Watch files, rebuild, redeploy
     • Live updates without restart
     • Multi-service orchestration
     • Custom workflows in Tiltfile

"I need a local Kubernetes cluster"
└──▶ kind / minikube / Docker Desktop
     • kind: Fast, CI-friendly, multi-node
     • minikube: Feature-rich, addons, GPU
     • Docker Desktop: Simple, already there

DEVELOPER WORKFLOW STACK:
─────────────────────────────────────────────────────────────────
                     Your Development Machine
─────────────────────────────────────────────────────────────────
                              │
    ┌─────────────────────────┼─────────────────────────┐
    │                         │                         │
    ▼                         ▼                         ▼
┌─────────┐            ┌─────────────┐            ┌─────────┐
│   k9s   │            │    Tilt     │            │  kind   │
│  (view) │            │   (build)   │            │ (local) │
└─────────┘            └─────────────┘            └─────────┘
    │                         │                         │
    └─────────────────────────┼─────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   Telepresence  │
                    │   (intercept)   │
                    └─────────────────┘
                              │
                              ▼
                    Remote Kubernetes Cluster
```

## The Developer Experience Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                 DEVELOPER EXPERIENCE STACK                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  CLUSTER INTERACTION                                            │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  k9s                                                       │ │
│  │  • Visual navigation  • Logs  • Shell  • Port-forward     │ │
│  │                                                            │ │
│  │  kubectl plugins (krew)                                    │ │
│  │  • ctx/ns switching  • neat YAML  • tree  • who-can       │ │
│  │                                                            │ │
│  │  stern                                                     │ │
│  │  • Multi-pod log tailing  • Color-coded  • Regex match    │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              │                                   │
│  LOCAL DEVELOPMENT                                              │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Telepresence                                              │ │
│  │  • Intercept cluster traffic  • Local debugging           │ │
│  │                                                            │ │
│  │  Tilt                                                      │ │
│  │  • File watching  • Live updates  • Multi-service         │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              │                                   │
│  LOCAL CLUSTERS                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  kind           │  minikube        │  Docker Desktop      │ │
│  │  (CI, multi-node)  (addons, GPU)     (simple, quick)      │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Study Path

```
Module 8.1: k9s & CLI Tools
     │
     │  Faster cluster navigation
     │  Plugins, aliases, productivity
     ▼
Module 8.2: Telepresence & Tilt
     │
     │  Local development workflows
     │  Remote cluster integration
     ▼
Module 8.3: Local Kubernetes
     │
     │  Local cluster options
     │  kind, minikube comparison
     ▼
[Toolkit Complete] → Apply to daily work!
```

## Key Concepts

### Productivity Principles

| Principle | Tool | Implementation |
|-----------|------|----------------|
| **Visual feedback** | k9s | See cluster state instantly |
| **Fast iteration** | Tilt | Automatic rebuild on save |
| **Real environment** | Telepresence | Test against real services |
| **Disposable clusters** | kind | Fresh environment per task |

### Tool Categories

```
DEVELOPER EXPERIENCE CATEGORIES
─────────────────────────────────────────────────────────────────

NAVIGATION & PRODUCTIVITY
├── k9s - Terminal UI
├── kubectl plugins - Extended commands
├── stern - Multi-pod logging
├── kubecolor - Colored output
└── shell aliases - Quick commands

DEVELOPMENT WORKFLOWS
├── Telepresence - Remote development
├── Tilt - Build automation
├── Skaffold - CI/CD development
└── DevSpace - Development environments

LOCAL CLUSTERS
├── kind - Kubernetes IN Docker
├── minikube - Feature-rich local K8s
├── Docker Desktop - Built-in K8s
├── k3d - k3s in Docker
└── Rancher Desktop - k3s alternative
```

## Common Workflows

### Daily Development

```
TYPICAL DEVELOPER DAY
─────────────────────────────────────────────────────────────────

Morning: Check cluster state
$ k9s                          # Visual overview
$ :pods                        # See all pods
$ /my-service                  # Filter to my work

Development: Code → Test cycle
$ tilt up                      # Start development
[Edit code]                    # Tilt auto-rebuilds
[Browser: localhost]           # See changes instantly

Debugging: Production issue
$ telepresence connect         # Connect to cluster
$ telepresence intercept api   # Route traffic locally
[Local debugger]               # Step through code
$ telepresence leave           # Done debugging

Testing: New feature
$ kind create cluster          # Fresh cluster
$ kubectl apply -f manifests/  # Deploy
[Test feature]                 # Validate
$ kind delete cluster          # Clean up
```

### CI/CD Development

```
CI/CD DEVELOPMENT WORKFLOW
─────────────────────────────────────────────────────────────────

Local development:
┌─────────────────────────────────────────────────────────────┐
│  kind cluster + Tilt                                         │
│  • Fast iteration                                           │
│  • Multi-node testing                                       │
│  • Mirror production setup                                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Push
                              ▼
CI pipeline:
┌─────────────────────────────────────────────────────────────┐
│  kind in CI (GitHub Actions, etc.)                          │
│  • Same local setup works in CI                             │
│  • Integration tests against real K8s                       │
│  • Ephemeral, reproducible                                  │
└─────────────────────────────────────────────────────────────┘
```

## Hands-On Focus

| Module | Key Exercise |
|--------|--------------|
| k9s & CLI | Install k9s, navigate cluster, set up aliases |
| Telepresence & Tilt | Intercept service, create Tiltfile |
| Local Kubernetes | Create kind cluster, load local images |

## Tool Comparison

```
LOCAL KUBERNETES OPTIONS
─────────────────────────────────────────────────────────────────

                   kind           minikube         Docker Desktop
─────────────────────────────────────────────────────────────────
Multi-node         ✓✓             ✓                ✗
Speed              Fast           Medium           Fast
Resources          Low            Medium           Low
GPU support        ✗              ✓                ✓
Addons             Manual         Built-in         Manual
Best for           CI/CD, testing Learning         Quick start
─────────────────────────────────────────────────────────────────

DEVELOPMENT TOOLS
─────────────────────────────────────────────────────────────────

                   Telepresence   Tilt             Skaffold
─────────────────────────────────────────────────────────────────
Purpose            Intercept      Build/deploy     Build/deploy
Local process      ✓              ✗                ✗
Hot reload         ✗              ✓                ✓
Multi-service      Via intercepts ✓                ✓
Best for           Debugging      Development      CI/CD
─────────────────────────────────────────────────────────────────
```

## Related Tracks

- **Before**: [Platforms Toolkit](../platforms/) — Portal and infrastructure
- **Applies**: [Platform Engineering Discipline](../../disciplines/core-platform/platform-engineering/) — Developer experience concepts
- **Related**: [IaC Discipline](../../disciplines/delivery-automation/iac/) — Infrastructure provisioning patterns
- **Related**: [CI/CD Pipelines Toolkit](../ci-cd-pipelines/) — Build and deploy automation
- **Related**: [GitOps & Deployments Toolkit](../gitops-deployments/) — Deployment workflows

---

*"Developer experience isn't about fancy tools—it's about removing friction. Every second saved compounds into hours of productivity."*

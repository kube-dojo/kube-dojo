---
title: "Platforms Toolkit"
sidebar:
  order: 1
  label: "Platforms"
---
> **Toolkit Track** | 3 Modules | ~2.5 hours total

## Overview

The Platforms Toolkit covers the building blocks of Internal Developer Platforms. Backstage provides the developer portal, Crossplane enables self-service infrastructure, and cert-manager automates TLS certificate management. Together, they form the foundation of a modern platform engineering stack.

This toolkit applies concepts from [Platform Engineering Discipline](../../disciplines/core-platform/platform-engineering/).

## Prerequisites

Before starting this toolkit:
- [Platform Engineering Discipline](../../disciplines/core-platform/platform-engineering/)
- Kubernetes CRD concepts
- Basic cloud provider knowledge
- TLS/PKI fundamentals

## Modules

| # | Module | Complexity | Time |
|---|--------|------------|------|
| 7.1 | [Backstage](module-7.1-backstage/) | `[COMPLEX]` | 50-60 min |
| 7.2 | [Crossplane](module-7.2-crossplane/) | `[COMPLEX]` | 50-60 min |
| 7.3 | [cert-manager](module-7.3-cert-manager/) | `[MEDIUM]` | 40-45 min |
| 3.4 | [Kubebuilder](module-3.4-kubebuilder/) | `[COMPLEX]` | 55 min |
| 3.5 | [Cluster API](module-3.5-cluster-api/) | `[COMPLEX]` | 50 min |
| 3.6 | [vCluster](module-3.6-vcluster/) | `[MEDIUM]` | 40 min |

## Learning Outcomes

After completing this toolkit, you will be able to:

1. **Deploy Backstage** — Software catalog, TechDocs, templates
2. **Configure Crossplane** — Self-service infrastructure APIs
3. **Manage certificates** — Automated TLS with cert-manager
4. **Build platform foundations** — Combine tools for developer experience

## Tool Selection Guide

```
WHICH PLATFORM TOOL?
─────────────────────────────────────────────────────────────────

"I need a developer portal / service catalog"
└──▶ Backstage
     • Service ownership
     • Documentation hub
     • Golden path templates
     • Plugin ecosystem

"I need self-service infrastructure for developers"
└──▶ Crossplane
     • Kubernetes-native IaC (see [IaC Discipline](../../disciplines/delivery-automation/iac/))
     • Custom APIs with Compositions
     • GitOps-friendly
     • Multi-cloud

"I need automated TLS certificate management"
└──▶ cert-manager
     • Let's Encrypt automation
     • Internal PKI
     • Certificate lifecycle
     • Ingress integration

PLATFORM STACK:
─────────────────────────────────────────────────────────────────
                    Developer Self-Service
─────────────────────────────────────────────────────────────────
                         │
    ┌────────────────────┼────────────────────┐
    │                    │                    │
    ▼                    ▼                    ▼
┌─────────┐       ┌─────────────┐       ┌─────────┐
│Backstage│       │  Crossplane │       │cert-mgr │
│ Portal  │       │   Infra     │       │   TLS   │
└─────────┘       └─────────────┘       └─────────┘
    │                    │                    │
    ▼                    ▼                    ▼
Templates         Cloud Resources      Certificates
Docs              (RDS, S3, etc)       (Auto-renewal)
Catalog
```

## The Platform Stack

```
┌─────────────────────────────────────────────────────────────────┐
│              INTERNAL DEVELOPER PLATFORM (IDP)                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  DEVELOPER PORTAL                                               │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Backstage                                                 │ │
│  │  • Service Catalog  • TechDocs  • Templates  • Plugins    │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              │                                   │
│  SELF-SERVICE APIs                                              │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Crossplane Compositions                                   │ │
│  │  "Database" → RDS + Security Group + Monitoring           │ │
│  │  "Queue" → SQS + DLQ + Alerts                             │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              │                                   │
│  INFRASTRUCTURE                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  cert-manager  │  External Secrets  │  Ingress Controller │ │
│  │  (TLS)           (Secrets sync)       (Traffic routing)    │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Study Path

```
Module 7.1: Backstage
     │
     │  Developer portal foundation
     │  Service catalog, docs, templates
     ▼
Module 7.2: Crossplane
     │
     │  Self-service infrastructure
     │  Custom APIs, GitOps
     ▼
Module 7.3: cert-manager
     │
     │  Automated TLS
     │  Certificate lifecycle
     ▼
[Toolkit Complete] → Developer Experience Toolkit
```

## Key Concepts

### Platform Engineering Principles

| Principle | Tool | Implementation |
|-----------|------|----------------|
| **Self-service** | Crossplane | Custom APIs for infrastructure |
| **Golden paths** | Backstage | Software templates |
| **Discoverability** | Backstage | Service catalog |
| **Automation** | cert-manager | Certificate lifecycle |

### Building Blocks

```
PLATFORM BUILDING BLOCKS
─────────────────────────────────────────────────────────────────

PORTAL (Backstage)
├── Service Catalog - What services exist?
├── Ownership - Who owns what?
├── Documentation - How do I use it?
├── Templates - How do I create new things?
└── Plugins - Kubernetes, CI/CD, monitoring

INFRASTRUCTURE (Crossplane)
├── Providers - AWS, GCP, Azure
├── Managed Resources - Direct cloud resources
├── Compositions - Custom APIs
└── Claims - Self-service requests

SECURITY (cert-manager)
├── Issuers - Let's Encrypt, internal CA
├── Certificates - TLS for services
├── Auto-renewal - No manual intervention
└── Integration - Ingress annotations
```

## Integration Patterns

### Backstage + Crossplane

```yaml
# Backstage template that creates Crossplane resources
apiVersion: scaffolder.backstage.io/v1beta3
kind: Template
metadata:
  name: microservice-with-database
spec:
  steps:
  - id: create-database
    name: Create Database
    action: kubernetes:apply
    input:
      manifest:
        apiVersion: platform.example.com/v1alpha1
        kind: DatabaseClaim
        metadata:
          name: ${{ parameters.name }}-db
        spec:
          size: small
```

### Crossplane + cert-manager

```yaml
# Crossplane composition that includes certificate
apiVersion: apiextensions.crossplane.io/v1
kind: Composition
spec:
  resources:
  - name: ingress
    base:
      apiVersion: networking.k8s.io/v1
      kind: Ingress
      metadata:
        annotations:
          cert-manager.io/cluster-issuer: letsencrypt-prod
```

## Common Architectures

### Full Platform Stack

```
COMPLETE PLATFORM ARCHITECTURE
─────────────────────────────────────────────────────────────────

                    Developer
                       │
                       │ Backstage UI
                       ▼
              ┌─────────────────┐
              │    Backstage    │
              │    (Portal)     │
              └────────┬────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
┌───────────┐  ┌───────────┐  ┌───────────┐
│ Template  │  │  Catalog  │  │  Plugins  │
│ (create)  │  │  (view)   │  │ (extend)  │
└─────┬─────┘  └───────────┘  └───────────┘
      │
      │ Creates resources
      ▼
┌─────────────────────────────────────────┐
│              Kubernetes                  │
│                                         │
│  ┌───────────┐  ┌───────────┐          │
│  │Crossplane │  │cert-manager│          │
│  │  Claim    │  │Certificate │          │
│  └─────┬─────┘  └─────┬─────┘          │
│        │              │                 │
└────────┼──────────────┼─────────────────┘
         │              │
         ▼              ▼
    Cloud Resources   TLS Certs
    (RDS, S3, etc)    (auto-renewed)
```

## Hands-On Focus

| Module | Key Exercise |
|--------|--------------|
| Backstage | Deploy portal, register service, create template |
| Crossplane | Create composition, provision cloud resource |
| cert-manager | Configure issuer, create certificate |

## Related Tracks

- **Before**: [Platform Engineering Discipline](../../disciplines/core-platform/platform-engineering/)
- **Before**: [IaC Discipline](../../disciplines/delivery-automation/iac/) — Infrastructure as Code fundamentals
- **Related**: [GitOps & Deployments](../gitops-deployments/) — Deploy platform resources
- **Related**: [Security Tools](../security-tools/) — Secure the platform
- **Related**: [IaC Tools](../iac-tools/) — Terraform, OpenTofu, Pulumi hands-on
- **After**: [Developer Experience](../developer-experience/) — Day-to-day tools

---

*"A platform is successful when developers don't need to think about infrastructure. These tools make that possible."*

---
title: "IaC Tools Toolkit"
sidebar:
  order: 0
  label: "IaC Tools"
---
> **Toolkit Track** | 13 Modules | ~13 hours total

## Overview

The IaC Tools Toolkit covers the major infrastructure as code tools in depth. From HashiCorp's Terraform to OpenTofu, from Pulumi's programming language approach to Ansible's configuration management, from CloudFormation to Bicep, and from Ansible roles to Kubernetes-native Ansible Operators—this toolkit gives you hands-on experience with the tools that define modern infrastructure.

This toolkit applies concepts from [IaC Discipline](../../../disciplines/delivery-automation/iac/).

## Prerequisites

Before starting this toolkit:
- [IaC Discipline](../../../disciplines/delivery-automation/iac/) — IaC fundamentals, testing, security
- [IaC Fundamentals](../../../disciplines/delivery-automation/iac/module-6.1-iac-fundamentals/) — Core concepts (minimum)
- Cloud provider account (AWS, Azure, or GCP for exercises)
- Basic command-line experience

## Modules

| # | Module | Complexity | Time |
|---|--------|------------|------|
| 7.1 | [Terraform Deep Dive](module-7.1-terraform/) | `[COMPLEX]` | 60 min |
| 7.2 | [OpenTofu](module-7.2-opentofu/) | `[MEDIUM]` | 45-50 min |
| 7.3 | [Pulumi](module-7.3-pulumi/) | `[COMPLEX]` | 55-60 min |
| 7.4 | [Ansible](module-7.4-ansible/) | `[COMPLEX]` | 55-60 min |
| 7.5 | [CloudFormation](module-7.5-cloudformation/) | `[MEDIUM]` | 45-50 min |
| 7.6 | [Bicep](module-7.6-bicep/) | `[MEDIUM]` | 45-50 min |
| 7.7 | [Wing](module-7.7-winglang/) | `[COMPLEX]` | 50-55 min |
| 7.8 | [SST](module-7.8-sst/) | `[MEDIUM]` | 45-50 min |
| 7.9 | [System Initiative](module-7.9-system-initiative/) | `[COMPLEX]` | 50-55 min |
| 7.10 | [Nitric](module-7.10-nitric/) | `[MEDIUM]` | 45-50 min |
| 7.11 | [HCP Terraform Workflow Operations](module-7.11-hcp-terraform-workflows/) | `[COMPLEX]` | 60-70 min |
| 7.12 | [Ansible Operator SDK Fundamentals](module-7.12-ansible-operator-sdk/) | `[COMPLEX]` | ~90 min |
| 7.13 | [Advanced watches.yaml Patterns](module-7.13-advanced-watches-yaml/) | `[COMPLEX]` | ~100 min |
| 7.15 | [Helm vs Ansible vs Go Operator Decision Framework](module-7.15-helm-ansible-go-operator-decision/) | `[COMPLEX]` | ~90 min |
| 7.16 | [Production Ansible Operator Patterns](module-7.16-production-ansible-operator-patterns/) | `[EXPERT]` | ~120 min |
| 7.17 | [Testing Ansible Operators with Molecule and Kuttl](module-7.17-testing-ansible-operators/) | `[COMPLEX]` | ~100 min |

## Learning Outcomes

After completing this toolkit, you will be able to:

1. **Write production Terraform** — Modules, workspaces, state backends, providers
2. **Migrate to OpenTofu** — Understand the fork, migration path, differences
3. **Use Pulumi** — Infrastructure in TypeScript, Python, Go
4. **Manage configuration with Ansible** — Playbooks, roles, inventory
5. **Deploy with CloudFormation** — AWS-native IaC, nested stacks, macros
6. **Use Bicep** — Azure-native IaC, simplified ARM templates
7. **Understand Wing** — Cloud-oriented programming language
8. **Develop with SST** — Modern serverless framework with live Lambda
9. **Explore System Initiative** — Reactive, visual DevOps automation
10. **Build with Nitric** — Cloud-agnostic application framework
11. **Operate Terraform at organizational scale** — HCP Terraform workspaces, dynamic provider credentials, Sentinel/OPA policy gates, drift detection, and private module registry workflows
12. **Build Ansible Operators** — Map Kubernetes custom resources to Ansible roles with Operator SDK, `watches.yaml`, `kubernetes.core`, and status-aware reconciliation
13. **Choose the right operator implementation style** — Score a requirement across twelve decision axes (complexity, state-machine fit, OLM tier, upgrade safety, and more) to select Helm, Ansible, or Go, and plan incremental migrations as requirements grow
14. **Operate Ansible Operators in production** — Status conditions, finalizer safety, idempotency at scale, CRD upgrade strategies, leader election, OLM bundles, and operator observability
15. **Master advanced watches.yaml patterns** — Multi-CRD operators, namespace scoping, cluster-scoped RBAC, watchDependentResources + blacklist filtering, finalizer mapping, selector filters, and worker concurrency tuning via ANSIBLE_WORKERS
16. **Test Ansible Operators** — Design a layered test strategy using Molecule (role-level unit and integration), Kuttl (end-to-end CRD reconciliation), and operator-sdk scorecard (OLM bundle validation)

## Tool Selection Guide

```
WHICH IAC TOOL?
─────────────────────────────────────────────────────────────────

"I need multi-cloud infrastructure provisioning"
└──▶ Terraform / OpenTofu
     • Declarative HCL syntax
     • Provider ecosystem (AWS, Azure, GCP, K8s, etc.)
     • State management built-in
     • Largest community

"I want to use my programming language (TypeScript, Python, Go)"
└──▶ Pulumi
     • Real programming languages
     • Better testing capabilities
     • Complex logic support
     • Reuse existing libraries

"I need AWS-only with native integration"
└──▶ CloudFormation
     • Deep AWS integration
     • Stack drift detection
     • StackSets for multi-account
     • No state file management

"I need Azure-only with simplified syntax"
└──▶ Bicep
     • Azure-first design
     • Cleaner than ARM templates
     • Built into Azure CLI
     • No state file management

"I need configuration management (post-provisioning)"
└──▶ Ansible
     • Agentless (SSH/WinRM)
     • Idempotent operations
     • Procedural + declarative
     • Great for OS configuration

"I want an Ansible role to reconcile Kubernetes custom resources"
└──▶ Ansible Operator SDK
     • Kubernetes controller shell from Operator SDK
     • Reconcile logic implemented as Ansible roles
     • `watches.yaml` maps CRDs to roles or playbooks
     • Strong when platform teams already own Ansible automation
     • Production patterns (status conditions, finalizers, OLM): Module 7.16

"I need to choose between Helm, Ansible, and Go for a Kubernetes operator"
└──▶ Module 7.15: Helm vs Ansible vs Go Operator Decision Framework
     • 12-axis decision matrix covering complexity, state-machine fit, OLM tier
     • Worked examples: cert-manager (Helm), MinIO (Ansible), Crossplane (Go)
     • OperatorHub.io capability level requirements per style
     • Migration paths from Helm → Ansible → Go

"I want Terraform without HashiCorp licensing concerns"
└──▶ OpenTofu
     • 1:1 Terraform compatible
     • Linux Foundation governance
     • Community-driven
     • Drop-in replacement

"I want unified infrastructure and application code"
└──▶ Wing
     • Cloud-oriented programming language
     • Compiles to Terraform + Lambda
     • Built-in local simulator
     • Preflight/inflight model

"I want fast serverless development with live reload"
└──▶ SST
     • Live Lambda development
     • Real AWS, instant reload
     • Full-stack support (Lambda, Next.js, etc.)
     • TypeScript-first

"I want visual, reactive infrastructure automation"
└──▶ System Initiative
     • Canvas-based visual editing
     • Reactive dependency propagation
     • Real-time collaboration
     • Function-based extensibility

"I want to deploy the same code to any cloud"
└──▶ Nitric
     • Cloud-agnostic APIs
     • Infrastructure derived from code
     • AWS, Azure, GCP support
     • TypeScript, Python, Go, Dart
```

## Tool Comparison Matrix

| Feature | Terraform | OpenTofu | Pulumi | Ansible | CloudFormation | Bicep |
|---------|-----------|----------|--------|---------|----------------|-------|
| **Language** | HCL | HCL | TypeScript/Python/Go | YAML | YAML/JSON | Bicep DSL |
| **State** | Required | Required | Required | None | Managed | Managed |
| **Multi-cloud** | Yes | Yes | Yes | Yes | AWS only | Azure only |
| **Learning curve** | Medium | Medium | Higher | Low | Medium | Low |
| **Testing** | Terratest | Terratest | Native | Molecule | TaskCat | ARM TTK |
| **Drift detection** | Plan | Plan | Preview | Check mode | Drift detection | What-if |
| **License** | BSL 1.1 | MPL 2.0 | Apache 2.0 | GPL 3.0 | Proprietary | MIT |

## The IaC Landscape

```
┌─────────────────────────────────────────────────────────────────┐
│                    IAC TOOL LANDSCAPE                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  PROVISIONING (Infrastructure Creation)                          │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                                                              ││
│  │  Multi-Cloud              Cloud-Native                       ││
│  │  ┌────────────┐          ┌────────────┐                     ││
│  │  │ Terraform  │          │CloudForm.  │ (AWS)               ││
│  │  │ OpenTofu   │          │ Bicep      │ (Azure)             ││
│  │  │ Pulumi     │          │ GCP DM     │ (GCP)               ││
│  │  └────────────┘          └────────────┘                     ││
│  │                                                              ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  CONFIGURATION (Post-Provisioning)                               │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  Ansible  │  Chef  │  Puppet  │  Salt                       ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  KUBERNETES-NATIVE                                               │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  Crossplane  │  Cluster API  │  Pulumi K8s                  ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Study Path

```
Module 7.1: Terraform Deep Dive
     │
     │  The industry standard
     │  Providers, modules, state
     ▼
Module 7.2: OpenTofu
     │
     │  Open-source alternative
     │  Migration from Terraform
     ▼
Module 7.3: Pulumi
     │
     │  Programming languages for IaC
     │  Testing with real code
     ▼
Module 7.4: Ansible
     │
     │  Configuration management
     │  Playbooks and roles
     ▼
Module 7.5: CloudFormation
     │
     │  AWS-native IaC
     │  Stacks and StackSets
     ▼
Module 7.6: Bicep
     │
     │  Azure-native IaC
     │  ARM template evolution
     ▼
Module 7.7: Wing
     │
     │  Cloud-oriented language
     │  Unified infra and code
     ▼
Module 7.8: SST
     │
     │  Live Lambda development
     │  Modern serverless
     ▼
Module 7.9: System Initiative
     │
     │  Visual, reactive IaC
     │  Collaboration built-in
     ▼
Module 7.10: Nitric
     │
     │  Cloud-agnostic framework
     │  Deploy anywhere
     ▼
Module 7.11: HCP Terraform Workflow Operations
     │
     │  Remote runs, governance, drift
     │  Operate Terraform at org scale
     ▼
Module 7.12: Ansible Operator SDK Fundamentals
     │
     │  Map CRDs to Ansible roles
     │  Build a minimum viable operator
     ▼
Module 7.15: Helm vs Ansible vs Go Operator Decision Framework
     │
     │  12-axis decision matrix
     │  Three worked examples, all 3 flavors on kind
     ▼
Module 7.13: Advanced watches.yaml Patterns
     │
     │  Multi-CRD, namespace scoping, finalizers
     │  blacklist filtering + ANSIBLE_WORKERS tuning
     ▼
Module 7.16: Production Ansible Operator Patterns
     │
     │  Status conditions, finalizers, idempotency at scale
     │  Leader election, OLM, observability, chaos testing
     ▼
Module 7.17: Testing Ansible Operators with Molecule and Kuttl
     │
     │  Molecule role-level unit and integration tests
     │  Kuttl E2E CRD reconciliation tests
     ▼
[Toolkit Complete] → Apply to production
```

## Hands-On Focus

| Module | Key Exercise |
|--------|--------------|
| Terraform | Build multi-environment setup with modules |
| OpenTofu | Migrate existing Terraform project |
| Pulumi | Deploy infrastructure with TypeScript |
| Ansible | Configure servers with roles and inventory |
| CloudFormation | Create nested stack with drift detection |
| Bicep | Deploy Azure resources with parameters |
| Wing | Build image processing pipeline with simulator |
| SST | URL shortener with live Lambda development |
| System Initiative | Reactive VPC with automatic subnet calculation |
| Nitric | Multi-cloud notes API deployed everywhere |
| HCP Terraform | VCS-driven workflow with dynamic credentials and policy gates |
| Ansible Operator SDK | Build a DemoApp custom resource reconciled by an Ansible role |
| Advanced watches.yaml | Multi-CRD operator with namespace scoping, blacklist filtering, and finalizer |
| Helm vs Ansible vs Go Decision | Build all three operator styles against the same WebApp CRD on kind; compare line counts, debugging, and capability ceilings |
| Production Ansible Operator Patterns | Deploy operator with HA leader election, create 100 CRs, inject leader transition, measure reconciliation latency |
| Testing Ansible Operators | Molecule delegated + docker + kind scenarios, Kuttl E2E create/delete assertions on kind |

## Related Tracks

- **Before**: [IaC Discipline](../../../disciplines/delivery-automation/iac/) — IaC fundamentals (essential)
- **Related**: [GitOps & Deployments](../../cicd-delivery/gitops-deployments/) — GitOps for infrastructure delivery
- **Related**: [Security Tools](../../security-quality/security-tools/) — Security scanning for IaC
- **Related**: [CI/CD Pipelines](../../cicd-delivery/ci-cd-pipelines/) — IaC in pipelines
- **Related**: [Platforms Toolkit](../platforms/) — Crossplane as Kubernetes-native IaC

---

*"The best tool is the one your team will actually use consistently. Master one deeply, understand all broadly."*

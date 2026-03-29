---
title: "IaC Tools Toolkit"
sidebar:
  order: 1
  label: "IaC Tools"
---
> **Toolkit Track** | 10 Modules | ~8.5 hours total

## Overview

The IaC Tools Toolkit covers the major infrastructure as code tools in depth. From HashiCorp's Terraform to OpenTofu, from Pulumi's programming language approach to Ansible's configuration management, from CloudFormation to Bicep—this toolkit gives you hands-on experience with the tools that define modern infrastructure.

This toolkit applies concepts from [IaC Discipline](../../disciplines/delivery-automation/iac/).

## Prerequisites

Before starting this toolkit:
- [IaC Discipline](../../disciplines/delivery-automation/iac/) — IaC fundamentals, testing, security
- [IaC Fundamentals](../../disciplines/delivery-automation/iac/module-6.1-iac-fundamentals/) — Core concepts (minimum)
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

## Related Tracks

- **Before**: [IaC Discipline](../../disciplines/delivery-automation/iac/) — IaC fundamentals (essential)
- **Related**: [GitOps & Deployments](../gitops-deployments/) — GitOps for infrastructure delivery
- **Related**: [Security Tools](../security-tools/) — Security scanning for IaC
- **Related**: [CI/CD Pipelines](../ci-cd-pipelines/) — IaC in pipelines
- **Related**: [Platforms Toolkit](../platforms/) — Crossplane as Kubernetes-native IaC

---

*"The best tool is the one your team will actually use consistently. Master one deeply, understand all broadly."*

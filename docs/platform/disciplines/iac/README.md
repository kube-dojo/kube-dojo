# Infrastructure as Code Discipline

> **Discipline Track** | 6 Modules | ~4 hours total

## Overview

Infrastructure as Code (IaC) is the practice of managing and provisioning infrastructure through machine-readable configuration files rather than physical hardware configuration or interactive tools. This track covers IaC principles, testing, security, scale, drift management, and cost optimization.

This isn't about learning a specific tool—it's about understanding the patterns, practices, and principles that make infrastructure as code successful regardless of which tool you use.

## Prerequisites

Before starting this track:
- [Prerequisites: Infrastructure as Code](../../../prerequisites/modern-devops/module-1-infrastructure-as-code.md) — Basic IaC concepts
- [Systems Thinking](../../foundations/systems-thinking/README.md) — Understanding complex systems
- Basic cloud provider knowledge (any cloud)

## Modules

| # | Module | Complexity | Time |
|---|--------|------------|------|
| 6.1 | [IaC Fundamentals & Maturity Model](module-6.1-iac-fundamentals.md) | `[MEDIUM]` | 35-40 min |
| 6.2 | [IaC Testing Strategies](module-6.2-iac-testing.md) | `[COMPLEX]` | 40-45 min |
| 6.3 | [IaC Security](module-6.3-iac-security.md) | `[COMPLEX]` | 40-45 min |
| 6.4 | [IaC at Scale](module-6.4-iac-at-scale.md) | `[COMPLEX]` | 45-50 min |
| 6.5 | [Drift Detection & Remediation](module-6.5-drift-remediation.md) | `[MEDIUM]` | 35-40 min |
| 6.6 | [IaC Cost Management](module-6.6-iac-cost-management.md) | `[MEDIUM]` | 35-40 min |

## Learning Outcomes

After completing this track, you will be able to:

1. **Assess IaC maturity** — Evaluate where your organization is on the IaC journey
2. **Test infrastructure code** — Unit, integration, and compliance testing
3. **Secure IaC pipelines** — Policy as code, secrets management, supply chain security
4. **Scale IaC practices** — Modules, workspaces, state management at scale
5. **Detect and fix drift** — Identify when reality diverges from code
6. **Optimize costs** — FinOps practices in infrastructure code

## Key Concepts

### The IaC Maturity Model

```
┌─────────────────────────────────────────────────────────────────┐
│                     IAC MATURITY LEVELS                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Level 1: Manual     → Some scripts, mostly console clicks       │
│  Level 2: Scripted   → Basic automation, no state management     │
│  Level 3: IaC        → Version-controlled, state-managed         │
│  Level 4: Tested     → Automated testing, policy enforcement     │
│  Level 5: Self-serve → Platform APIs, guardrails, autonomy       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### IaC Testing Pyramid

```
                    ┌─────────────┐
                    │   E2E /     │  ← Real infrastructure
                    │ Integration │     (slowest, most confident)
                    ├─────────────┤
                    │   Policy    │  ← Compliance checks
                    │  Scanning   │     (OPA, Checkov, tfsec)
                    ├─────────────┤
                    │    Unit     │  ← Logic validation
                    │   Tests     │     (fastest, least coverage)
                    └─────────────┘
```

### Core Principles

1. **Everything in version control** — No console clicking in production
2. **Idempotency** — Running the same code twice produces the same result
3. **Immutable infrastructure** — Replace, don't modify
4. **State as source of truth** — Track what exists
5. **Modularity** — Compose infrastructure from reusable components

## Study Path

```
Module 6.1: IaC Fundamentals & Maturity Model
     │
     │  Foundation concepts
     │  Maturity assessment
     ▼
Module 6.2: IaC Testing Strategies
     │
     │  Testing pyramid
     │  Policy as code
     ▼
Module 6.3: IaC Security
     │
     │  Supply chain security
     │  Secrets management
     ▼
Module 6.4: IaC at Scale
     │
     │  Modules, workspaces
     │  State management
     ▼
Module 6.5: Drift Detection & Remediation
     │
     │  Drift sources
     │  Detection tools
     ▼
Module 6.6: IaC Cost Management
     │
     │  FinOps practices
     │  Cost estimation
     ▼
[Track Complete] → IaC Tools Toolkit
```

## Tools Covered (Conceptually)

This track covers **concepts** that apply across tools. For hands-on tool implementations, see the [IaC Tools Toolkit](../../toolkits/iac-tools/README.md).

| Category | Examples |
|----------|----------|
| **Provisioning** | Terraform, OpenTofu, Pulumi, CloudFormation |
| **Configuration** | Ansible, Chef, Puppet, Salt |
| **Testing** | Terratest, OPA, Checkov, tfsec, Infracost |
| **Drift Detection** | Driftctl, Terraform Cloud, Pulumi |
| **Cost Management** | Infracost, Kubecost, cloud-native tools |

## Related Tracks

- **Before**: [Systems Thinking](../../foundations/systems-thinking/README.md) — Complex systems fundamentals
- **Before**: [Security Principles](../../foundations/security-principles/README.md) — Security foundations for IaC Security module
- **Related**: [Platform Engineering](../platform-engineering/README.md) — IaC is core to self-service platforms
- **Related**: [DevSecOps](../devsecops/README.md) — Security in IaC pipelines
- **Related**: [GitOps](../gitops/README.md) — GitOps for infrastructure delivery
- **After**: [IaC Tools Toolkit](../../toolkits/iac-tools/README.md) — Terraform, OpenTofu, Pulumi hands-on

---

*"Infrastructure as Code is not about typing instead of clicking. It's about applying software engineering discipline to infrastructure."*

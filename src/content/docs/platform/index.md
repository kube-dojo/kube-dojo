---
title: "Platform Engineering"
sidebar:
  order: 1
  label: "Platform Engineering"
---
**Principles, practices, and disciplines for running production systems on Kubernetes.**

Kubernetes certifications teach you *how* to use Kubernetes. This track teaches you *how to run production systems* — the theory, disciplines, and leadership that separate operators from practitioners.

This is for people who:
- Have Kubernetes fundamentals (or certifications)
- Want to understand theory, not just tools
- Need to make technology decisions at work
- Want to implement best practices, not just pass exams

> Looking for tool-specific guides? See **[Cloud Native Tools](toolkits/)**.

## Do Not Start Here First If

- you are still learning basic Kubernetes objects and workflows
- you mostly need terminal, Linux, and first-cluster fundamentals
- you want an exam-first path rather than a theory-and-practice systems path

In those cases, start with [Prerequisites](../prerequisites/) or [Kubernetes Certifications](../k8s/) first.

## Safest Route Into Platform

```text
Prerequisites
   |
Kubernetes fundamentals
   |
Cloud and/or Linux depth
   |
Platform Foundations
   |
Platform Disciplines
```

For most learners, `Platform` should come after basic cluster competence, not before it.

---

## Structure

```
platform/
├── foundations/                         # Theory that doesn't change (32 modules)
│   ├── systems-thinking/               # Mental models for complex systems
│   ├── reliability-engineering/        # Failure theory, redundancy, risk
│   ├── observability-theory/           # What to measure and why
│   ├── security-principles/           # Zero trust, threat modeling
│   ├── distributed-systems/           # CAP, consensus, consistency
│   ├── advanced-networking/           # Network theory, protocols, design
│   └── engineering-leadership/        # Technical leadership, org design
│
└── disciplines/                        # Applied practices (81 modules)
    ├── core-platform/
    │   ├── sre/                        # Operations, reliability, on-call
    │   ├── platform-engineering/       # Developer experience, self-service
    │   └── platform-leadership/        # Strategy, adoption, evangelism
    │
    ├── delivery-automation/
    │   ├── release-engineering/        # Build, release, deploy lifecycle
    │   ├── gitops/                     # Deployment, reconciliation
    │   └── iac/                        # IaC patterns, testing, drift
    │
    ├── reliability-security/
    │   ├── networking/                 # Network architecture, policy
    │   ├── chaos-engineering/          # Failure injection, resilience
    │   └── devsecops/                  # Security integration, compliance
    │
    ├── data-ai/
    │   ├── data-engineering/           # Pipelines, streaming, storage
    │   ├── mlops/                      # ML lifecycle, model serving
    │   ├── aiops/                      # AI-driven operations
    │   └── ai-infrastructure/          # GPU scheduling, model hosting
    │
    └── business-value/
        └── finops/                     # Cloud cost optimization
```

---

## Reading Order

### Start with Foundations

Theory that applies everywhere. Read these first — they don't change.

| Track | Why Start Here |
|-------|---------------|
| [Systems Thinking](foundations/systems-thinking/) | Mental models for complex systems |
| [Reliability Engineering](foundations/reliability-engineering/) | Failure theory, redundancy, risk |
| [Distributed Systems](foundations/distributed-systems/) | CAP, consensus, consistency |
| [Observability Theory](foundations/observability-theory/) | What to measure and why |
| [Security Principles](foundations/security-principles/) | Zero trust, threat modeling |
| [Advanced Networking](foundations/advanced-networking/) | Network theory, protocols, design |
| [Engineering Leadership](foundations/engineering-leadership/) | Technical leadership, org design |

### Then Pick a Discipline

Applied practices — how to do the work.

#### Core Platform

| Discipline | Modules | Best For |
|------------|---------|----------|
| [SRE](disciplines/core-platform/sre/) | 7 | Operations, reliability, on-call |
| [Platform Engineering](disciplines/core-platform/platform-engineering/) | 6 | Developer experience, self-service |
| [Platform Leadership](disciplines/core-platform/leadership/) | 5 | Strategy, adoption, evangelism |

#### Delivery & Automation

| Discipline | Modules | Best For |
|------------|---------|----------|
| [Release Engineering](disciplines/delivery-automation/release-engineering/) | 5 | Build, release, deploy lifecycle |
| [GitOps](disciplines/delivery-automation/gitops/) | 6 | Deployment, reconciliation |
| [Infrastructure as Code](disciplines/delivery-automation/iac/) | 6 | IaC patterns, testing, drift management |

#### Reliability & Security

| Discipline | Modules | Best For |
|------------|---------|----------|
| [Networking](disciplines/reliability-security/networking/) | 5 | Network architecture, policy, design |
| [Chaos Engineering](disciplines/reliability-security/chaos-engineering/) | 5 | Failure injection, resilience |
| [DevSecOps](disciplines/reliability-security/devsecops/) | 7 | Security integration, compliance |

#### Data & AI

| Discipline | Modules | Best For |
|------------|---------|----------|
| [Data Engineering](disciplines/data-ai/data-engineering/) | 6 | Pipelines, streaming, storage |
| [MLOps](disciplines/data-ai/mlops/) | 6 | ML lifecycle, model serving |
| [AIOps](disciplines/data-ai/aiops/) | 6 | AI-driven operations, automation |
| [AI Infrastructure](disciplines/data-ai/ai-infrastructure/) | 6 | GPU scheduling, model hosting |

#### Business Value

| Discipline | Modules | Best For |
|------------|---------|----------|
| [FinOps](disciplines/business-value/finops/) | 6 | Cloud cost optimization |

## Common Routes Through This Track

- `SRE / reliability`: Foundations -> Reliability Engineering -> Observability Theory -> SRE
- `Platform builder`: Foundations -> Systems Thinking -> Platform Engineering -> Platform Leadership
- `Delivery automation`: Foundations -> Distributed Systems -> Release Engineering -> GitOps -> IaC
- `Security-minded platform`: Foundations -> Security Principles -> DevSecOps -> Networking
- `AI platform`: Foundations -> Distributed Systems -> Data Engineering / MLOps / AI Infrastructure

---

## Module Format

Every module includes:

- **Why This Matters** — Real-world motivation
- **Theory** — Principles and mental models
- **Current Landscape** — Tools that implement this
- **Hands-On** — Practical implementation
- **Best Practices** — What good looks like
- **Common Mistakes** — Anti-patterns to avoid
- **Further Reading** — Books, talks, papers

---

## Status

| Section | Modules | Description |
|---------|---------|-------------|
| Foundations | 32 | 7 sections: Systems Thinking, Reliability Engineering, Observability Theory, Security Principles, Distributed Systems, Advanced Networking, Engineering Leadership |
| Disciplines | 81 | 14 disciplines across Core Platform, Delivery & Automation, Reliability & Security, Data & AI, and Business Value |
| **Total** | **113** | |

> Tool-specific implementation guides (96 modules) are in **[Cloud Native Tools](toolkits/)**.

---

## Prerequisites

Before starting this track, you should have:
- Kubernetes basics (or completed [Prerequisites](../prerequisites/))
- Some production experience (helpful but not required)
- Curiosity about "why" not just "how"

## Where This Track Leads

- into deeper [Cloud](../cloud/) architecture work
- into serious [On-Premises](../on-premises/) operations and private-platform design
- into [AI/ML Engineering](../ai-ml-engineering/) operations paths through the Data & AI disciplines

---

*"Tools change. Principles don't."*

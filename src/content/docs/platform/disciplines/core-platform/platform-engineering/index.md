---
title: "Platform Engineering Discipline"
sidebar:
  order: 1
  label: "Platform Engineering"
---
> Building internal products that make developers productive.

## Overview

Platform Engineering is the discipline of designing and building toolchains and workflows that enable self-service capabilities for software engineering organizations. Unlike traditional infrastructure teams that respond to tickets, platform teams build products that enable developers to do their own infrastructure work safely and efficiently.

## Learning Objectives

After completing this track, you will be able to:

- Explain what platform engineering is and how it differs from DevOps
- Apply the platform-as-a-product mindset to internal tooling
- Design for developer experience using cognitive load theory
- Architect Internal Developer Platforms (IDPs)
- Create effective golden paths that developers actually want to use
- Implement self-service infrastructure with appropriate guardrails
- Assess platform maturity and build improvement roadmaps

## Prerequisites

Before starting this track, you should:

- Understand Kubernetes fundamentals (deployments, services, namespaces)
- Be familiar with CI/CD concepts and tools
- Have experience with infrastructure-as-code (or complete [IaC Discipline](../iac/))
- Complete the **Systems Thinking** foundation track (recommended)

## Modules

| # | Module | Complexity | Time | Description |
|---|--------|------------|------|-------------|
| 2.1 | [What is Platform Engineering?](module-2.1-what-is-platform-engineering/) | MEDIUM | 35-45 min | Origins, platform-as-a-product, Team Topologies |
| 2.2 | [Developer Experience](module-2.2-developer-experience/) | MEDIUM | 40-50 min | SPACE framework, cognitive load, flow state |
| 2.3 | [Internal Developer Platforms](module-2.3-internal-developer-platforms/) | COMPLEX | 50-60 min | Five pillars, reference architectures, build vs buy |
| 2.4 | [Golden Paths](module-2.4-golden-paths/) | MEDIUM | 40-50 min | Design, mandates vs paths, maintenance |
| 2.5 | [Self-Service Infrastructure](module-2.5-self-service-infrastructure/) | COMPLEX | 50-60 min | Abstractions, guardrails, lifecycle management |
| 2.6 | [Platform Maturity](module-2.6-platform-maturity/) | MEDIUM | 45-55 min | Assessment, dimensions, roadmaps |

**Total Time**: ~4.5-5.5 hours

## Learning Path

```
Module 2.1: What is Platform Engineering?
    │
    ├── Understand the origin and evolution
    ├── Learn platform-as-a-product mindset
    └── Apply Team Topologies patterns
          │
          ▼
Module 2.2: Developer Experience
    │
    ├── Measure with SPACE framework
    ├── Reduce cognitive load
    └── Enable flow state
          │
          ▼
Module 2.3: Internal Developer Platforms
    │
    ├── Understand the five pillars
    ├── Choose reference architecture
    └── Make build vs buy decisions
          │
          ▼
Module 2.4: Golden Paths
    │
    ├── Design effective paths
    ├── Balance guidance with autonomy
    └── Maintain over time
          │
          ▼
Module 2.5: Self-Service Infrastructure
    │
    ├── Create useful abstractions
    ├── Implement guardrails
    └── Manage full lifecycle
          │
          ▼
Module 2.6: Platform Maturity
    │
    ├── Assess current state
    ├── Identify gaps
    └── Build improvement roadmap
```

## Key Concepts

### Platform Engineering vs DevOps

| Aspect | DevOps | Platform Engineering |
|--------|--------|---------------------|
| Focus | Process and culture | Products and tooling |
| Model | Embedded in teams | Separate team serving teams |
| Success metric | Deployment frequency | Developer productivity |
| Interaction | Collaboration | Self-service |

### The Platform-as-a-Product Mindset

Platform teams treat developers as customers:
- Research needs before building
- Measure adoption and satisfaction
- Iterate based on feedback
- Compete with alternatives (shadow IT)

### The Five IDP Pillars

```
┌─────────────────────────────────────────────────────────────────┐
│                   INTERNAL DEVELOPER PLATFORM                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │Developer │  │ Infra    │  │  App     │  │ Security │       │
│  │ Portal   │  │Orchestr. │  │ Delivery │  │& Govern. │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
│                                                                  │
│                       ┌──────────┐                              │
│                       │Observa-  │                              │
│                       │bility    │                              │
│                       └──────────┘                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Cognitive Load Types

| Type | Description | Platform Strategy |
|------|-------------|-------------------|
| **Intrinsic** | Complexity inherent to the task | Can't eliminate, can support |
| **Extraneous** | Unnecessary complexity | **Eliminate through platform** |
| **Germane** | Learning that builds expertise | Preserve and enable |

## Related Tracks

**Foundations** (Start here if new to these concepts):
- [Systems Thinking](../../foundations/systems-thinking/) - Feedback loops and emergent behavior
- [Reliability Engineering](../../foundations/reliability-engineering/) - Change management principles

**Disciplines** (Apply platform engineering in context):
- [SRE Discipline](../sre/) - Reliability practices for platforms
- [GitOps Discipline](../gitops/) - GitOps for platform delivery
- [DevSecOps Discipline](../devsecops/) - Security in platform workflows
- [IaC Discipline](../iac/) - Infrastructure as Code patterns and practices

**Toolkits** (Deep dive into specific tools):
- [GitOps Tools](../../toolkits/cicd-delivery/gitops-deployments/) - ArgoCD, Flux implementation
- [Platforms Toolkit](../../toolkits/infrastructure-networking/platforms/) - Backstage, Crossplane hands-on
- [IaC Tools](../../toolkits/infrastructure-networking/iac-tools/) - Terraform, OpenTofu, Pulumi, Ansible

## Tools You'll Encounter

| Tool | Purpose |
|------|---------|
| **Backstage** | Developer portal, service catalog |
| **Crossplane** | Infrastructure orchestration |
| **ArgoCD/Flux** | GitOps delivery |
| **OPA/Gatekeeper** | Policy as code |
| **Kustomize/Helm** | Configuration management |
| **OpenTelemetry** | Observability |

## Progress Checklist

- [ ] Module 2.1: What is Platform Engineering? - Foundations
- [ ] Module 2.2: Developer Experience - Measurement and improvement
- [ ] Module 2.3: Internal Developer Platforms - Architecture
- [ ] Module 2.4: Golden Paths - Template design
- [ ] Module 2.5: Self-Service Infrastructure - Provisioning patterns
- [ ] Module 2.6: Platform Maturity - Assessment and roadmaps

## Quick Reference

### Platform Team Anti-Patterns

| Anti-Pattern | Description | Fix |
|--------------|-------------|-----|
| Build it and they will come | No adoption focus | Treat platform as product |
| Golden handcuffs | Mandates, not paths | Make the right thing easy |
| Ticket queue | Still ticket-based | Build self-service |
| Perfect platform | Never ship | MVP + iterate |

### Maturity Levels

| Level | Name | Characteristics |
|-------|------|-----------------|
| 1 | Provisional | Ad-hoc, tribal knowledge |
| 2 | Operational | Basic automation, some self-service |
| 3 | Scalable | Self-service works, metrics tracked |
| 4 | Managed | Business impact measured, proactive |
| 5 | Optimizing | Continuous improvement, industry leader |

### Success Metrics

```yaml
Adoption:
  - Golden path usage rate
  - Self-service success rate
  - Time to first deploy

Satisfaction:
  - Developer NPS
  - Support ticket volume
  - Cognitive load surveys

Impact:
  - Deployment frequency
  - Lead time for changes
  - Platform ROI
```

## Further Reading

### Books
- *Team Topologies* - Matthew Skelton & Manuel Pais
- *The Phoenix Project* - Gene Kim, Kevin Behr, George Spafford
- *Accelerate* - Nicole Forsgren, Jez Humble, Gene Kim

### Articles
- [What is Platform Engineering?](https://platformengineering.org/blog/what-is-platform-engineering)
- [Spotify's Golden Paths](https://engineering.atspotify.com/2020/08/how-we-use-golden-paths-to-solve-fragmentation-in-our-software-ecosystem/)
- [CNCF Platform Maturity Model](https://tag-app-delivery.cncf.io/whitepapers/platform-eng-maturity-model/)

### Conferences
- [PlatformCon](https://platformcon.com/) - Annual platform engineering conference
- [KubeCon](https://www.cncf.io/kubecon-cloudnativecon-events/) - Platform talks track

---

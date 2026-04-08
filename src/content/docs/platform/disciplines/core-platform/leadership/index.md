---
title: "Platform Leadership"
sidebar:
  order: 0
  label: "Platform Leadership"
---
> **Discipline Track** | 5 Modules | ~5 hours total

Leading platform teams is fundamentally different from leading product teams. You are building infrastructure that other engineers depend on, marketing to an audience that can fork your work, and measuring success by what your users never have to think about.

---

## Why Platform Leadership?

Platform teams fail more often from organizational problems than technical ones. The technology is the easy part. The hard part is:
- **Building the right team** — Platform engineers need a rare mix of empathy and deep technical skill
- **Earning adoption** — You cannot mandate your way to a successful platform
- **Proving value** — Platform work is invisible when it works and blamed when it breaks
- **Scaling without bureaucracy** — Growing from 1 team to 10 without becoming the bottleneck you set out to eliminate

This discipline gives you frameworks, patterns, and hard-won lessons for leading platform organizations that actually deliver value.

---

## Modules

| # | Module | Time | Description |
|---|--------|------|-------------|
| 1.1 | [Building Platform Teams](module-1.1-platform-team-building/) | 55-65 min | Team topologies, hiring, skill mix, Conway's Law, org design |
| 1.2 | [Developer Experience Strategy](module-1.2-developer-experience/) | 55-65 min | DORA/SPACE metrics, golden paths, self-service, cognitive load |
| 1.3 | [Platform as Product](module-1.3-platform-as-product/) | 55-65 min | Product management, user research, roadmapping, success metrics |
| 1.4 | [Adoption & Migration Strategy](module-1.4-adoption-migration/) | 55-65 min | Voluntary vs mandatory, migration patterns, resistance management |
| 1.5 | [Scaling Platform Organizations](module-1.5-scaling-platform-org/) | 55-65 min | Federated governance, SLOs, cost models, build vs buy |

---

## Learning Path

```
START HERE
    │
    ▼
┌─────────────────────────────────────┐
│  Module 1.1                         │
│  Building Platform Teams            │
│  └── Team topologies                │
│  └── Hiring platform engineers      │
│  └── Conway's Law in practice       │
│  └── Embedding vs centralized       │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│  Module 1.2                         │
│  Developer Experience Strategy      │
│  └── Measuring DX (DORA, SPACE)     │
│  └── Golden paths vs guardrails     │
│  └── Self-service design            │
│  └── Cognitive load reduction       │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│  Module 1.3                         │
│  Platform as Product                │
│  └── Internal product management    │
│  └── User research methods          │
│  └── Roadmapping & prioritization   │
│  └── Adoption metrics               │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│  Module 1.4                         │
│  Adoption & Migration Strategy      │
│  └── Voluntary vs mandatory         │
│  └── Migration patterns             │
│  └── Incentive design               │
│  └── Organizational resistance      │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│  Module 1.5                         │
│  Scaling Platform Organizations     │
│  └── From 1 to 10 teams            │
│  └── Federated governance           │
│  └── Cost allocation models         │
│  └── Build vs buy decisions         │
└──────────────────┬──────────────────┘
                   │
                   ▼
        PLATFORM LEADERSHIP
            COMPLETE
                   │
    ┌──────────────┼──────────────┐
    │              │              │
    ▼              ▼              ▼
Platform       SRE            GitOps
Engineering  Discipline     Discipline
Discipline
```

---

## Key Concepts You'll Learn

| Concept | Module | What It Means |
|---------|--------|---------------|
| Team Topologies | 1.1 | Framework for organizing platform teams |
| Conway's Law | 1.1 | Org structure shapes system architecture |
| DORA Metrics | 1.2 | Four key metrics for software delivery performance |
| SPACE Framework | 1.2 | Multi-dimensional developer productivity model |
| Golden Paths | 1.2 | Opinionated, well-supported defaults |
| Platform as Product | 1.3 | Treating internal platforms like products with users |
| RICE Scoring | 1.3 | Reach, Impact, Confidence, Effort prioritization |
| Strangler Fig | 1.4 | Gradual migration pattern replacing legacy piece by piece |
| Chargeback | 1.5 | Allocating platform costs to consuming teams |
| Federated Governance | 1.5 | Balancing central standards with team autonomy |

---

## Prerequisites

- **Required**: [Engineering Leadership Track](../../../foundations/engineering-leadership/) — Incident command, postmortems, ADRs, stakeholder communication
- **Required**: [Systems Thinking Track](../../../foundations/systems-thinking/) — Understanding organizational systems
- **Recommended**: [SRE Discipline](../sre/) — SLOs, error budgets, operational maturity
- **Recommended**: [Platform Engineering Discipline](../platform-engineering/) — Technical platform concepts
- **Helpful**: Experience working on or with infrastructure/platform teams
- **Helpful**: Some management or tech lead experience

---

## Where This Leads

After completing Platform Leadership, you're ready for:

| Track | Why |
|-------|-----|
| [Platform Engineering Discipline](../platform-engineering/) | Technical depth for platforms you lead |
| [SRE Discipline](../sre/) | Reliability practices your platform must embody |
| [FinOps Discipline](../../business-value/finops/) | Cost management for platforms at scale |
| [GitOps Discipline](../../delivery-automation/gitops/) | Delivery patterns your platform enables |
| [IaC Discipline](../../delivery-automation/iac/) | Infrastructure automation your platform wraps |

---

## Key Resources

**Books** (referenced throughout):
- **"Team Topologies"** — Matthew Skelton & Manuel Pais (the foundational text)
- **"Platform Engineering"** — Camille Fournier (O'Reilly, 2024)
- **"Empowered"** — Marty Cagan (product management for tech teams)
- **"An Elegant Puzzle"** — Will Larson (systems of engineering management)

**Reports**:
- **DORA State of DevOps Report** — Annual industry benchmarks
- **Puppet State of Platform Engineering** — Platform maturity data

**Communities**:
- **Platform Engineering community** — platformengineering.org
- **Internal Developer Platform** — internaldeveloperplatform.org
- **PlatformCon** — Annual conference

---

## The Platform Leadership Mindset

| Question to Ask | Why It Matters |
|-----------------|----------------|
| "Who are our users?" | Platform teams without user empathy build shelfware |
| "What's our adoption rate?" | Measures real value, not assumed value |
| "What's the developer's inner loop?" | Understand what you're optimizing |
| "Can they self-serve this?" | If not, you're a ticket queue, not a platform |
| "What would we stop doing?" | Prioritization means saying no |
| "Are we building or buying?" | Not everything needs to be homegrown |

---

## Discipline Complete

After these 5 modules, you can:

- **Build** effective platform teams with the right structure and skills
- **Measure** developer experience with data, not assumptions
- **Run** your platform like a product with real user research
- **Drive** adoption without mandates through incentive design
- **Scale** from a small team to a platform organization

Platform leadership is not about controlling infrastructure. It is about enabling the people who build on it.

---

*"The best platform is the one developers choose to use."* — Gregor Hohpe

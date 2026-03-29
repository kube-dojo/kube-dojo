---
title: "Site Reliability Engineering (SRE)"
sidebar:
  order: 1
  label: "SRE"
---
> **Discipline Track** | 7 Modules | ~4 hours total

The practice of applying software engineering to operations. SRE provides concrete methods for measuring, maintaining, and improving the reliability of production systems.

---

## Why SRE?

Traditional operations faces a fundamental tension: development wants to ship fast, operations wants stability. These goals seem opposed.

SRE resolves this tension through:
- **Measurable reliability** — SLOs replace vague "make it reliable" with concrete targets
- **Error budgets** — Calculated risk-taking, not reckless shipping or excessive caution
- **Engineering mindset** — Automate toil, don't just do it
- **Learning culture** — Blameless postmortems turn failures into improvements

SRE isn't just operations with a fancy name. It's a fundamentally different approach to running production systems.

---

## Modules

| # | Module | Time | Description |
|---|--------|------|-------------|
| 1.1 | [What is SRE?](module-1.1-what-is-sre/) | 30-35 min | Origins, mindset, team structures, SRE vs DevOps |
| 1.2 | [Service Level Objectives](module-1.2-slos/) | 35-40 min | SLI, SLO, SLA hierarchy, choosing and measuring |
| 1.3 | [Error Budgets](module-1.3-error-budgets/) | 30-35 min | Budget calculation, policies, balancing velocity |
| 1.4 | [Toil and Automation](module-1.4-toil-automation/) | 30-35 min | Identifying toil, 50% rule, automation strategies |
| 1.5 | [Incident Management](module-1.5-incident-management/) | 35-40 min | Response roles, severity, on-call, runbooks |
| 1.6 | [Postmortems and Learning](module-1.6-postmortems/) | 30-35 min | Blameless culture, postmortem structure, action items |
| 1.7 | [Capacity Planning](module-1.7-capacity-planning/) | 35-40 min | Forecasting, provisioning, load testing, cost |

---

## Learning Path

```
START HERE
    │
    ▼
┌─────────────────────────────────────┐
│  Module 1.1                         │
│  What is SRE?                       │
│  └── SRE origins and mindset        │
│  └── SRE vs DevOps vs Platform      │
│  └── Team structures                │
│  └── The 50% rule                   │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│  Module 1.2                         │
│  Service Level Objectives           │
│  └── SLI, SLO, SLA hierarchy        │
│  └── Choosing good SLIs             │
│  └── Setting realistic SLOs         │
│  └── SLO-based alerting             │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│  Module 1.3                         │
│  Error Budgets                      │
│  └── Budget calculation             │
│  └── Error budget policies          │
│  └── Balancing reliability/velocity │
│  └── When to spend vs save          │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│  Module 1.4                         │
│  Toil and Automation                │
│  └── Defining and measuring toil    │
│  └── The 50% rule in practice       │
│  └── Automation hierarchy           │
│  └── ROI-based prioritization       │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│  Module 1.5                         │
│  Incident Management                │
│  └── Response roles (IC, Comms)     │
│  └── Severity levels                │
│  └── On-call best practices         │
│  └── Runbooks and playbooks         │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│  Module 1.6                         │
│  Postmortems and Learning           │
│  └── Blameless culture              │
│  └── The "second story"             │
│  └── Effective action items         │
│  └── Sharing learnings              │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│  Module 1.7                         │
│  Capacity Planning                  │
│  └── Demand forecasting             │
│  └── Provisioning strategies        │
│  └── Load testing                   │
│  └── Cost optimization              │
└──────────────────┬──────────────────┘
                   │
                   ▼
            SRE COMPLETE
                   │
    ┌──────────────┼──────────────┐
    │              │              │
    ▼              ▼              ▼
Platform      GitOps       Observability
Engineering   Discipline      Toolkit
```

---

## Key Concepts You'll Learn

| Concept | Module | What It Means |
|---------|--------|---------------|
| SLI | 1.2 | Service Level Indicator — what you measure |
| SLO | 1.2 | Service Level Objective — your target |
| SLA | 1.2 | Service Level Agreement — external promise |
| Error Budget | 1.3 | Allowed unreliability (1 - SLO) |
| Toil | 1.4 | Repetitive, automatable work |
| 50% Rule | 1.1, 1.4 | Cap toil at 50% to ensure engineering time |
| Incident Commander | 1.5 | Person coordinating incident response |
| Blameless Postmortem | 1.6 | Learning from failure without blame |
| Burn Rate | 1.2, 1.3 | How fast error budget is being consumed |
| Headroom | 1.7 | Buffer capacity for traffic spikes |

---

## Prerequisites

- **Required**: [Reliability Engineering Track](../../../foundations/reliability-engineering/) — Failure modes and resilience
- **Required**: [Systems Thinking Track](../../../foundations/systems-thinking/) — Understanding system dynamics
- **Recommended**: [Observability Theory Track](../../../foundations/observability-theory/) — Metrics and monitoring
- **Helpful**: Experience operating production systems
- **Helpful**: Some Kubernetes experience

---

## Where This Leads

After completing the SRE Discipline, you're ready for:

| Track | Why |
|-------|-----|
| [Platform Engineering Discipline](../platform-engineering/) | Build platforms using SRE principles |
| [GitOps Discipline](../../delivery-automation/gitops/) | Declarative infrastructure operations |
| [IaC Discipline](../../delivery-automation/iac/) | Infrastructure as Code for reliable provisioning |
| [Observability Toolkit](../../../toolkits/observability-intelligence/observability/) | Implement Prometheus, Grafana, OpenTelemetry |
| [IaC Tools Toolkit](../../../toolkits/infrastructure-networking/iac-tools/) | Terraform, OpenTofu, Pulumi for automation |
| [CKA Certification](../../../../k8s/cka/) | Apply SRE to Kubernetes administration |

---

## Key Resources

**Books** (referenced throughout):
- **"Site Reliability Engineering"** — Google (free online, the original SRE book)
- **"The Site Reliability Workbook"** — Google (practical companion)
- **"Implementing Service Level Objectives"** — Alex Hidalgo

**Articles**:
- **"What is SRE?"** — Google Cloud
- **"SRE vs DevOps"** — Atlassian

**Tools** mentioned:
- **Prometheus/Grafana**: SLO monitoring
- **PagerDuty/OpsGenie**: Incident management
- **k6/Locust**: Load testing
- **Kubernetes HPA**: Auto-scaling

---

## The SRE Mindset

| Question to Ask | Why It Matters |
|-----------------|----------------|
| "What's our SLO?" | Can't improve what you don't measure |
| "How much error budget do we have?" | Know when to ship vs when to stabilize |
| "Is this toil?" | Automate if yes, protect engineering time |
| "What would prevent this incident?" | Systems fix, not human vigilance |
| "Who's the IC?" | Clear roles in chaos |
| "Can we handle 2x traffic?" | Plan before you need it |

---

## Discipline Complete

After these 7 modules, you can:

- **Define and measure** reliability with SLOs
- **Balance** reliability and velocity with error budgets
- **Identify and eliminate** toil systematically
- **Respond** to incidents with clear roles and processes
- **Learn** from failures through blameless postmortems
- **Plan** for future capacity and growth

You're now equipped to practice SRE, not just read about it.

---

*"Hope is not a strategy."* — Traditional SRE saying

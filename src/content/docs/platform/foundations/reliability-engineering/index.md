---
title: "Reliability Engineering"
sidebar:
  order: 0
  label: "Reliability Engineering"
---
> **Foundation Track** | 5 Modules | ~2.5 hours total

The engineering discipline of building systems that work when users need them. Theory and principles that apply regardless of your tech stack.

---

## Why Reliability Engineering?

Users don't care about your architecture. They care about one thing: **does it work?**

Reliability engineering teaches you to:
- **Define** what "reliable" means for your context
- **Measure** reliability objectively
- **Design** for failure before it happens
- **Improve** continuously through data-driven decisions

This isn't about hoping things don't break. It's about engineering systems that survive when they do.

---

## Modules

| # | Module | Time | Description |
|---|--------|------|-------------|
| 2.1 | [What is Reliability?](module-2.1-what-is-reliability/) | 25-30 min | Definitions, nines, MTBF/MTTR, error budgets |
| 2.2 | [Failure Modes and Effects](module-2.2-failure-modes-and-effects/) | 30-35 min | FMEA, graceful degradation, blast radius |
| 2.3 | [Redundancy and Fault Tolerance](module-2.3-redundancy-and-fault-tolerance/) | 30-35 min | HA vs FT, active-active, redundancy patterns |
| 2.4 | [Measuring and Improving Reliability](module-2.4-measuring-and-improving-reliability/) | 35-40 min | Metrics, postmortems, and continuous improvement |
| 2.5 | [SLIs, SLOs, and Error Budgets — The Theory](module-2.5-slos-slis-error-budgets/) | 20-30 min | Deep dive into the SRE mental model for reliability targets |

---

## Learning Path

```
START HERE
    │
    ▼
┌─────────────────────────────────────┐
│  Module 2.1                         │
│  What is Reliability?               │
│  └── Definitions and metrics        │
│  └── The nines                      │
│  └── MTBF, MTTR, error budgets      │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│  Module 2.2                         │
│  Failure Modes and Effects          │
│  └── Failure taxonomy               │
│  └── FMEA technique                 │
│  └── Graceful degradation           │
│  └── Blast radius                   │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│  Module 2.3                         │
│  Redundancy and Fault Tolerance     │
│  └── HA vs FT                       │
│  └── Active-passive vs active-active│
│  └── Redundancy patterns            │
│  └── The costs of redundancy        │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│  Module 2.4                         │
│  Measuring and Improving            │
│  └── Reliability metrics            │
│  └── Postmortems                    │
│  └── Continuous improvement         │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│  Module 2.5                         │
│  SLIs, SLOs, and Error Budgets      │
│  └── SLIs vs SLOs vs SLAs           │
│  └── Error budgets in practice      │
│  └── The SRE mental model           │
└──────────────────┬──────────────────┘
                   │
                   ▼
              COMPLETE
                   │
    ┌──────────────┼──────────────┐
    │              │              │
    ▼              ▼              ▼
Observability   Security        SRE
   Theory      Principles    Discipline
```

---

## Key Concepts You'll Learn

| Concept | Module | What It Means |
|---------|--------|---------------|
| The Nines | 2.1 | 99.9% vs 99.99% = 10x difference in allowed downtime |
| MTBF/MTTR | 2.1 | Mean time between failures / to recovery |
| Error Budget | 2.1, 2.5 | Acceptable unreliability as a resource to spend |
| FMEA | 2.2 | Systematic technique for predicting failures |
| Graceful Degradation | 2.2 | Partial functionality better than total failure |
| Blast Radius | 2.2 | Scope of impact when something fails |
| Bulkhead Pattern | 2.2, 2.3 | Isolation to prevent cascading failures |
| High Availability | 2.3 | System stays operational with minimal downtime |
| Fault Tolerance | 2.3 | System continues without any interruption |
| SLI/SLO/SLA | 2.5 | Indicator/Objective/Agreement framework |

---

## Prerequisites

- **Recommended**: [Systems Thinking Track](../systems-thinking/)
- Helpful: Some experience operating production systems
- Helpful: Understanding of distributed systems basics

---

## Where This Leads

After completing Reliability Engineering, you're ready for:

| Track | Why |
|-------|-----|
| [Observability Theory](../observability-theory/) | Can't improve reliability without seeing what's happening |
| [SRE Discipline](../../disciplines/core-platform/sre/) | Putting reliability engineering into operational practice |
| [Security Principles](../security-principles/) | Security and reliability share patterns |
| [Distributed Systems](../distributed-systems/) | Deep dive into CAP, consensus, and distributed patterns |

---

## Key Resources

Books referenced throughout this track:

- **"Site Reliability Engineering"** — Google
- **"Release It! Second Edition"** — Michael Nygard
- **"Designing Data-Intensive Applications"** — Martin Kleppmann
- **"Implementing Service Level Objectives"** — Alex Hidalgo

Papers:

- **"How Complex Systems Fail"** — Richard Cook (free online)

---

*"Reliability is not a feature you add. It's how you build from the start."*
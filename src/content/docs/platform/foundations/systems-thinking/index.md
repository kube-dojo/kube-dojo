---
title: "Systems Thinking"
sidebar:
  order: 0
  label: "Systems Thinking"
---
> **Foundation Track** | 4 Modules | ~2 hours total

Mental models for understanding complex systems. The theoretical foundation for SRE, Platform Engineering, and all operational disciplines.

---

## Why Systems Thinking?

You can't fix what you don't understand. And you can't understand a distributed system by looking at each component in isolation.

Systems thinking teaches you to see:
- **Wholes, not parts** — Behavior emerges from interactions
- **Patterns, not events** — Look deeper than the current incident
- **Feedback loops** — What drives growth and stability
- **Complexity** — Why systems fail in surprising ways

This foundation applies to everything that follows in the Platform Engineering track.

---

## Modules

| # | Module | Time | Description |
|---|--------|------|-------------|
| 1.1 | [What is Systems Thinking?](module-1.1-what-is-systems-thinking/) | 25-30 min | Systems vs components, emergence, the iceberg model |
| 1.2 | [Feedback Loops](module-1.2-feedback-loops/) | 30-35 min | Reinforcing and balancing loops, delays, oscillation |
| 1.3 | [Mental Models for Operations](module-1.3-mental-models-for-operations/) | 30-35 min | Leverage points, stock-and-flow, causal loop diagrams |
| 1.4 | [Complexity and Emergent Behavior](module-1.4-complexity-and-emergent-behavior/) | 35-40 min | Cynefin framework, how complex systems fail, resilience |

---

## Learning Path

```
START HERE
    │
    ▼
┌─────────────────────────────────────┐
│  Module 1.1                         │
│  What is Systems Thinking?          │
│  └── Systems vs components          │
│  └── Emergence                      │
│  └── The iceberg model              │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│  Module 1.2                         │
│  Feedback Loops                     │
│  └── Reinforcing loops              │
│  └── Balancing loops                │
│  └── Delays and oscillation         │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│  Module 1.3                         │
│  Mental Models for Operations       │
│  └── Leverage points                │
│  └── Stock-and-flow diagrams        │
│  └── Causal loop diagrams           │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│  Module 1.4                         │
│  Complexity and Emergent Behavior   │
│  └── Cynefin framework              │
│  └── How complex systems fail       │
│  └── Designing for resilience       │
└──────────────────┬──────────────────┘
                   │
                   ▼
              COMPLETE
                   │
    ┌──────────────┼──────────────┐
    │              │              │
    ▼              ▼              ▼
Reliability    Observability    SRE
Engineering       Theory      Discipline
```

---

## Key Concepts You'll Learn

| Concept | Module | What It Means |
|---------|--------|---------------|
| Emergence | 1.1 | System behavior that no individual component exhibits |
| Iceberg Model | 1.1 | Events → Patterns → Structures → Mental Models |
| Reinforcing Loop | 1.2 | Feedback that amplifies change (exponential growth/collapse) |
| Balancing Loop | 1.2 | Feedback that opposes change (stability/oscillation) |
| Leverage Points | 1.3 | Places where small changes create big effects |
| Stock-and-Flow | 1.3 | Accumulations and rates of change |
| Cynefin | 1.4 | Framework for categorizing situations (clear, complicated, complex, chaotic) |
| Resilience | 1.4 | Ability to adapt to unexpected failures |

---

## Prerequisites

- None — This is the entry point to the Platform Engineering track
- Helpful: Some experience operating production systems

---

## Where This Leads

After completing Systems Thinking, you're ready for:

| Track | Why |
|-------|-----|
| [Reliability Engineering](../reliability-engineering/) | Applies systems thinking to failure modes and redundancy |
| [Observability Theory](../observability-theory/) | Understanding what to measure and why |
| [SRE Discipline](../../disciplines/core-platform/sre/) | Putting systems thinking into operational practice |
| [Distributed Systems](../distributed-systems/) | Deep dive into CAP, consensus, and distributed patterns |

---

## Key Resources

Books referenced throughout this track:

- **"Thinking in Systems: A Primer"** — Donella Meadows
- **"How Complex Systems Fail"** — Richard Cook (free online)
- **"Drift into Failure"** — Sidney Dekker
- **"The Fifth Discipline"** — Peter Senge

---

*"You can't understand a system by looking at its parts. You understand a system by seeing how the parts interact."*

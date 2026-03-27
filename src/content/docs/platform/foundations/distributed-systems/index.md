---
title: "Distributed Systems"
sidebar:
  order: 1
  label: "Distributed Systems"
---
> **Foundation Track** | 3 Modules | ~1.5 hours total

The fundamentals of building systems that run across multiple machines. Understanding why distributed systems are hard, and the patterns that make them work.

---

## Why Distributed Systems?

Every modern system is distributed. The moment you have a web server and a database, you're distributed. The moment you deploy to multiple availability zones, you face distributed systems challenges.

Distributed systems don't behave like single machines. Things that were easy become hard:

- **Latency**: Network calls are millions of times slower than local calls
- **Partial failure**: Components fail independently, often invisibly
- **No global clock**: You can't reliably order events across machines
- **Uncertainty**: You can't always tell if a remote call succeeded

Understanding these challenges helps you design systems that work despite them.

---

## Modules

| # | Module | Time | Description |
|---|--------|------|-------------|
| 5.1 | [What Makes Systems Distributed](module-5.1-what-makes-systems-distributed/) | 25-30 min | Fundamental challenges, CAP theorem, Kubernetes as distributed system |
| 5.2 | [Consensus and Coordination](module-5.2-consensus-and-coordination/) | 35-40 min | Paxos, Raft, leader election, distributed locks, etcd |
| 5.3 | [Eventual Consistency](module-5.3-eventual-consistency/) | 30-35 min | Consistency models, replication, conflict resolution, CRDTs |

---

## Learning Path

```
START HERE
    │
    ▼
┌─────────────────────────────────────┐
│  Module 5.1                         │
│  What Makes Systems Distributed     │
│  └── The fundamental challenges     │
│  └── CAP theorem                    │
│  └── Kubernetes as example          │
│  └── Why it's hard                  │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│  Module 5.2                         │
│  Consensus and Coordination         │
│  └── Paxos and Raft                 │
│  └── Leader election                │
│  └── Distributed locks              │
│  └── etcd and ZooKeeper             │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│  Module 5.3                         │
│  Eventual Consistency               │
│  └── Consistency spectrum           │
│  └── Replication strategies         │
│  └── Conflict resolution            │
│  └── CRDTs                          │
└──────────────────┬──────────────────┘
                   │
                   ▼
           FOUNDATIONS COMPLETE
                   │
    ┌──────────────┼──────────────┐
    │              │              │
    ▼              ▼              ▼
   SRE         Platform      GitOps
Discipline    Engineering   Discipline
```

---

## Key Concepts You'll Learn

| Concept | Module | What It Means |
|---------|--------|---------------|
| Latency | 5.1 | Network calls are slow (physics) |
| Partial Failure | 5.1 | Parts fail while others continue |
| CAP Theorem | 5.1 | Choose consistency or availability during partition |
| Consensus | 5.2 | Getting nodes to agree on a value |
| Raft | 5.2 | Understandable consensus algorithm |
| Leader Election | 5.2 | Choosing one coordinator among many |
| Distributed Lock | 5.2 | Mutual exclusion across machines |
| Eventual Consistency | 5.3 | Convergence without immediate agreement |
| Version Vectors | 5.3 | Tracking causality without clocks |
| CRDTs | 5.3 | Conflict-free data structures |

---

## Prerequisites

- **Recommended**: [Systems Thinking Track](../systems-thinking/) — Understanding system interactions
- **Recommended**: [Reliability Engineering Track](../reliability-engineering/) — Failure modes and resilience
- Helpful: Basic Kubernetes knowledge
- Helpful: Some programming experience

---

## Where This Leads

After completing Distributed Systems, you're ready for:

| Track | Why |
|-------|-----|
| [SRE Discipline](../../disciplines/sre/) | Apply distributed systems thinking to reliability |
| [Platform Engineering Discipline](../../disciplines/platform-engineering/) | Build platforms on distributed foundations |
| [GitOps Discipline](../../disciplines/gitops/) | Eventual consistency in practice |
| [Observability Toolkit](../../toolkits/observability/) | Monitor distributed systems |

---

## Key Resources

Books referenced throughout this track:

- **"Designing Data-Intensive Applications"** — Martin Kleppmann (the definitive guide)
- **"Distributed Systems for Fun and Profit"** — Mikito Takada (free online)
- **"Database Internals"** — Alex Petrov

Papers:

- **"Time, Clocks, and the Ordering of Events"** — Leslie Lamport
- **"In Search of an Understandable Consensus Algorithm"** — Diego Ongaro (Raft)
- **"Dynamo: Amazon's Highly Available Key-value Store"** — DeCandia et al.

---

## The Distributed Mindset

| Question to Ask | Why It Matters |
|-----------------|----------------|
| "What if this call fails?" | Design for partial failure |
| "What if it's just slow?" | Can't distinguish slow from dead |
| "Do we need consensus here?" | Consensus is expensive, use sparingly |
| "What consistency do we need?" | Match consistency to requirements |
| "How do we handle conflicts?" | Concurrent writes will happen |
| "What's the failure domain?" | Understand blast radius |

---

## Foundations Complete

This is the final track in the Foundations series. You've now covered:

1. **Systems Thinking**: See systems as interconnected wholes
2. **Reliability Engineering**: Design for failure, measure with SLOs
3. **Observability Theory**: Understand through metrics, logs, traces
4. **Security Principles**: Defense in depth, least privilege
5. **Distributed Systems**: Consensus, consistency, coordination

These foundations prepare you for the practical Disciplines and Toolkits tracks.

---

*"A distributed system is one in which the failure of a computer you didn't even know existed can render your own computer unusable."* — Leslie Lamport

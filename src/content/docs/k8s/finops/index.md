---
title: "FinOps Certified Practitioner (FOCP)"
sidebar:
  order: 1
  label: "FinOps"
---
> **Multiple-choice exam** | 60 minutes | 50 questions | $325 USD | 75% passing score

## Overview

The FinOps Certified Practitioner (FOCP) validates your understanding of cloud financial management — the practice of bringing financial accountability to the variable spend model of cloud. It is a **conceptual exam**, not a hands-on lab. You will answer multiple-choice questions about FinOps principles, lifecycle phases, organizational models, and cloud billing.

> **Important**: This certification is from the **FinOps Foundation** (a Linux Foundation project), **NOT** CNCF. The content is largely non-technical. You won't write kubectl commands or configure clusters. Think business strategy meets cloud economics.

**Who is this for?** Engineers, finance professionals, and managers who need to understand how organizations manage and optimize cloud spending. If you've ever asked "why is our cloud bill so high?" — this is for you.

---

## Exam Domains

| Domain | Weight | Module |
|--------|--------|--------|
| FinOps Lifecycle | 30% | [Module 1](module-1.1-finops-fundamentals/) |
| FinOps Capabilities | 28% | [Module 2](module-1.2-finops-practice/) |
| FinOps Principles | 12% | [Module 1](module-1.1-finops-fundamentals/) |
| Teams & Motivation | 12% | [Module 1](module-1.1-finops-fundamentals/) |
| Terminology & Cloud Bill | 10% | [Module 2](module-1.2-finops-practice/) |
| Challenge of Cloud | 8% | [Module 1](module-1.1-finops-fundamentals/) |

---

## Learning Path

```
FOCP PREPARATION PATH
══════════════════════════════════════════════════════════════

Module 1: FinOps Fundamentals (conceptual)
├── What is FinOps and why it exists
├── The 6 FinOps Principles
├── FinOps Lifecycle: Inform → Optimize → Operate
├── Team structure and organizational models
└── Covers: Principles (12%), Lifecycle (30%),
    Teams (12%), Challenge of Cloud (8%)

Module 2: FinOps in Practice (applied)
├── Cost allocation: tags, labels, showback, chargeback
├── Budgeting, forecasting, and rate optimization
├── Workload optimization and right-sizing
├── Cloud billing anatomy
├── Kubernetes-specific FinOps
└── Covers: Capabilities (28%), Terminology (10%)

Bonus: Hands-On with OpenCost (toolkit)
└── OpenCost installation, cost dashboards, right-sizing
    See: platform/toolkits/developer-experience/scaling-reliability/module-6.4-finops-opencost.md
```

---

## Module Overview

| # | Module | Complexity | Time | Focus |
|---|--------|------------|------|-------|
| 1 | [FinOps Fundamentals](module-1.1-finops-fundamentals/) | `[MEDIUM]` | 45 min | Principles, lifecycle, teams, organizational models |
| 2 | [FinOps in Practice](module-1.2-finops-practice/) | `[MEDIUM]` | 50 min | Cost allocation, optimization, billing, K8s FinOps |

---

## Related KubeDojo Content

The FOCP is conceptual, but KubeDojo's Platform Engineering track covers the **hands-on implementation** of FinOps practices in Kubernetes:

| Module | Topic | Relevance |
|--------|-------|-----------|
| [OpenCost Toolkit](../../platform/toolkits/developer-experience/scaling-reliability/module-6.4-finops-opencost/) | OpenCost installation, cost dashboards, right-sizing | Direct — the practical side of Module 2 |
| [Karpenter](../../platform/toolkits/developer-experience/scaling-reliability/module-6.1-karpenter/) | Node autoscaling, spot instance strategies | Supports rate optimization concepts |
| [KEDA](../../platform/toolkits/developer-experience/scaling-reliability/module-6.2-keda/) | Event-driven autoscaling | Supports workload optimization concepts |

---

## Exam Tips

- **This is a business exam, not a technical exam.** You won't write code or configure anything. Focus on understanding *concepts*, *processes*, and *organizational dynamics*.
- **Memorize the 6 FinOps Principles.** They appear directly in exam questions and are the foundation for everything else.
- **Know the lifecycle phases cold.** 30% of the exam tests Inform, Optimize, and Operate. Understand what activities happen in each phase.
- **Understand motivations by persona.** The exam tests whether you know what engineers vs. finance vs. executives care about — these are different.
- **Read questions carefully.** Multiple-choice exams test nuance. "Best" answer vs. "correct" answer matters.
- **Budget your time.** 50 questions in 60 minutes = ~72 seconds per question. Flag and move on if stuck.

---

## Study Strategy

```
WEEK 1 (recommended)
══════════════════════════════════════════════════════════════

Day 1-2: Module 1 — FinOps Fundamentals
├── Read and understand all 6 principles
├── Master the lifecycle diagram (Inform/Optimize/Operate)
└── Complete all quiz questions

Day 3-4: Module 2 — FinOps in Practice
├── Understand cost allocation models (showback vs chargeback)
├── Learn rate optimization strategies
├── Study cloud billing terminology
└── Complete all quiz questions

Day 5: Review and Reinforce
├── Re-take both module quizzes without peeking
├── Review any topics where you scored below 80%
└── Optional: Walk through the OpenCost toolkit module
    for hands-on context

Day 6-7: Practice
├── Review FinOps Foundation's official materials
├── Focus on weak areas from quiz results
└── Take the exam with confidence
```

---

## Related Certifications

```
FINOPS + CLOUD NATIVE PATH
══════════════════════════════════════════════════════════════

FinOps Foundation:
├── FOCP (FinOps Certified Practitioner) ← YOU ARE HERE
├── FOCSE (FinOps Certified Service Engineer)
└── FOCPE (FinOps Certified Platform Engineer)

CNCF (complementary):
├── KCNA (Cloud Native Associate) — K8s fundamentals
├── CKA (K8s Administrator) — Cluster operations
└── CNPE (Platform Engineer) — Includes cost management
```

The FOCP pairs well with CKA or CNPE. FinOps gives you the business context; Kubernetes certifications give you the technical skills to implement cost optimization.

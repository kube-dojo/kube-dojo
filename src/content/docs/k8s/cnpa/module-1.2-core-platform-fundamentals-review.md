---
title: "CNPA Core Platform Fundamentals Review"
slug: k8s/cnpa/module-1.2-core-platform-fundamentals-review
sidebar:
  order: 102
---

> **CNPA Track** | Multiple-choice exam prep | **Core domain review**

## Why This Module Matters

This is the highest-weighted CNPA domain, so it deserves the most disciplined review. The exam is testing whether you understand why platform engineering exists, what problem it solves, and what "good" looks like when developers consume platform capabilities.

The core idea is simple:
- DevOps asks teams to own more of the stack.
- Platform engineering reduces that burden with shared products and paved roads.
- The platform is successful only if developers actually choose to use it.

If you remember that, a lot of CNPA questions become easier to eliminate.

## What You'll Learn

After this module, you will be able to:

- explain platform engineering as a product discipline
- separate platform engineering from DevOps and SRE without flattening them together
- identify the purpose of internal developer platforms, golden paths, and self-service
- understand where GitOps and Infrastructure as Code fit into platform engineering
- recognize the difference between guardrails and bottlenecks

## Core Ideas

### Platform Engineering Is Product Thinking

A platform team is not just "ops with a nicer title." It behaves more like a product team:

- it has users, not tickets only
- it gathers feedback
- it iterates on adoption and usability
- it measures success in developer outcomes

The platform is only useful if it makes the rest of the engineering organization faster, safer, and more consistent.

### Developer Experience Is Not Decoration

Developer experience is not about adding a pretty portal on top of painful processes. It is about reducing the number of decisions, handoffs, and repeated steps required to ship software.

Good DevEx usually means:
- fewer context switches
- a smaller set of supported paths
- clear defaults
- visible documentation
- fast feedback when something goes wrong

### Golden Paths Need Guardrails

A golden path is the recommended route for a common workflow. It should be:
- opinionated enough to be useful
- flexible enough to fit real workloads
- documented enough to reduce support burden
- measured so you know whether people actually use it

The exam may try to frame golden paths as restrictions. The better answer is that they are curated paths that reduce accidental complexity.

### Internal Developer Platforms (IDPs)

An IDP is the surface area through which developers request and operate platform capabilities.

An IDP can expose:
- application templates
- service scaffolds
- deployment flows
- secrets or identity bootstrapping
- observability defaults
- infrastructure requests

The important idea is not the UI itself. It is the abstraction boundary between developers and the lower-level systems.

### Self-Service Infrastructure

Self-service means developers can provision what they need without waiting on a manual platform ticket, but it does not mean they bypass governance.

Self-service should still include:
- policy
- defaults
- quotas or limits
- auditability
- rollback or remediation paths

That is one of the most common exam traps: self-service without controls is not mature platform engineering.

## Exam Comparison Table

| Concept | Best description |
|---|---|
| DevOps | A culture and operating model that reduces silos and improves delivery |
| Platform engineering | A discipline for building internal products that reduce cognitive load |
| SRE | A reliability-focused operating model using error budgets and engineering discipline |
| IDP | The developer-facing interface for platform capabilities |
| Golden path | The preferred path for a common workflow |

## Recommended KubeDojo Review Map

- [What is Platform Engineering?](../../../platform/disciplines/core-platform/platform-engineering/module-2.1-what-is-platform-engineering/)
- [Developer Experience](../../../platform/disciplines/core-platform/platform-engineering/module-2.2-developer-experience/)
- [Internal Developer Platforms](../../../platform/disciplines/core-platform/platform-engineering/module-2.3-internal-developer-platforms/)
- [Golden Paths](../../../platform/disciplines/core-platform/platform-engineering/module-2.4-golden-paths/)
- [Self-Service Infrastructure](../../../platform/disciplines/core-platform/platform-engineering/module-2.5-self-service-infrastructure/)
- [Platform Maturity](../../../platform/disciplines/core-platform/platform-engineering/module-2.6-platform-maturity/)
- [What is GitOps?](../../../platform/disciplines/delivery-automation/gitops/module-3.1-what-is-gitops/)
- [IaC Fundamentals](../../../platform/disciplines/delivery-automation/iac/module-6.1-iac-fundamentals/)
- [What is Observability?](../../../platform/foundations/observability-theory/module-3.1-what-is-observability/)
- [Incident Management](../../../platform/disciplines/core-platform/sre/module-1.5-incident-management/)

## Common Mistakes

| Mistake | Why it is wrong | Better answer |
|---|---|---|
| Treating platform engineering as a tool choice | The exam tests the operating model, not just the stack | Explain the product mindset first |
| Confusing developer portal with platform | A portal can be part of the platform, but it is not the whole thing | Talk about the abstraction and the capabilities behind it |
| Thinking self-service removes governance | CNPA expects mature guardrails | Pair self-service with policies and defaults |
| Assuming adoption is optional | A platform no one uses is not successful | Treat adoption as a core success metric |

## Key Phrases To Remember

- "Platform as a product"
- "Reduce cognitive load"
- "Paved road, not forced road"
- "Self-service with guardrails"
- "Success is measured by adoption and outcomes"

## Next Module

Continue with [CNPA Delivery, APIs, and Observability Review](./module-1.3-delivery-apis-and-observability-review/).

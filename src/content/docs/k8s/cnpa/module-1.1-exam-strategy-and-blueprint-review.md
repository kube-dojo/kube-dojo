---
title: "CNPA Exam Strategy and Blueprint Review"
slug: k8s/cnpa/module-1.1-exam-strategy-and-blueprint-review
sidebar:
  order: 101
---

> **CNPA Track** | Multiple-choice exam prep | **120 minutes** | **No prerequisites** | **Beginner**

## Why This Module Matters

The CNPA exam is not a tooling exam. It tests whether you understand the ideas behind modern platform engineering well enough to choose the right answer when the wording changes.

That means the best preparation is not memorizing product names. It is learning the language of platform engineering:
- platform as a product
- golden paths and self-service
- GitOps and Infrastructure as Code
- observability, security, and conformance
- APIs, provisioning, and developer experience

This module gives you the exam map before you start reading the deeper content. If you know the blueprint, the rest of the track becomes a guided study path instead of a pile of related ideas.

## What You Need To Know First

CNPA is an online, proctored, multiple-choice exam. The official curriculum groups the exam into six domains:

| Domain | Weight | What it is really testing |
|---|---:|---|
| Platform Engineering Core Fundamentals | 36% | Whether you understand the platform engineering model itself |
| Platform Observability, Security, and Conformance | 20% | Whether you can separate signals, controls, and guardrails |
| Continuous Delivery & Platform Engineering | 16% | Whether you understand how platform delivery works in practice |
| Platform APIs and Provisioning Infrastructure | 12% | Whether you understand self-service provisioning and reconciliation |
| IDPs and Developer Experience | 8% | Whether you know how internal platforms serve developers |
| Measuring your Platform | 8% | Whether you can judge if a platform is actually working |

The mistake learners make is assuming the smallest domains are optional. They are not. A 12% or 8% domain can still decide a borderline score if it is the topic that appears in a confusing question.

## What You'll Learn

After this module, you will be able to:

- choose a study order that matches the CNPA weightings
- recognize which questions are about concepts rather than products
- separate platform engineering from DevOps, SRE, and pure infrastructure work
- identify where the KubeDojo platform track already covers the CNPA blueprint
- use practice questions without overfitting to one phrase or one vendor

## CNPA Study Order

The most efficient order is:

1. Platform Engineering Core Fundamentals
2. GitOps and delivery concepts
3. Observability, security, and conformance
4. APIs and provisioning infrastructure
5. IDPs and developer experience
6. Measuring platform success
7. Full practice review

That order matters because the exam often layers concepts. A question about an internal developer platform may also assume you understand GitOps, self-service, and the platform-as-product mindset.

## Core Strategy

### 1. Read For Definitions, Not Products

If a question asks about a concept, answer with the concept first:

- platform as a product
- developer experience
- golden path
- self-service infrastructure
- reconciliation loop
- conformance policy
- platform measurement

Then map it to tools only if the question explicitly asks for tools.

### 2. Learn The Confusion Pairs

The exam likes comparisons:

| Pair | The trap |
|---|---|
| Platform engineering vs DevOps | Platform engineering reduces the burden on teams instead of asking every team to build everything themselves |
| Golden paths vs lock-in | Golden paths guide users; they are not meant to remove choice everywhere |
| Observability vs monitoring | Monitoring answers known questions; observability supports new questions |
| Declarative vs imperative | Declarative describes desired state; imperative describes steps |
| Self-service vs unmanaged freedom | Self-service still needs guardrails, policy, and visibility |

### 3. Use The Weighting To Your Advantage

The biggest domain is core fundamentals, so your study time should reflect that. But do not ignore the smaller domains. CNPA is broad by design, and many learners lose easy points because they over-study the concepts they already like.

## Recommended Review Path In KubeDojo

Start here:
- [What is Platform Engineering?](../../../platform/disciplines/core-platform/platform-engineering/module-2.1-what-is-platform-engineering/)
- [Developer Experience](../../../platform/disciplines/core-platform/platform-engineering/module-2.2-developer-experience/)
- [Internal Developer Platforms](../../../platform/disciplines/core-platform/platform-engineering/module-2.3-internal-developer-platforms/)
- [Golden Paths](../../../platform/disciplines/core-platform/platform-engineering/module-2.4-golden-paths/)
- [Self-Service Infrastructure](../../../platform/disciplines/core-platform/platform-engineering/module-2.5-self-service-infrastructure/)
- [Platform Maturity](../../../platform/disciplines/core-platform/platform-engineering/module-2.6-platform-maturity/)
- [What is GitOps?](../../../platform/disciplines/delivery-automation/gitops/module-3.1-what-is-gitops/)
- [What is Observability?](../../../platform/foundations/observability-theory/module-3.1-what-is-observability/)

Then move into the more targeted material:
- GitOps drift and promotion
- IaC and provisioning infrastructure
- OPA, Kyverno, and security guardrails
- Crossplane and operator-style provisioning
- SRE incident and postmortem thinking

## Exam-Day Workflow

Use a three-pass rhythm:

1. Answer the definition questions immediately.
2. Mark the comparison questions that need a second look.
3. Return to the scenario questions once the easier points are secure.

This is a theory exam. The right answer is often the one that most faithfully reflects the platform operating model, not the one with the most tool names.

## Common Mistakes

| Mistake | Why it hurts | Better approach |
|---|---|---|
| Memorizing vendors instead of concepts | Questions can describe the same idea with different tool names | Anchor your answer in the concept |
| Treating self-service as "anything goes" | CNPA expects guardrails, not chaos | Pair self-service with policy and measurement |
| Studying only the largest domain | Small domains still contribute meaningful points | Cover the full blueprint |
| Confusing platform engineering with pure ops | The exam emphasizes product thinking for developers | Learn the platform-as-product model |

## Quick Self-Check

- Can you explain why a platform team should care about developer experience?
- Can you distinguish observability from monitoring without using tool names?
- Can you explain why reconciliation is central to both GitOps and platform provisioning?
- Can you name at least one metric that tells you whether a platform is being adopted?

If you cannot answer those four questions cleanly, keep studying before you jump into the practice sets.

## Next Module

Continue with [CNPA Core Platform Fundamentals Review](./module-1.2-core-platform-fundamentals-review/).

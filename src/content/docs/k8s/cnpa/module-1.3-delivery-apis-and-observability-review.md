---
title: "CNPA Delivery, APIs, and Observability Review"
slug: k8s/cnpa/module-1.3-delivery-apis-and-observability-review
sidebar:
  order: 103
---

> **CNPA Track** | Multiple-choice exam prep | **Delivery, APIs, observability, and measurement**

## Why This Module Matters

This module covers the parts of CNPA that prove a platform is not just a philosophy. A good platform has delivery flows, provisioning APIs, observability, policy, and metrics that tell you whether the platform is actually helping.

If the previous module was about the platform as a product, this one is about how the product behaves in practice.

## What You'll Learn

After this module, you will be able to:

- distinguish delivery, release, and promotion concepts
- explain why reconciliation-based provisioning matters
- identify observability building blocks and conformance controls
- choose the right high-level metric for platform success
- avoid exam traps around tooling, API style, and feedback loops

## Part 1: Delivery And Release

CNPA questions about delivery usually test whether you know the difference between:

- continuous integration
- continuous delivery
- continuous deployment
- progressive delivery
- release promotion

The exam does not expect implementation details. It expects you to understand that a platform should make delivery repeatable, observable, and safe.

### Common distinctions

| Term | Meaning |
|---|---|
| Continuous integration | Changes are merged and verified frequently |
| Continuous delivery | The system is always in a deployable state |
| Continuous deployment | Deployments happen automatically after checks pass |
| Progressive delivery | Release strategies such as canary or blue-green |
| Promotion | Moving the same artifact across environments with controls |

The right answer is often the one that says "reduce manual handoffs and make outcomes reproducible."

## Part 2: Platform APIs And Provisioning

The exam often uses API language to test whether you understand self-service infrastructure.

Good platform APIs:
- are declarative
- return a stable desired state
- hide implementation details behind a clear contract
- can be reconciled repeatedly

This is where CRDs, operators, and Crossplane-style abstractions matter. The point is not "Kubernetes everywhere." The point is exposing a safe, reusable interface to platform consumers.

Recommended study anchors:
- [Self-Service Infrastructure](../../../platform/disciplines/core-platform/platform-engineering/module-2.5-self-service-infrastructure/)
- [CRDs and Operators](../../../k8s/cka/part1-cluster-architecture/module-1.5-crds-operators/)
- [Crossplane](../../../platform/toolkits/infrastructure-networking/platforms/module-7.2-crossplane/)
- [Kubebuilder](../../../platform/toolkits/infrastructure-networking/platforms/module-3.4-kubebuilder/)

### What The Exam May Ask

- What makes a provisioning API "platform-like" rather than "ticket-like"?
- Why is reconciliation useful for infrastructure requests?
- How do CRDs fit into self-service infrastructure?
- What is the relationship between claims, composite resources, and the underlying provider resources?

## Part 3: Observability And Conformance

Observability is not the same as logging. CNPA wants you to understand the full picture:

- metrics show trends
- logs show events and context
- traces show request flow across services

Conformance is about proving the platform behaves consistently and safely. That can include:
- policy enforcement
- standards for app delivery
- security guardrails
- reporting on whether workloads meet the expected platform baseline

Recommended study anchors:
- [What is Observability?](../../../platform/foundations/observability-theory/module-3.1-what-is-observability/)
- [The Three Pillars](../../../platform/foundations/observability-theory/module-3.2-the-three-pillars/)
- [From Data to Insight](../../../platform/foundations/observability-theory/module-3.4-from-data-to-insight/)
- [Security Mindset](../../../platform/foundations/security-principles/module-4.1-security-mindset/)
- [OPA & Gatekeeper](../../../platform/toolkits/security-quality/security-tools/module-4.2-opa-gatekeeper/)
- [Kyverno](../../../platform/toolkits/security-quality/security-tools/module-4.7-kyverno/)

### Observability Traps

| Trap | Better answer |
|---|---|
| Monitoring and observability are synonyms | Monitoring is predefined; observability supports new questions |
| High-cardinality data is always good | High-cardinality data is useful in the right telemetry layer, not as a blanket metric label strategy |
| Policies are only for security teams | Platform policies are part of the user experience and platform baseline |

## Part 4: Measuring Your Platform

This domain is small, but it is not soft. The exam wants to know whether you understand that a platform should be measured like a product.

Useful measurement categories:
- adoption
- developer satisfaction
- time to first successful deploy
- time to provision a standard service
- error rate or incident reduction
- policy compliance or conformance

SRE concepts help here:
- [Incident Management](../../../platform/disciplines/core-platform/sre/module-1.5-incident-management/)
- [Postmortems](../../../platform/disciplines/core-platform/sre/module-1.6-postmortems/)

The point is to prove the platform improves outcomes, not just that it exists.

## Common Mistakes

| Mistake | Why it hurts | Better answer |
|---|---|---|
| Treating delivery as only "CI/CD" | CNPA also cares about promotion and safe release | Include release strategy and environment flow |
| Forgetting observability is a system property | The exam may separate telemetry from insight | Explain the system, not just the tools |
| Overfocusing on one metric | A platform can look busy and still be ineffective | Use adoption plus reliability plus developer outcomes |
| Treating APIs as implementation details | The platform itself is often exposed through APIs | Think self-service contract first |

## Mini Recall Check

- Can you explain why continuous deployment is not the same as progressive delivery?
- Can you describe a self-service API without naming a product?
- Can you separate observability from monitoring in one sentence?
- Can you name at least two metrics that would tell you whether a platform is adopted?

## Next Module

Continue with [CNPA Practice Questions Set 1](./module-1.4-practice-questions-set-1/).

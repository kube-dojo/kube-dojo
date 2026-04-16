---
title: "CNPA Practice Questions Set 2"
slug: k8s/cnpa/module-1.5-practice-questions-set-2
sidebar:
  order: 105
---

> **CNPA Track** | Practice questions | Set 2

## How To Use This Set

This second set is designed to expose comparison traps. Focus on the reason each distractor is wrong.

## Questions

### 1. Which option best reflects platform engineering?

1. Every team builds its own deployment tooling.
2. A dedicated team builds reusable internal products and paved paths.
3. The ops team handles all provisioning requests manually.
4. Developers may use any workflow, with no standards.

<details>
<summary>Answer</summary>

**Correct answer: 2**

Platform engineering reduces duplicated effort by building shared products. It is not a return to centralized ticket handling.
</details>

### 2. What is the best description of reconciliation in a platform context?

1. A one-time setup step that happens only during deployment.
2. A loop that compares desired state to actual state and brings them together.
3. A manual approval process for every change.
4. A method of hiding drift from developers.

<details>
<summary>Answer</summary>

**Correct answer: 2**

Reconciliation is continuous, not one-time. It is the control-loop idea that underpins GitOps and many provisioning platforms.
</details>

### 3. Which combination belongs most naturally together?

1. Developer experience, golden paths, internal developer platforms
2. Ticket queues, tribal knowledge, ad hoc scripts
3. Monitoring only, no policies, no metrics
4. Manual approvals, one-off YAML, invisible drift

<details>
<summary>Answer</summary>

**Correct answer: 1**

Those three ideas form a coherent CNPA story: the platform exists to improve the developer journey.
</details>

### 4. Which statement about measurement is most accurate?

1. Platform success is only measured by cost reduction.
2. A platform should be measured with adoption, reliability, and time-to-value signals.
3. If the platform team is busy, the platform is healthy.
4. A platform needs no metrics if users are happy.

<details>
<summary>Answer</summary>

**Correct answer: 2**

Cost matters, but CNPA expects product thinking. Adoption and time-to-value are usually stronger indicators than activity.
</details>

### 5. Which is the best explanation of self-service with guardrails?

1. Developers can do anything they want.
2. The platform exposes safe paths with policy, limits, and auditability.
3. The platform team approves every request manually.
4. Developers never interact with the platform at all.

<details>
<summary>Answer</summary>

**Correct answer: 2**

The essence is autonomy within controlled boundaries. That is the pattern the exam wants you to recognize.
</details>

## Readiness Check

If you can explain why answers 2 in questions 1, 2, 4, and 5 are correct without re-reading the module, you are in good shape for the conceptual part of CNPA.

## Final Review Notes

- Platform engineering is a delivery model, not just a tool stack.
- A platform without adoption is a cost center.
- Self-service without policy is not mature platform engineering.

## Next Module

Move to the CGOA track if you also want the GitOps associate exam path.

---
title: "CNPA Practice Questions Set 1"
slug: k8s/cnpa/module-1.4-practice-questions-set-1
sidebar:
  order: 104
---

> **CNPA Track** | Practice questions | Set 1

## How To Use This Set

Do these questions under exam-like conditions. Read the question once, eliminate obviously wrong choices, and do not overthink wording that is trying to distract you from the concept.

## Questions

### 1. What best describes a platform team that succeeds?

1. It closes the most infrastructure tickets.
2. It builds internal products that developers actually choose to use.
3. It owns every production incident.
4. It removes all freedom from application teams.

<details>
<summary>Answer</summary>

**Correct answer: 2**

A platform team is successful when it behaves like a product team and improves developer outcomes. Ticket closure and incident ownership are operational metrics, not the core definition. Removing all freedom is the opposite of a useful platform.
</details>

### 2. Which statement best captures "golden path"?

1. The only legal way to deploy software.
2. A recommended, well-supported route for a common workflow.
3. A path that hides all platform complexity forever.
4. A legacy process that everyone must use manually.

<details>
<summary>Answer</summary>

**Correct answer: 2**

A golden path is opinionated guidance, not hard coercion. It should reduce friction and improve consistency while still leaving room for special cases where needed.
</details>

### 3. Which metric is the strongest sign that a platform is being adopted?

1. The number of Git commits in the platform repository.
2. The number of platform tickets assigned last week.
3. The percentage of teams using the paved path for a standard workflow.
4. The number of dashboards the platform team created.

<details>
<summary>Answer</summary>

**Correct answer: 3**

Adoption is about real usage by target users. Commit count and dashboard count are activity metrics, not user success metrics.
</details>

### 4. Which pair best shows the difference between observability and monitoring?

1. Observability answers only yes/no questions; monitoring explores unknowns.
2. Observability supports new questions; monitoring checks predefined conditions.
3. Both are identical as long as dashboards exist.
4. Monitoring is always more detailed than observability.

<details>
<summary>Answer</summary>

**Correct answer: 2**

Monitoring checks what you already know to watch. Observability helps you investigate what you did not predict in advance.
</details>

### 5. Which platform capability most directly supports self-service infrastructure?

1. A ticket queue with weekly review meetings.
2. A CRD or API that exposes a safe provisioning contract.
3. A spreadsheet of manual approvals.
4. A runbook stored in a wiki.

<details>
<summary>Answer</summary>

**Correct answer: 2**

Self-service requires a request interface, a contract, and a reconciliation model. A ticket queue can be part of operations, but it is not self-service.
</details>

## Review Notes

- If you hesitated between 1 and 2 on question 1, re-read the platform-as-product section.
- If you picked "only legal way" on question 2, you are overfitting golden paths into policy enforcement.
- If you confused observability with logging on question 4, go back to the observability review.

## Next Module

Continue with [CNPA Practice Questions Set 2](./module-1.5-practice-questions-set-2/).

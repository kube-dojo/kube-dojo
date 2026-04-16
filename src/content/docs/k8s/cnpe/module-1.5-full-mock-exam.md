---
title: "CNPE Full Mock Exam"
slug: k8s/cnpe/module-1.5-full-mock-exam
sidebar:
  order: 105
---

> **CNPE Track** | Complexity: `[COMPLEX]` | Time to Complete: 90-120 min
>
> **Prerequisites**: CNPE Exam Strategy and Environment, GitOps and Delivery Lab, Platform APIs and Self-Service Lab, Observability Security and Operations Lab

## What You'll Be Able to Do

After this module, you will be able to:
- run a realistic CNPE-style practice session from start to finish
- manage time across multiple domains without getting trapped by one task
- recognize whether a change belongs in Git, in a platform API, or in an operational fix
- verify each task before moving on
- review your own work like an examiner would

## Why This Module Matters

The fastest way to discover gaps is to run the whole system under pressure. A mock exam is where isolated skills become an integrated workflow.

This module is not meant to be read like theory. It is meant to be used like a rehearsal. If the earlier CNPE modules are the instrument training, this is the flight simulation.

> **The Dress Rehearsal Analogy**
>
> A real performance does not expose whether you can memorize the score. It exposes whether you can keep tempo, recover from mistakes, and finish strongly. CNPE works the same way.

## Mock Exam Rules

Use these rules when you rehearse:
- set a timer and do not pause it
- keep a small scratchpad of task state
- verify every change before moving on
- do not optimize for perfect elegance if a smaller correct fix exists
- if a task stalls, park it and return later

This is a practice exam, not a code review. You are trying to build pressure tolerance and sequencing skill.

## Sample Exam Flow

### Task 1: GitOps Delivery

You are given an application that is not syncing correctly.

Expected actions:
- inspect the repository intent
- fix the environment-specific change
- restore sync or correct the rollout path
- verify that the live state now matches the desired state

### Task 2: Platform API Self-Service

You are asked to provision or repair a self-service platform object.

Expected actions:
- read the CRD or claim
- identify the contract fields
- repair validation, status, or reconciliation issues
- confirm the platform object reaches the expected healthy state

### Task 3: Observability or Security Incident

You are given a failing service, policy denial, or runtime issue.

Expected actions:
- narrow the cause using metrics, logs, traces, or events
- apply the smallest safe fix
- preserve the platform guardrails
- verify the symptom is gone

### Task 4: Operations Follow-Up

You are asked to make the platform easier to operate after the incident.

Expected actions:
- confirm the right alerting or runbook signal exists
- document the fix or add the missing operational clue
- ensure the platform remains explainable for the next operator

## Suggested Scoring Rubric

Use this rubric after the run:

| Area | Full Credit | Partial Credit |
|------|-------------|----------------|
| Delivery | Sync or rollout converges with correct environment boundaries | Change works but promotion or verification is weak |
| Platform API | Contract is understood and the resource reconciles | Resource is created but status or contract reasoning is unclear |
| Operations | Root cause is identified and fixed safely | Symptom is improved but evidence is incomplete |
| Security | Guardrails stay intact while the issue is fixed | Fix works but weakens controls unnecessarily |
| Time Management | Tasks are sequenced and stuck work is parked | One task absorbs too much of the session |

Passing the mock exam is not about getting every detail perfect. It is about proving that your workflow is stable enough to survive pressure.

## What Good Looks Like

A strong run usually has these traits:
- easy points are collected first
- every task has a clear verification step
- the scratchpad stays short
- changes are scoped narrowly
- the final review pass catches small mistakes before time expires

If you notice yourself editing the same object repeatedly without new evidence, that is a sign to pause and re-evaluate.

## Common Failure Patterns

| Failure Pattern | What It Looks Like | Better Habit |
|-----------------|--------------------|--------------|
| Starting with a complex incident | The first task consumes your attention | Collect quick wins first |
| Confusing intent and implementation | You patch the wrong layer | Identify the contract before editing |
| Verifying too late | The exam ends before you discover the mistake | Verify after each change |
| Over-logging | Notes become a second project | Keep the scratchpad minimal |
| Overcorrecting | You solve one issue by creating another | Make the smallest safe fix |

## Hands-On Exercise

**Task**: Run a full 60-minute CNPE rehearsal.

**Steps**:
1. Pick one delivery, one API, and one operations task from the CNPE track.
2. Set the timer.
3. Solve the tasks in the order that gives you the most points fastest.
4. Use the final 10 minutes for a review pass.
5. Grade yourself using the rubric above.

**Success Criteria**:
- [ ] You finish all three domains without losing the timer discipline
- [ ] Every task has a verification command or signal
- [ ] You can explain at least one decision you would change on the next run

**Verification**:
```bash
git status --short
kubectl get events -A --sort-by=.lastTimestamp | tail -n 20
kubectl get all -n <namespace>
```

## Debrief Questions

1. Which task consumed the most time, and why?
2. Did you move too early on any hard task?
3. Where did verification save you from a bad assumption?
4. Which platform layer was easiest to reason about under pressure?

## Quiz

1. Why is a mock exam more valuable than reading another theory page?
   <details>
   <summary>Answer</summary>
   Because it exposes sequencing, verification, and time-management gaps that theory reading hides.
   </details>

2. What is the most important rule during a practice run?
   <details>
   <summary>Answer</summary>
   Keep the timer honest and verify each task before moving on. The mock should behave like the real exam.
   </details>

3. Why should you park a stuck task instead of brute-forcing it?
   <details>
   <summary>Answer</summary>
   Because one stuck task can cost the whole run. Parking it preserves time for easier points and often makes the problem easier when you return.
   </details>

4. What proves you are becoming CNPE-ready?
   <details>
   <summary>Answer</summary>
   You can complete multi-domain tasks with a stable read-act-verify loop, clear pacing, and minimal rework.
   </details>

## Next Step

After this module, return to the CNPE hub and start the full rehearsal again. The goal is not to memorize this mock exam. The goal is to make your exam workflow boringly repeatable.

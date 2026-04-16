---
title: "CNPE GitOps and Delivery Lab"
slug: k8s/cnpe/module-1.2-gitops-and-delivery-lab
sidebar:
  order: 102
---

> **CNPE Track** | Complexity: `[COMPLEX]` | Time to Complete: 60-75 min
>
> **Prerequisites**: CNPE Exam Strategy and Environment, GitOps discipline, ArgoCD/Flux, Argo Rollouts, Helm and Kustomize

## What You'll Be Able to Do

After this module, you will be able to:
- choose a GitOps delivery pattern that fits the exam task
- explain the difference between desired state, sync state, and live state
- promote an application between environments without breaking drift control
- troubleshoot a broken sync, a failed rollout, or an incorrect repo layout
- verify delivery outcomes instead of assuming that a successful command means success

## Why This Module Matters

GitOps is one of the highest-value CNPE areas because it tests the exact habits that platform teams rely on in production: declarative change, controlled promotion, repeatable deployment, and drift correction.

The exam usually will not ask you to "use GitOps" in the abstract. It will ask you to make a change safely and prove that the platform converged on the intended state. If you can translate that prompt into repo edits, sync checks, and deployment verification, you are already ahead of most candidates.

> **The Control Loop Analogy**
>
> GitOps is not "deploy from Git because Git is fashionable." It is a control loop: Git defines the target, the delivery system compares target and reality, and reconciliation closes the gap.

## What CNPE Wants You to Understand

The CNPE delivery domain is not just about tool names. It is about:
- how app state moves from repository to cluster
- how environment promotion is represented
- how you detect and fix drift
- when to use progressive delivery versus a straight rollout
- how to verify that the application changed for the right reason

The tools in the track matter because they express those ideas:
- ArgoCD and Flux for reconciliation
- Helm and Kustomize for packaging and overlays
- Argo Rollouts for canary and blue-green delivery
- CI/CD tooling for the build and handoff side of the path

## The GitOps Mental Model

Think in three states:

| State | Question | Example |
|------|----------|---------|
| Desired | What should exist? | The manifest in Git says 3 replicas |
| Live | What exists right now? | The cluster is running 2 replicas |
| Sync | Are desired and live aligned? | The controller reports OutOfSync |

When exam tasks get tricky, they usually live in the gap between these states.

## Part 1: Delivery Architecture

### 1.1 Pick the Smallest Useful Path

For exam work, prefer the simplest delivery path that satisfies the task:
- if the task is about sync and promotion, use the GitOps controller
- if the task is about package reuse, use Helm or Kustomize
- if the task is about progressive rollout, use Argo Rollouts or an equivalent pattern

Do not over-engineer the path just because multiple tools are available.

### 1.2 A Clean Repo Shape

A practical repo layout usually looks like this:

```text
apps/
  payment-api/
    base/
    overlays/
      dev/
      staging/
      prod/
platform/
  clusters/
    dev/
    staging/
    prod/
```

The exact structure matters less than the discipline:
- base stays stable
- overlays express environment differences
- promotions are visible in Git history
- cluster state should be explainable from repo state

### 1.3 Sync, Promotion, and Drift

GitOps exam tasks often combine one or more of these behaviors:
- create a new app from a template
- fix a broken sync
- promote a change from dev to staging
- detect and correct drift
- confirm rollback to a previous revision

If the controller is healthy but the app is wrong, the bug is often in the repo, not the cluster.

## Part 2: Lab Scenarios

### 2.1 Scenario A: Bootstrap a Service

You are given a repo, a target namespace, and a service definition.

Your job:
- wire the app into the GitOps path
- ensure the controller can sync it
- confirm that the live state matches the desired state

Verify using:
```bash
kubectl get applications -A 2>/dev/null || true
kubectl get kustomizations -A 2>/dev/null || true
kubectl get pods -n <namespace>
```

### 2.2 Scenario B: Promote a Change

You update a config value or image tag in dev and must promote the same intent to staging.

Good promotion behavior:
- the change is visible in Git
- the change is scoped to the correct environment
- the controller converges without manual patching
- the verification shows the new revision

### 2.3 Scenario C: Recover from Drift

Someone changed a live object manually.

Your job:
- identify the source of drift
- decide whether Git or the cluster is the source of truth
- restore the intended state
- verify the controller stopped fighting you

If the live object keeps flipping back, do not keep editing the live object. Fix the repo or the delivery config.

## Part 3: Progressive Delivery

Progressive delivery is the safest answer when a task asks for staged exposure, rollback safety, or controlled rollout.

Use it when you need:
- canary traffic shifting
- blue/green cutover
- automated analysis before promotion
- a fast rollback path

Use a straight rollout when the task is simple and the safer path is not required.

## Common Mistakes

| Mistake | Problem | Better Approach |
|---------|---------|-----------------|
| Editing the live cluster first | You create drift and confusion | Make the change in Git unless the task says otherwise |
| Replacing one tool with another mid-task | You waste time rebuilding the path | Stick to the smallest working delivery pattern |
| Ignoring verification | Sync can succeed while the app is still wrong | Check revision, health, and runtime state |
| Misreading environment boundaries | The same change leaks into the wrong place | Keep base and overlays separate |
| Forgetting rollback | A bad rollout becomes a bigger incident | Confirm the revert path before making risky changes |

## Did You Know?

- GitOps is easier to reason about when you treat Git history as the audit log of intent.
- A clean environment overlay often solves more exam problems than a clever manifest trick.
- The most common delivery failure is not a broken controller; it is a bad mental model of desired state.

## Hands-On Exercise

**Task**: Rehearse a delivery change end-to-end.

**Steps**:
1. Create or locate an app overlay for a non-production environment.
2. Change one visible setting, such as image tag, replica count, or config value.
3. Apply the change through the GitOps path.
4. Verify sync status and live pod state.
5. Revert the change and verify rollback behavior.

**Success Criteria**:
- [ ] The change is visible in Git
- [ ] The controller reaches the expected sync state
- [ ] The live workload reflects the new revision
- [ ] Rollback returns the app to a known good state

**Verification**:
```bash
git diff --stat
kubectl rollout status deploy/<name> -n <namespace>
kubectl get events -n <namespace> --sort-by=.lastTimestamp | tail -n 10
```

## Quiz

1. What is the difference between desired state and live state?
   <details>
   <summary>Answer</summary>
   Desired state is what Git or the platform declares should exist. Live state is what the cluster actually has right now. GitOps works by reconciling the two.
   </details>

2. When should you prefer progressive delivery over a direct rollout?
   <details>
   <summary>Answer</summary>
   When the task needs staged exposure, a controlled rollout, or a safe rollback path. Progressive delivery reduces risk when changes can break users.
   </details>

3. What is the fastest way to tell whether you are dealing with drift?
   <details>
   <summary>Answer</summary>
   Compare the repo intent with the live object and check whether the delivery controller keeps reconciling the live object back to Git.
   </details>

4. Why is repository structure part of the exam skill?
   <details>
   <summary>Answer</summary>
   Because good structure makes environment promotion, rollback, and verification easier to reason about. CNPE cares about how the platform is operated, not just whether a manifest can be applied.
   </details>

## Next Module

Continue with [CNPE Platform APIs and Self-Service Lab](./module-1.3-platform-apis-and-self-service-lab/), where the control loop becomes a user-facing platform contract.

---
title: "CNPE Observability, Security, and Operations Lab"
slug: k8s/cnpe/module-1.4-observability-security-and-operations-lab
sidebar:
  order: 104
---

> **CNPE Track** | Complexity: `[COMPLEX]` | Time to Complete: 75-90 min
>
> **Prerequisites**: CNPE Exam Strategy and Environment, Observability Theory, SRE, Security Principles, DevSecOps, Prometheus, OpenTelemetry, Grafana, Loki, OPA/Gatekeeper, Kyverno, Falco

## What You'll Be Able to Do

After this module, you will be able to:
- interpret operational signals without mistaking dashboards for root cause
- connect metrics, logs, traces, and events into one incident story
- identify and correct common platform security and policy failures
- reason about access control, admission control, and runtime security as part of one system
- recover a platform service while preserving the minimum safe posture

## Why This Module Matters

CNPE expects more than deployment skills. A platform engineer must be able to see what is happening, explain why it is happening, and fix it without making the platform less safe in the process.

That means observability, security, and operations are not separate chapters in practice. They are one loop:
- observe the symptom
- determine the cause or constraint
- apply the smallest safe fix
- verify the result
- leave the system better documented than before

> **The Flight Deck Analogy**
>
> Dashboards are not the aircraft. They are instruments. The pilot does not win by staring at gauges harder; the pilot wins by interpreting the instrument cluster, choosing the right response, and confirming the aircraft is stable again.

## What CNPE Wants You to Understand

This domain typically combines:
- Prometheus and alerting behavior
- OpenTelemetry and trace context
- Grafana and log exploration
- incident triage and SLO thinking
- RBAC and admission controls
- secret handling and runtime policy
- workload hardening and workload identity

CNPE is looking for system-level thinking:
- what broke
- what signal proves it
- what fix is safe
- what verification confirms the platform is now in a good state

## Part 1: Observability as Evidence

### 1.1 Start with the Symptom, Not the Guess

When something fails, do not assume the first dashboard is the answer.

Use the evidence chain:
1. user-facing symptom
2. metric shift or alert
3. log pattern
4. trace or dependency failure
5. recent change or policy event

That order matters because it stops you from jumping to the wrong fix.

### 1.2 Signals You Should Read Quickly

Be fluent with:
- request latency and error rates
- pod restarts and crash loops
- controller reconciliation errors
- admission denials
- permission failures
- alert firing and silence state

If the exam gives you only one clue, use it to narrow the search instead of starting a broad tool tour.

### 1.3 SLO Thinking

Observability tasks often become easier when you think in terms of user impact:
- is the service still within its error budget?
- is the current issue a symptom or a cause?
- is the alert noise, or is it a meaningful signal?

CNPE rewards candidates who can distinguish an urgent incident from a noisy but low-impact warning.

## Part 2: Security and Policy

### 2.1 Security Is Part of the Fix

Do not solve an incident by removing the protections that keep the platform safe unless the task explicitly asks you to.

Common safe changes:
- correct RBAC
- tighten or repair a policy
- add a secret reference or workload identity binding
- fix a security context or network rule
- patch an admission problem

### 2.2 Read the Security Plane

Security problems often show up as:
- denied requests
- policy rejections
- missing permissions
- failed secret mounts
- blocked runtime behavior
- suspicious container activity

The right fix usually comes from understanding which plane blocked the change:
- API server / RBAC
- admission policy
- runtime policy
- network policy
- identity and secrets

### 2.3 Keep Policy Explicit

When policy is working, it should be visible in the manifest or controller config. Do not hide the logic in one-off manual changes.

Tools in this track reinforce that discipline:
- OPA/Gatekeeper for policy-as-code
- Kyverno for YAML-native policy
- Falco for runtime detection
- Vault and External Secrets for secrets
- SPIFFE/SPIRE or service mesh identity for workload trust

## Part 3: Operational Drills

### 3.1 Scenario A: A Service Is Slow

Your job:
- determine whether the issue is CPU saturation, memory pressure, network behavior, or an upstream dependency
- find the strongest evidence before changing anything
- apply the smallest safe remediation
- verify that the symptom improved

### 3.2 Scenario B: A Deployment Is Blocked

Your job:
- inspect the event stream
- find whether the block is caused by admission, RBAC, missing secrets, or a bad policy
- fix the actual blocker, not a symptom

### 3.3 Scenario C: A Policy Change Broke a Team

Your job:
- identify the policy that caused the failure
- decide whether the policy is correct but misconfigured, or simply too strict
- repair the policy without dropping guardrails entirely

### 3.4 Scenario D: A Runtime Signal Appears

Your job:
- confirm whether the signal is real
- inspect pod behavior, logs, and recent changes
- decide whether to isolate, patch, or roll back

## Common Mistakes

| Mistake | Problem | Better Approach |
|---------|---------|-----------------|
| Looking only at Grafana | Dashboards show symptoms, not full cause | Correlate metrics with logs, traces, and events |
| Breaking security to fix availability | The platform becomes less trustworthy | Fix the blocker while preserving controls |
| Changing multiple things at once | You cannot tell what fixed the issue | Change the smallest thing first |
| Ignoring admission or RBAC errors | The actual cause stays hidden | Check the control plane and policy plane early |
| Forgetting to verify after the fix | The incident may still be active | Re-check the original symptom and supporting signals |

## Did You Know?

- Good observability is not just "more data." It is evidence that reduces uncertainty.
- In platform work, the best security fix is often a configuration correction, not a big redesign.
- Many operational incidents are solved faster by reading events than by opening a dashboard first.

## Hands-On Exercise

**Task**: Rehearse an incident response loop.

**Steps**:
1. Pick one service or deployment from the platform track.
2. Assume it is failing for one of these reasons: resource pressure, RBAC, policy, or secret access.
3. Use metrics, logs, events, or traces to narrow the cause.
4. Apply the smallest safe fix.
5. Confirm the original symptom is gone.

**Success Criteria**:
- [ ] You can explain the cause using at least two signals
- [ ] Your fix does not remove the platform guardrails entirely
- [ ] You can verify the service or policy recovered

**Verification**:
```bash
kubectl get events -A --sort-by=.lastTimestamp | tail -n 20
kubectl logs deploy/<name> -n <namespace> --tail=50
kubectl describe deploy/<name> -n <namespace>
```

## Quiz

1. Why should you not treat a dashboard as the root cause?
   <details>
   <summary>Answer</summary>
   Because a dashboard is only one signal. Root cause usually needs correlation across metrics, logs, traces, events, and recent changes.
   </details>

2. What should you check first when a workload is blocked?
   <details>
   <summary>Answer</summary>
   Check the event stream and the most likely control plane blocker: RBAC, admission, policy, secret access, or runtime restrictions.
   </details>

3. Why is it risky to fix availability by disabling security controls?
   <details>
   <summary>Answer</summary>
   Because it solves the immediate incident by weakening the platform. CNPE expects you to preserve safe guardrails while restoring service.
   </details>

4. What proves an operations task is complete?
   <details>
   <summary>Answer</summary>
   The original symptom must be gone, the system should be in a healthy and explainable state, and the signals should show that the fix held.
   </details>

## Next Module

Continue with [CNPE Full Mock Exam](./module-1.5-full-mock-exam/), where GitOps, platform APIs, observability, and security are combined into a timed run.

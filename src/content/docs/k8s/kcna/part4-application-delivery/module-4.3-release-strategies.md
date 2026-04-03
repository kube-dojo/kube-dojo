---
title: "Module 4.3: Release Strategies (Theory)"
slug: k8s/kcna/part4-application-delivery/module-4.3-release-strategies
sidebar:
  order: 4
---

> **Complexity**: `[MEDIUM]` | Time: 30-40 minutes
>
> **Prerequisites**: [Module 4.1: CI/CD Fundamentals](../module-4.1-ci-cd/), [Module 4.2: Application Packaging](../module-4.2-application-packaging/)

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Compare** rolling update, blue-green, and canary release strategies by risk and complexity
2. **Explain** how Kubernetes Deployments implement rolling updates with maxSurge and maxUnavailable
3. **Identify** which release strategy fits a given scenario based on risk tolerance and traffic patterns
4. **Evaluate** rollback mechanisms and how automated rollback triggers reduce deployment risk

---

## Why This Module Matters

In June 2019, a major UK bank pushed a database migration to production using a single big-bang deployment. Every customer-facing service — mobile banking, online transfers, card payments — went down simultaneously at 14:23 on a Friday afternoon. The rollback took 9 hours. 1.9 million customers could not access their accounts over an entire weekend. The bank was fined 48.65 million GBP by regulators, their CEO issued a public apology, and post-incident analysis revealed the root cause was not the migration itself but the deployment strategy: everything was released at once, with no incremental validation and no fast rollback path.

The fix was not better code. The fix was a better release strategy. They moved to canary deployments with automated rollback triggers. The next migration — larger in scope — went out over four days with zero customer impact.

How you release software matters as much as what you release. This module teaches you the three core strategies Kubernetes supports, when each one fits, and how to think about risk when choosing between them. On the KCNA exam, you will be expected to recognize these patterns, understand their trade-offs, and match them to scenarios.

---

## What You Will Learn

- How rolling updates replace pods incrementally and what can go wrong
- How blue/green deployments enable instant rollback through traffic switching
- How canary releases use percentage-based traffic routing to limit blast radius
- A decision framework for choosing the right strategy based on risk appetite, cost, and speed

---

## Rolling Updates

Rolling updates are the default deployment strategy in Kubernetes. When you update a Deployment's pod template, Kubernetes gradually replaces old pods with new ones. At no point during the rollout is the application fully down — some pods run the old version while new pods come up.

### How It Works

Kubernetes uses two parameters to control rolling updates: `maxUnavailable` (how many old pods can be removed before new ones are ready) and `maxSurge` (how many extra pods can exist above the desired count during the update). The defaults are 25% for both.

```
Rolling Update Sequence (4 replicas, maxUnavailable=1, maxSurge=1)
─────────────────────────────────────────────────────────────────

Step 1: Steady state
  [v1] [v1] [v1] [v1]                    4 pods running

Step 2: New pod created (surge), one old pod terminating
  [v1] [v1] [v1] [v1:terminating] [v2:starting]

Step 3: v2 passes readiness probe, next old pod terminates
  [v1] [v1] [v1:terminating] [v2] [v2:starting]

Step 4: Continues until all replaced
  [v1:terminating] [v2] [v2] [v2:starting]

Step 5: Complete
  [v2] [v2] [v2] [v2]                    4 pods running
```

### When to Use Rolling Updates

Rolling updates work well when:
- The new version is backward-compatible with the old version (both run simultaneously during rollout)
- You can tolerate a brief period where clients hit a mix of old and new versions
- You do not need instant rollback — rolling back means doing another rolling update in reverse

### Risks to Know

**Mixed-version window**: During rollout, some traffic hits v1 and some hits v2. If v2 changes an API response format, clients may see inconsistent behavior. Database schema changes are especially dangerous here — v1 pods may not understand v2's schema.

**Slow rollback**: If v2 is broken, Kubernetes can roll back, but it is another rolling update in the opposite direction. Depending on pod count and startup time, full rollback can take minutes.

**Silent failures**: If readiness probes are too lenient (or missing), Kubernetes will consider broken pods "ready" and keep replacing old pods. By the time you notice, all pods may be running bad code.

---

## Blue/Green Deployments

Blue/green deployments run two complete environments side by side: "blue" (the current production version) and "green" (the new version). Traffic switches from blue to green all at once by updating the Service selector or Ingress rules.

### How It Works

```
Blue/Green Deployment
─────────────────────────────────────────────────────────────────

Phase 1: Blue is live, Green is deploying
                          ┌─────────────┐
  Users ──> Service ──────>│  Blue (v1)  │   LIVE
                          │  4 replicas  │
                          └─────────────┘
                          ┌─────────────┐
              (no traffic) │  Green (v2) │   TESTING
                          │  4 replicas  │
                          └─────────────┘

Phase 2: Green passes smoke tests, traffic switches
                          ┌─────────────┐
              (no traffic) │  Blue (v1)  │   STANDBY
                          │  4 replicas  │
                          └─────────────┘
                          ┌─────────────┐
  Users ──> Service ──────>│  Green (v2) │   LIVE
                          │  4 replicas  │
                          └─────────────┘

Phase 3: After confidence period, Blue is scaled down
                          ┌─────────────┐
  Users ──> Service ──────>│  Green (v2) │   LIVE
                          │  4 replicas  │
                          └─────────────┘
```

### When to Use Blue/Green

Blue/green is the right choice when:
- You need instant rollback — switching the Service selector back to "blue" takes seconds
- The new version has breaking changes that make mixed-version serving impossible
- You are deploying to a small number of services where doubling resources is affordable
- You want to run full integration tests against the green environment before any real user sees it

### Cost Implications

The obvious downside: you need double the resources during the transition. If your service normally runs 20 pods, you need capacity for 40 during the switchover. In cloud environments this means double the compute cost for the deployment window. In on-premises environments, you need that spare capacity available.

For large-scale deployments (hundreds of pods), this cost can be prohibitive. Most teams keep blue running for a "bake time" (30 minutes to a few hours) before scaling it down, adding to the expense.

---

## Canary Releases

Canary releases send a small percentage of traffic to the new version first. If metrics look good, traffic gradually shifts from old to new. If something goes wrong, only a small fraction of users are affected.

The name comes from coal miners who brought canaries into mines — if the bird stopped singing, the air was toxic. Your canary pods are the early warning system.

### How It Works

```
Canary Release (progressive traffic shift)
─────────────────────────────────────────────────────────────────

Stage 1: Canary gets 5% of traffic
                            ┌────────────────┐
  Users ──> Ingress ──95%──>│  Stable (v1)   │
               │            │  10 replicas    │
               │            └────────────────┘
               │            ┌────────────────┐
               └────5%─────>│  Canary (v2)   │
                            │  1 replica      │
                            └────────────────┘

              Watching: error rate, p99 latency, CPU usage

Stage 2: Metrics healthy after 10 min -- promote to 25%
                            ┌────────────────┐
  Users ──> Ingress ──75%──>│  Stable (v1)   │
               │            │  8 replicas     │
               │            └────────────────┘
               │            ┌────────────────┐
               └───25%─────>│  Canary (v2)   │
                            │  3 replicas     │
                            └────────────────┘

Stage 3: Full promotion (or instant rollback if metrics degrade)
                            ┌────────────────┐
  Users ──> Ingress ──────> │  New Stable(v2)│
                            │  10 replicas    │
                            └────────────────┘
```

### Traffic Routing Mechanisms

In Kubernetes, canary routing can be achieved through several mechanisms:

- **Replica ratio**: Run 1 canary pod alongside 9 stable pods. With a round-robin Service, roughly 10% of traffic hits the canary. Simple but imprecise.
- **Ingress annotations**: NGINX Ingress Controller supports `canary-weight` annotations for percentage-based splitting.
- **Service mesh**: Istio, Linkerd, and similar meshes give fine-grained traffic control with VirtualService weights. This is the most precise approach.
- **GitOps controllers**: Argo Rollouts and Flagger automate the entire canary lifecycle — traffic shifting, metric analysis, and automatic promotion or rollback.

### What Metrics Drive Promotion

A canary without metrics is just a smaller blast radius with no early warning. The promotion decision should be driven by:

- **Error rate**: Are 5xx responses higher than the baseline?
- **Latency**: Is p99 response time within acceptable bounds?
- **Saturation**: Is CPU or memory usage spiking compared to the same traffic volume on v1?
- **Business metrics**: Are conversion rates, transaction success rates, or other domain-specific numbers stable?

Automated canary analysis (provided by tools like Flagger or Argo Rollouts) compares these metrics between canary and stable pods and makes the promote/rollback decision without human intervention.

---

## Choosing the Right Strategy

There is no universally best strategy. The right choice depends on your risk tolerance, resource budget, and the nature of the change.

### Decision Matrix

| Factor | Rolling Update | Blue/Green | Canary |
|--------|---------------|------------|--------|
| **Rollback speed** | Minutes (reverse rollout) | Seconds (selector switch) | Seconds (shift traffic back) |
| **Resource overhead** | Minimal (+25% surge) | High (2x during switch) | Low-moderate (+5-25%) |
| **Mixed-version risk** | Yes, during rollout | No, clean switch | Yes, by design |
| **Blast radius** | Grows as rollout progresses | All-or-nothing | Controlled (5% then 25% etc.) |
| **Complexity** | Low (built into Kubernetes) | Medium (two Deployments + routing) | High (needs metrics + routing) |
| **Best for** | Routine, backward-compatible updates | Breaking changes, database migrations | Risky changes, new features, large user bases |
| **Worst for** | Schema-breaking changes | Resource-constrained environments | Changes without observable metrics |

### Thinking in Blast Radius

Blast radius is the percentage of users or systems affected if the deployment goes wrong. This is the most useful mental model for choosing a strategy:

- **Rolling update**: Blast radius starts small but grows to 100% as the rollout completes. If you catch a problem early, you limit damage. If you catch it late, most users are already affected.
- **Blue/green**: Blast radius is 0% (during testing) or 100% (after the switch). There is no middle ground, but rollback is instant.
- **Canary**: Blast radius is explicitly controlled. You decide: 5% first, then 25%, then 50%, then 100%. At each step, you can stop.

The right question is not "which strategy is best?" but "how much risk can we accept, and how fast do we need to recover?"

---

## Did You Know?

1. **Google deploys over 800,000 times per week** across its infrastructure. Nearly all of these use some form of canary analysis. Their internal system (called Canary Analysis Service) automatically compares dozens of metrics between canary and production before promoting any release.

2. **The term "blue/green deployment" was popularized by Jez Humble and David Farley** in their 2010 book *Continuous Delivery*. The color names are arbitrary — some organizations use "red/black" (Netflix's original terminology) or "A/B" (which can be confused with A/B testing).

3. **Kubernetes rolling updates were not always the default.** Before Deployments existed (pre-1.2), the only built-in option was ReplicationController's `kubectl rolling-update`, which was client-side and could leave the cluster in an inconsistent state if the client disconnected.

4. **A 2023 DORA (DevOps Research and Assessment) report found** that elite-performing teams deploy 973 times more frequently than low performers. The key enabler is not deployment speed but deployment safety — progressive delivery strategies that make each release low-risk.

---

## Common Mistakes

| Mistake | Why It Happens | What Goes Wrong |
|---------|---------------|-----------------|
| No readiness probes on rolling updates | Team assumes pods are ready when container starts | Kubernetes routes traffic to pods that cannot serve requests; cascading failures |
| Using blue/green for services with persistent connections | WebSocket or gRPC streams do not follow selector changes | Existing connections stay on blue; new connections go to green; split-brain behavior |
| Canary without baseline metrics | Team deploys canary but has no "normal" to compare against | Cannot distinguish canary problems from existing noise; false confidence in bad releases |
| Deploying database schema changes with rolling updates | Schema migration and code rollout happen simultaneously | v1 pods crash on new schema; v2 pods crash on old schema during the mixed-version window |
| Setting maxUnavailable too high | Team wants faster rollouts | Too many pods terminate at once; remaining pods cannot handle the load; partial outage |
| Treating canary percentage as canary safety | 5% traffic to canary feels safe | 5% of 10 million users is 500,000 people; canary percentage must be calibrated to actual user volume |

---

## Knowledge Check

Test your understanding with these scenario-based questions. Try to answer before revealing the explanation.

### Question 1

Your team runs an e-commerce platform with 20 backend pods. You are deploying a minor bug fix to the search autocomplete feature. The fix is backward-compatible, and you have comprehensive readiness probes. Which release strategy should you use?

<details>
<summary>Answer</summary>

A rolling update is the right choice here. The change is backward-compatible (so mixed-version serving is safe), it is a minor bug fix (low risk), and you have proper readiness probes to gate traffic. Rolling updates are the default Kubernetes strategy for good reason — they handle this exact scenario with minimal overhead and no extra infrastructure. Blue/green would waste resources doubling the pods, and canary adds unnecessary complexity for a low-risk change.
</details>

### Question 2

Your team is deploying a payment service rewrite that changes the database schema. The old code cannot read the new schema format, and the new code cannot read the old format. You need zero-downtime deployment. Which strategy fits?

<details>
<summary>Answer</summary>

Blue/green deployment is the only safe option here. A rolling update would create a mixed-version window where v1 pods try to read v2's schema and crash, causing an outage. A canary would have the same problem — canary pods would write in the new format while stable pods try to read it. Blue/green lets you migrate the schema, bring up the entire green environment, verify it works, and switch all traffic at once. The old blue environment stays available for instant rollback if needed (though rolling back a schema migration requires its own plan).
</details>

### Question 3

A social media company with 50 million daily active users wants to test a new recommendation algorithm. They expect it to increase engagement but are not sure if it might increase page load times. What release strategy should they use?

<details>
<summary>Answer</summary>

A canary release is ideal here. The change is uncertain (new algorithm, unknown performance impact), the user base is massive (so even a small percentage is statistically significant), and the key concern is a measurable metric (page load time). They can route 2% of traffic to the canary, monitor latency and engagement metrics for a defined period, and promote only if the numbers look good. Starting with 2% means roughly 1 million users see the change — enough for statistical confidence, but limited blast radius if latency spikes.
</details>

### Question 4

During a rolling update, you notice that new pods are passing readiness probes but returning 500 errors on approximately 10% of requests. The rollout is at 50% — half your pods are v2. What is happening, and what should you do?

<details>
<summary>Answer</summary>

The readiness probes are too lenient. They check that the pod can accept connections but do not verify that the application logic is working correctly. A readiness probe that only checks a basic health endpoint will pass even when business logic is broken. The immediate action is to pause the rollout (using `kubectl rollout pause`) and then initiate a rollback (`kubectl rollout undo`). The longer-term fix is to make readiness probes test a meaningful code path, not just "is the HTTP server listening." This is one of the most common rolling update failures.
</details>

### Question 5

Your organization runs a Kubernetes cluster with strict resource quotas — there is only 15% spare capacity at any time. You need to deploy a large update to a service that runs 40 pods. Which strategies are feasible and which are not?

<details>
<summary>Answer</summary>

Blue/green is not feasible — it requires doubling to 80 pods, which needs 100% extra capacity. You only have 15%. A rolling update is feasible if you set `maxSurge` to a low value (like 10-15%) so the extra pods fit within your spare capacity. A canary is also feasible since you only add a few pods (2-4) initially. The deciding factor between rolling update and canary is how risky the change is. For routine changes, rolling update with conservative surge settings works fine. For risky changes, start with a canary at 5-10% and promote gradually. Resource constraints are a real architectural factor in strategy selection.
</details>

---

## Decision Exercise

For each scenario below, choose a release strategy and write one to two sentences justifying your choice. Consider blast radius, rollback speed, resource constraints, and the nature of the change.

**Scenario A**: A healthcare startup (8 pods, no service mesh) is deploying a HIPAA-required encryption update. The update changes how data is encrypted at rest but does not change any APIs. Downtime during business hours is acceptable for up to 2 minutes.

**Scenario B**: A global streaming platform (200 pods across 3 regions) is rolling out a new video transcoding pipeline. Early internal testing shows a 3% chance of degraded video quality on certain codecs. They have Istio service mesh and Prometheus metrics.

**Scenario C**: An internal DevOps team (12 pods, single cluster) is updating their CI runner from v3.1 to v3.2. The changelog lists only dependency bumps and minor bug fixes. They have basic readiness probes.

<details>
<summary>Suggested Answers</summary>

**Scenario A**: Blue/green deployment. The encryption change may affect data read/write paths in ways that make mixed-version serving risky (v1 might not decrypt v2's data). Blue/green lets you test the green environment thoroughly before switching, and the team can accept the brief deployment window. With only 8 pods, the double-resource cost is manageable.

**Scenario B**: Canary release. The known 3% degradation risk on certain codecs is exactly what canary deployments are designed for. With Istio, they can route precisely 2% of traffic to the new pipeline, monitor video quality metrics in Prometheus, and promote gradually. At 200 pods and a global footprint, blue/green would require 400 pods temporarily — expensive and operationally complex across regions.

**Scenario C**: Rolling update. This is a low-risk, backward-compatible version bump to an internal service. The change is minor (dependency bumps), the service is small (12 pods), and it is not user-facing. A rolling update with default settings handles this cleanly. Adding canary or blue/green complexity is not justified for the risk level.
</details>

---

## Summary

Release strategies are not about technology — they are about risk management. Rolling updates handle the 80% case: routine, backward-compatible changes. Blue/green gives you a hard switch with instant rollback for breaking changes. Canary lets you validate uncertain changes against real traffic before committing.

The KCNA exam expects you to recognize these patterns, understand their trade-offs, and match them to scenarios. The key insight is that the choice depends on three factors: how risky the change is, how fast you need to recover if it fails, and how many resources you can afford to spend on safety.

> **Exam Tip**: When a KCNA question describes a deployment scenario, look for keywords. "Backward-compatible" and "gradual" point to rolling updates. "Instant rollback" and "breaking change" point to blue/green. "Small percentage," "metrics-driven," and "progressive" point to canary.

---

**Next Module**: [Back to KCNA Overview](../../kcna/)

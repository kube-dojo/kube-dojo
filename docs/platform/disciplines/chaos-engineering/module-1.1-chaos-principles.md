# Module 1.1: Principles of Chaos Engineering & Resilience

> **Discipline Module** | Complexity: `[QUICK]` | Time: 1.5 hours

## Prerequisites

Before starting this module:
- **Required**: [Kubernetes Basics](../../../prerequisites/kubernetes-basics/README.md) — Core cluster concepts and workloads
- **Required**: [Release Engineering](../sre/README.md) — Understanding deployment pipelines and rollbacks
- **Recommended**: Experience operating at least one production system
- **Recommended**: Familiarity with monitoring concepts (Prometheus, Grafana)

---

## Why This Module Matters

On October 22, 2012, an engineer at Netflix pushed a routine configuration change to a critical microservice. Within 45 minutes, the entire streaming platform was down for millions of users worldwide. The postmortem revealed something uncomfortable: nobody had tested what would happen when that exact service failed during peak traffic.

That outage, and dozens like it before, led to a fundamental question: **Why do we wait for production to teach us how our systems break?**

Chaos Engineering was born from this question. It is the discipline of proactively injecting controlled failures into systems to discover weaknesses before they become real outages. It sounds counterintuitive — deliberately breaking things to make them stronger — but it is the same logic behind fire drills, vaccine science, and military war games. You stress the system under controlled conditions so it survives uncontrolled ones.

**Here's the uncomfortable truth**: Your system will fail. The only question is whether you discover how it fails on your terms (during a planned experiment at 2 PM on a Tuesday) or on production's terms (at 3 AM on New Year's Eve when your on-call engineer is asleep).

This module teaches you the philosophy, scientific method, and safety practices of Chaos Engineering — everything you need before touching a single chaos tool.

---

## Did You Know?

> **Netflix's Chaos Monkey** was created in 2011 and randomly terminated EC2 instances in production. Engineers initially hated it. Within six months, they loved it — their services had become so resilient that individual instance failures caused zero customer impact. Netflix later open-sourced it, spawning an entire discipline.

> **The term "Chaos Engineering"** was formalized in a 2015 paper by Netflix engineers titled *"Principles of Chaos Engineering"*. Before that, the practice was informally called "chaos testing" or "failure injection." The name change was deliberate — engineering implies rigor, hypotheses, and the scientific method, not random destruction.

> **Amazon's GameDay tradition** started internally in 2004. Teams would simulate catastrophic failures (entire data center loss, database corruption) with executives watching. The practice was so effective at finding weaknesses that AWS eventually built it into their standard operating procedures. Today, AWS runs hundreds of Game Days per year across their organization.

> **The largest chaos experiment ever run** was by Google during the development of Spanner, their globally distributed database. Engineers simulated entire data center failures, network partitions across continents, and clock skew of several seconds — all simultaneously. The result was a database that maintains consistency across the planet with 99.999% availability.

---

## The Philosophy of Chaos Engineering

### It Is Not Random Destruction

Let's kill the biggest misconception immediately: Chaos Engineering is **not** about randomly breaking things and seeing what happens. That's vandalism, not engineering.

Chaos Engineering is a **disciplined investigation**. You form a hypothesis, design a controlled experiment, execute it with safety measures, observe the results, and draw conclusions. It follows the scientific method as rigorously as any laboratory experiment.

Think of it this way:

| What It Is NOT | What It IS |
|----------------|------------|
| Randomly killing pods | Hypothesis-driven experimentation |
| Breaking production for fun | Controlled failure injection with safety nets |
| Testing until something crashes | Verifying that systems behave as designed |
| Creating chaos | Discovering hidden chaos that already exists |
| A one-time activity | A continuous practice embedded in culture |

### The Core Insight

Every distributed system has **emergent behaviors** — behaviors that arise from the interaction of components but cannot be predicted by examining any single component in isolation.

Consider a microservices application with 20 services. Each service has been unit tested, integration tested, and load tested. Every individual component works correctly. But when Service A retries failed calls to Service B, and Service B is slow because Service C's database is under load, those retries amplify the load on Service B, which cascades into Service D, which has a 30-second timeout that blocks threads, which... you get the picture.

No amount of unit testing or code review would catch this. The failure only emerges from the **interaction** of components under specific conditions. Chaos Engineering is designed to surface exactly these emergent failures.

### Resilience vs. Robustness

These terms are often confused, but the distinction matters enormously:

**Robustness** means the system can handle *known* failure modes. You've tested for them, built handling for them, and verified the handlers work. A robust bridge can handle its rated wind load.

**Resilience** means the system can handle *unknown* or *unexpected* failure modes and recover. A resilient bridge sways in unexpected wind patterns and returns to its original position.

Chaos Engineering builds **resilience** — the ability to withstand and recover from failures you haven't explicitly planned for.

```
Robustness spectrum:

Fragile ─────── Robust ─────── Resilient ─────── Antifragile
 Breaks          Handles         Handles            Gets
 easily          known           unknown            stronger
                 failures        failures           from stress
```

The ultimate goal is **antifragility** — systems that actually improve when stressed. Netflix achieved this: every time Chaos Monkey killed an instance, engineers improved their services, making the entire platform stronger over time.

---

## The Scientific Method of Chaos

### The Chaos Engineering Cycle

Every chaos experiment follows a strict cycle. Skipping steps is how you turn engineering into vandalism.

```
┌──────────────────────────────────────────────────┐
│                 CHAOS CYCLE                       │
│                                                   │
│   1. Define Steady State                          │
│        ↓                                          │
│   2. Form Hypothesis                              │
│        ↓                                          │
│   3. Design Experiment                            │
│        ↓                                          │
│   4. Define Blast Radius & Abort Conditions       │
│        ↓                                          │
│   5. Run Experiment                               │
│        ↓                                          │
│   6. Observe & Measure                            │
│        ↓                                          │
│   7. Analyze Results                              │
│        ↓                                          │
│   8. Document & Share Findings                    │
│        ↓                                          │
│   (loop back to 1)                                │
└──────────────────────────────────────────────────┘
```

Let's examine each step in detail.

### Step 1: Define Steady State

Before you can detect a problem, you need to know what "normal" looks like. Steady state is not "everything is green" — it is a **measurable definition** of normal system behavior.

Good steady-state definitions:

| Metric | Steady State Value | Measurement Source |
|--------|--------------------|--------------------|
| Request latency (p99) | < 200ms | Prometheus histogram |
| Error rate (5xx) | < 0.1% | Istio telemetry |
| Order completion rate | > 98.5% | Business metrics DB |
| Pod restart count | 0 restarts/hour | kube-state-metrics |
| Queue depth | < 500 messages | RabbitMQ exporter |

Notice the last two rows. Steady state should include **business metrics**, not just infrastructure metrics. A system can have perfect CPU and memory while silently dropping orders.

```yaml
# Example: Steady state as a monitoring rule
# This becomes your "is the experiment safe?" check
groups:
  - name: chaos-steady-state
    rules:
      - alert: SteadyStateViolation
        expr: |
          (
            histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) > 0.2
            or
            sum(rate(http_requests_total{code=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) > 0.001
            or
            rate(orders_completed_total[5m]) / rate(orders_started_total[5m]) < 0.985
          )
        for: 1m
        labels:
          severity: chaos-abort
```

### Step 2: Form a Hypothesis

A chaos hypothesis has a specific format:

> **"We believe that [system behavior] will continue even when [failure condition], because [resilience mechanism]."**

Examples:

- "We believe that order processing will continue within 3 seconds even when the payment service pod is killed, because Kubernetes will restart it within 30 seconds and the retry logic in the order service will handle the brief outage."

- "We believe that search results will continue to be served even when 200ms of latency is added between the API gateway and the search service, because circuit breakers will trip after 5 failed requests and return cached results."

- "We believe that user sessions will be preserved even when a Redis Sentinel node is killed, because Sentinel will promote a replica within 10 seconds and the session middleware reconnects automatically."

Bad hypotheses (too vague):
- "The system should handle pod failures" — handle how? What metric?
- "Performance won't degrade" — by how much? What's acceptable?
- "Everything will keep working" — define "everything" and "working"

### Step 3: Design the Experiment

An experiment specification includes:

```yaml
# Chaos Experiment Specification (human-readable)
experiment:
  name: "Payment service pod failure during checkout"
  date: "2026-03-24"
  owner: "platform-team"
  approvers: ["lead-sre", "payment-team-lead"]

  hypothesis: >
    Order completion rate stays above 98.5% when the payment
    service pod is killed, due to Kubernetes auto-restart
    and order-service retry logic.

  steady_state:
    metrics:
      - name: order_completion_rate
        query: "rate(orders_completed[5m]) / rate(orders_started[5m])"
        expected: ">= 0.985"
      - name: p99_latency
        query: "histogram_quantile(0.99, rate(http_duration_bucket[5m]))"
        expected: "<= 0.5"

  injection:
    type: pod-kill
    target: "payment-service"
    namespace: "production"
    selector:
      app: payment-service
    count: 1  # kill 1 of 3 replicas

  abort_conditions:
    - "order_completion_rate < 0.95 for 2 minutes"
    - "p99_latency > 2s for 1 minute"
    - "any 500 errors on checkout endpoint"

  blast_radius:
    scope: "payment-service namespace only"
    max_impact: "1 pod out of 3 replicas"
    customer_impact: "possible 2-3s delay for ~5% of checkouts"

  duration: 10 minutes
  rollback: "kubectl rollout restart deployment/payment-service"
```

### Step 4: Blast Radius and Abort Conditions

**Blast radius** is the potential impact zone of your experiment. Always start small.

```
Blast Radius Progression:

Level 1: Single pod in staging          ← Start here
Level 2: Single pod in production
Level 3: Multiple pods in production
Level 4: Entire service in production
Level 5: Cross-service failure          ← Work up to here
Level 6: Availability zone failure
Level 7: Region failure                 ← Only for mature orgs
```

**Abort conditions** are your emergency brake. They must be:
- **Automated**: A human watching a dashboard is not fast enough
- **Measurable**: Based on metrics, not feelings
- **Preset**: Decided before the experiment, not during
- **Tested**: Verify the abort mechanism actually works before running chaos

```yaml
# Example abort configuration (Chaos Mesh style)
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: payment-pod-kill
spec:
  action: pod-kill
  mode: one
  selector:
    namespaces:
      - production
    labelSelectors:
      app: payment-service
  duration: "10m"
  # Abort is handled externally via monitoring + Chaos Mesh dashboard pause
```

### Step 5-8: Execute, Observe, Analyze, Share

**Execute**: Always run experiments during business hours when the team is available. Never run your first experiment at 3 AM or on a Friday afternoon.

**Observe**: Watch dashboards in real-time. Record everything — not just metrics, but observations. "The dashboard showed a spike at T+30s" is useful data.

**Analyze**: Did the system behave as hypothesized? If yes, increase the blast radius next time. If no, you found a weakness — that's a success! Write a remediation plan.

**Share**: The worst thing you can do with chaos results is keep them to yourself. Share findings broadly. Write them up. Present them at team meetings. The organizational learning is as valuable as the technical findings.

---

## Game Days vs. Continuous Chaos

There are two modes of practicing Chaos Engineering, and mature organizations use both.

### Game Days

A Game Day is a scheduled, focused chaos event. Think of it as a fire drill for your infrastructure.

**Structure of a Game Day:**

```
09:00 - Kickoff: Review today's experiments, assign roles
09:30 - Steady State Verification: Confirm all systems nominal
10:00 - Experiment 1: Pod failure in service A
10:30 - Debrief Experiment 1: Results, surprises, actions
11:00 - Experiment 2: Network partition between zones
11:30 - Debrief Experiment 2
12:00 - Lunch Break
13:00 - Experiment 3: Database failover simulation
13:30 - Debrief Experiment 3
14:00 - Wrap-up: Overall findings, action items, next Game Day date
```

**Roles during a Game Day:**

| Role | Responsibility |
|------|---------------|
| **Game Master** | Coordinates experiments, manages schedule |
| **Experimenter** | Executes the chaos injection |
| **Observer** | Monitors dashboards, records metrics |
| **Communicator** | Updates stakeholders, manages abort decisions |
| **Scribe** | Documents everything in real-time |

**When to use Game Days:**
- First-time chaos experiments in a new environment
- Testing complex, multi-service failure scenarios
- Training new team members on incident response
- Building organizational confidence in chaos practices
- Before major events (Black Friday, product launches)

### Continuous Chaos

Continuous chaos runs automated experiments on a schedule — hourly, daily, or triggered by deployments. This is the "Chaos Monkey" model.

**When to use Continuous Chaos:**
- After Game Days have validated basic resilience
- For well-understood failure modes with proven recovery
- To prevent resilience regression (services that were resilient staying resilient)
- To build confidence that auto-scaling and self-healing work continuously

**Maturity Model:**

```
Level 0: No chaos practices
           ↓
Level 1: Ad-hoc manual testing ("let's kill a pod and see what happens")
           ↓
Level 2: Structured Game Days (quarterly, documented, with hypotheses)
           ↓
Level 3: Automated chaos in staging (continuous, CI/CD integrated)
           ↓
Level 4: Automated chaos in production (with automated abort)
           ↓
Level 5: Chaos as culture (every team runs experiments, findings shared org-wide)
```

Most organizations are between Level 0 and Level 1. Getting to Level 2 is a massive improvement. Don't rush to Level 4 — premature continuous chaos in production causes the outages it's supposed to prevent.

---

## Building a Safety Culture

### The Pre-Requisites Before Any Chaos

Before running your first chaos experiment, these must be in place:

1. **Observability**: You need dashboards and alerts to see the impact. If you can't observe steady state, you can't detect deviation from it.

2. **Rollback capability**: You must be able to undo the experiment instantly. If you kill a pod and can't restart it, that's not chaos engineering — that's an outage.

3. **Communication channels**: Everyone who might be affected should know an experiment is happening. Use a dedicated Slack channel, not email.

4. **Management buy-in**: Your first experiment should not be a surprise to leadership. Get explicit approval, especially for production experiments.

5. **Incident response process**: If the experiment goes wrong, you need to handle it like a real incident. The chaos experiment becomes the incident trigger.

### The "Opt-In" Principle

Teams should never have chaos imposed on them. The opt-in principle states:

- Teams **volunteer** their services for chaos experiments
- Teams **define** their own steady state and abort conditions
- Teams **participate** in experiments on their services
- Teams **own** the remediation of discovered weaknesses

Forcing chaos on unwilling teams creates resentment, not resilience. The goal is cultural change, and culture cannot be mandated.

### Communicating About Chaos

When proposing chaos engineering to your organization, frame it correctly:

**Don't say**: "We want to break things in production."
**Do say**: "We want to verify our resilience claims before our customers test them for us."

**Don't say**: "We're going to inject failures everywhere."
**Do say**: "We're going to run controlled, scientific experiments to find weaknesses we can fix proactively."

**Don't say**: "What's the worst that could happen?"
**Do say**: "Here is our blast radius analysis, abort conditions, and rollback plan."

---

## Common Mistakes

| Mistake | Why It's a Problem | Better Approach |
|---------|-------------------|-----------------|
| Running chaos without observability | You can't measure impact if you can't see it — the experiment is useless or dangerous | Set up monitoring and dashboards first; verify you can detect the steady-state deviation |
| Skipping the hypothesis step | Without a hypothesis, you're just breaking things randomly with no learning objective | Always write "We believe X will happen because Y" before running any experiment |
| Starting in production | Your first chaos experiment should not risk customer impact while you're still learning the tools | Start in staging or dev; graduate to production only after multiple successful staging runs |
| No abort conditions | Without automated abort, a runaway experiment becomes a real outage | Define metrics-based abort conditions and verify they trigger correctly before running |
| Running experiments on Fridays | If the experiment causes lasting damage, no one wants to fix it over the weekend | Run chaos Tuesday through Thursday, during business hours, with the full team available |
| Blaming individuals for failures found | If chaos reveals a bug, blaming the developer who wrote it kills the program instantly | Treat findings as systemic improvements; celebrate discovery, not assign blame |
| Too large a blast radius too soon | Killing half your production pods on your first experiment guarantees an outage, not learning | Start with one pod in staging; increase blast radius only after successful smaller experiments |
| Not documenting results | Undocumented experiments provide no organizational learning and cannot be reproduced | Write up every experiment: hypothesis, results, actions, and share with the broader team |

---

## Quiz

Test your understanding of Chaos Engineering principles:

### Question 1: What distinguishes Chaos Engineering from random failure testing?

<details>
<summary>Show Answer</summary>

Chaos Engineering follows the **scientific method**: it starts with a hypothesis about system behavior, defines steady state, designs controlled experiments with abort conditions, and analyzes results to draw conclusions. Random failure testing has no hypothesis, no measurement plan, and no structured learning process. The key difference is **discipline and rigor** — Chaos Engineering is an engineering practice, not ad-hoc destruction.

</details>

### Question 2: Why should steady state include business metrics, not just infrastructure metrics?

<details>
<summary>Show Answer</summary>

Infrastructure metrics (CPU, memory, pod status) can all be "green" while the system is failing users. For example, all pods may be running, latency may be normal, but a logic bug introduced by a failure could cause orders to be silently dropped. **Business metrics** like order completion rate, checkout success rate, or user session count directly measure what matters to customers. If you only monitor infrastructure, you may miss failures that affect users but don't affect servers.

</details>

### Question 3: What is blast radius, and why does it matter?

<details>
<summary>Show Answer</summary>

Blast radius is the **potential impact zone** of a chaos experiment — how many services, users, or transactions could be affected if the experiment reveals a real weakness. It matters because chaos experiments can cause real damage if the system isn't as resilient as hypothesized. By starting with a small blast radius (one pod in staging) and gradually increasing it, you limit the potential damage while still gaining valuable insights. A blast radius that is too large too soon turns an experiment into an outage.

</details>

### Question 4: Why is "100% availability" a poor goal, and how does Chaos Engineering relate to this?

<details>
<summary>Show Answer</summary>

100% availability is impossible in distributed systems and pursuing it leads to extremely conservative operations that slow development to a crawl. Instead, systems should target a realistic SLO (like 99.95%) and use the remaining error budget for improvements, including chaos experiments. Chaos Engineering **consumes error budget** by deliberately injecting failures, but the insights gained make the system more resilient, which **preserves error budget** during real incidents. It's an investment: spend a small amount of error budget now to avoid spending a large amount during an uncontrolled failure later.

</details>

### Question 5: A team wants to start chaos engineering. They have monitoring, CI/CD, and management approval. What should their first experiment look like?

<details>
<summary>Show Answer</summary>

Their first experiment should be:
- **In staging**, not production
- **Single pod kill** of a stateless service with multiple replicas
- **Well-defined hypothesis**: "We believe Service X will continue serving requests when 1 of 3 pods is killed, because Kubernetes will restart it within 30 seconds and the load balancer will route traffic to healthy pods"
- **Clear abort conditions**: Automated, based on metrics
- **Short duration**: 5-10 minutes
- **Full team present**: Everyone watching dashboards, ready to intervene
- **Documented**: Written experiment plan shared in advance, results documented after

The goal of the first experiment is as much about **building the muscle** of running experiments as it is about the technical findings.

</details>

### Question 6: What is the difference between a Game Day and continuous chaos, and when should each be used?

<details>
<summary>Show Answer</summary>

A **Game Day** is a scheduled, focused event where the team runs multiple chaos experiments with the full team present, observing, and debriefing. It's best for first-time experiments, complex multi-service scenarios, training, and building organizational confidence.

**Continuous chaos** runs automated experiments on a schedule or triggered by deployments, without human supervision (but with automated abort conditions). It's best for well-understood failure modes, preventing resilience regression, and validating that auto-healing works consistently.

Organizations should **start with Game Days** and graduate to continuous chaos only after they've validated their resilience and abort mechanisms through multiple successful Game Days. Running continuous chaos before you've mastered Game Days is like running a marathon before you can jog a mile.

</details>

---

## Hands-On Exercise: Draft a Chaos Experiment Document

### Objective

Create a complete Chaos Experiment Document for a realistic Kubernetes application. This exercise builds the skill of structured thinking about chaos — the most important skill before touching any tool.

### Scenario

You are an SRE for an e-commerce platform running on Kubernetes. The platform has these services:

```
                    ┌──────────┐
                    │  Ingress │
                    └────┬─────┘
                         │
                    ┌────▼─────┐
                    │   API    │  (3 replicas)
                    │ Gateway  │
                    └────┬─────┘
                   ┌─────┼──────┐
              ┌────▼──┐ ┌▼────┐ ┌▼─────┐
              │Product│ │Cart │ │Order │  (2-3 replicas each)
              │Service│ │Svc  │ │Svc   │
              └───┬───┘ └──┬──┘ └──┬───┘
                  │        │       │
              ┌───▼───┐ ┌──▼──┐ ┌─▼──────┐
              │Catalog│ │Redis│ │Payment │  (external API)
              │  DB   │ │     │ │Gateway │
              └───────┘ └─────┘ └────────┘
```

### Tasks

**Task 1**: Define the steady state for this system (at least 5 metrics with sources and thresholds).

**Task 2**: Write 3 chaos experiment specifications following the format from this module. Each should target a different failure domain:
- Experiment A: Pod failure (pick a service)
- Experiment B: Network issue (latency or packet loss)
- Experiment C: Dependency failure (database or Redis)

**Task 3**: For each experiment, define:
- A precise hypothesis using the "We believe X even when Y because Z" format
- Blast radius assessment
- At least 3 abort conditions
- Rollback procedure

**Task 4**: Design a half-day Game Day schedule that runs all 3 experiments with proper debriefs.

### Success Criteria

Your Chaos Experiment Document is complete when:

- [ ] Steady state uses business metrics (not just infrastructure metrics)
- [ ] All 3 hypotheses are specific and falsifiable
- [ ] Blast radius starts small (staging, single pod/connection)
- [ ] Abort conditions are metric-based and automatable
- [ ] Rollback procedures are specific kubectl commands, not vague descriptions
- [ ] Game Day schedule includes roles, debriefs, and buffer time
- [ ] The document could be handed to another engineer who could execute the experiments without additional context

### Example Solution (Experiment A only)

```yaml
experiment:
  name: "Cart Service Pod Failure During Active Shopping"
  date: "2026-03-28"
  owner: "platform-sre"
  environment: staging

  hypothesis: >
    We believe that shopping cart operations (add, view, update)
    will continue with less than 500ms p99 latency even when
    1 of 3 Cart Service pods is killed, because Kubernetes
    will restart the pod within 30 seconds, the API Gateway
    has a 3-second retry with exponential backoff, and Redis
    holds the cart state independently of the Cart Service pods.

  steady_state:
    - metric: cart_operation_success_rate
      expected: ">= 99.5%"
      source: prometheus
    - metric: cart_p99_latency
      expected: "<= 200ms"
      source: prometheus
    - metric: active_shopping_sessions
      expected: "within 10% of pre-experiment count"
      source: redis
    - metric: cart_service_pod_count
      expected: "3 (before), 2 (during), 3 (after recovery)"
      source: kube-state-metrics
    - metric: redis_connected_clients
      expected: ">= 2 (matching healthy pod count)"
      source: redis-exporter

  injection:
    type: pod-kill
    target: cart-service
    namespace: staging
    replicas_before: 3
    pods_to_kill: 1
    method: chaos-mesh-podchaos

  abort_conditions:
    - "cart_operation_success_rate < 95% for 1 minute"
    - "cart_p99_latency > 2s for 30 seconds"
    - "active_shopping_sessions drop > 25%"

  blast_radius:
    scope: "staging environment only"
    services_affected: ["cart-service"]
    max_user_impact: "none (staging)"
    max_data_impact: "none (Redis holds state)"

  rollback: |
    kubectl rollout restart deployment/cart-service -n staging
    kubectl wait --for=condition=available deployment/cart-service -n staging --timeout=60s

  duration: "10 minutes"
```

Complete all 4 tasks to build your chaos experiment planning muscle. This document becomes your template for every future experiment.

---

## Summary

Chaos Engineering is a disciplined, scientific practice for discovering systemic weaknesses before they cause real outages. It follows the scientific method: define steady state, form a hypothesis, design a controlled experiment with safety measures, execute, observe, and learn.

Key takeaways:
- **It's engineering, not destruction** — hypotheses, controls, measurements
- **Start small** — staging, single pods, short durations
- **Safety first** — abort conditions, blast radius limits, team availability
- **Culture matters** — opt-in, blameless, documented, shared
- **Two modes** — Game Days for learning, continuous chaos for regression prevention

In the next module, you'll put these principles into practice with Chaos Mesh, the most popular chaos engineering tool for Kubernetes.

---

## Next Module

Continue to [Module 1.2: Chaos Mesh Fundamentals](module-1.2-chaos-mesh.md) — Install, configure, and run your first chaos experiments using Chaos Mesh on a real Kubernetes cluster.

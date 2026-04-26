---
title: "CNPA Practice Questions Set 1"
slug: k8s/cnpa/module-1.4-practice-questions-set-1
sidebar:
  order: 104
---

# CNPA Practice Questions Set 1

> **Complexity**: `[MEDIUM]`
>
> **Time to Complete**: 55-70 minutes
>
> **Prerequisites**: Platform engineering foundations, cloud native architecture basics, Kubernetes API objects, observability basics, and self-service delivery concepts
>
> **Track**: CNPA practice and applied review
>
> **Kubernetes Version Target**: 1.35+

## Learning Outcomes

By the end of this module, you will be able to **evaluate** whether a platform team is operating as a product team or merely acting as an infrastructure ticket queue, using evidence such as adoption, feedback loops, service ownership, and developer experience outcomes.

You will be able to **compare** golden paths, guardrails, and hard policy controls in real platform scenarios, then justify which mechanism fits a workflow without removing the autonomy that application teams need to deliver safely.

You will be able to **debug** weak platform metrics by separating activity metrics from outcome metrics, then recommend measures that show whether teams are actually getting faster, safer, or more independent.

You will be able to **analyze** observability and monitoring choices during an incident, deciding when predefined alerts are enough and when engineers need telemetry that supports new questions about an unknown failure.

You will be able to **design** a small self-service infrastructure interface using Kubernetes-style API thinking, including request contracts, reconciliation, ownership boundaries, and success criteria that a platform team could operate.

## Why This Module Matters

A payments company had a platform team with impressive activity reports. The team closed a large number of tickets, maintained dozens of dashboards, and published a long internal wiki. Yet when a product team needed a new environment for a partner integration, the request moved through a chain of approvals, private Slack messages, hand-edited YAML, and manual cloud-console changes. The deployment was technically successful, but the delivery process taught application teams a dangerous lesson: the platform existed, but it could not be trusted as the fastest safe path.

The failure was not a missing tool. The failure was a missing product mindset. A platform can have Kubernetes, Terraform, GitOps, observability dashboards, and an internal portal while still behaving like a help desk with better branding. CNPA-style questions often test this distinction because cloud native platform work is not only about knowing nouns such as “golden path” or “self-service.” It is about evaluating whether the system of teams, APIs, guardrails, and feedback loops produces better outcomes for developers and operators.

This practice set is therefore not a trivia drill. It is a guided review of the mental models behind common CNPA question patterns. You will examine scenarios where teams confuse control with enablement, dashboards with observability, ticket throughput with adoption, and documentation with a working contract. The quiz at the end asks you to apply those models under realistic ambiguity, because real platform decisions rarely announce which principle they are testing.

## Core Content

### 1. Start With The Product Question

A successful platform team begins with a product question: who is the user, what problem are they trying to solve, and how will the team know whether the platform made that problem easier? This sounds simple, but it changes almost every engineering decision. A ticket queue asks, “How quickly did we respond?” A product platform asks, “Did the user complete the workflow safely without needing us?” The first question rewards local busyness, while the second rewards repeatable leverage.

Platform-as-product does not mean the platform team becomes a marketing department or stops caring about infrastructure quality. It means the platform team treats internal developers as users with workflows, pain points, constraints, and alternatives. Developers can ignore a platform, work around it, or build shadow tooling when the official path is slower than the unofficial one. That makes adoption a practical signal, not a popularity contest.

```text
+------------------------+        +---------------------------+
| Infrastructure Queue   |        | Platform Product          |
+------------------------+        +---------------------------+
| Request arrives        |        | Workflow is studied       |
| Human triages ticket   |        | Common path is designed   |
| Specialist performs it |        | API or template exposes it|
| User waits for update  |        | User completes it safely  |
| Metric: tickets closed |        | Metric: outcomes improved |
+------------------------+        +---------------------------+
```

The diagram shows the same underlying technical capability presented through two operating models. In the queue model, the scarce resource is the specialist. In the product model, the specialist’s knowledge is encoded into paved workflows, reusable APIs, templates, policies, and feedback mechanisms. The platform team still handles exceptions, but exceptions become learning signals for improving the product rather than the default path.

A senior platform engineer looks for evidence before declaring success. If teams keep asking for the same environment through tickets, the platform has not yet turned that workflow into a product capability. If teams use the paved path only when forced, the path may be compliant but not valuable. If teams voluntarily adopt the path for routine work because it is faster and safer, the platform has created leverage.

> **Pause and predict:** Your organization reports that the platform team closed 300 infrastructure tickets last quarter, but only two product teams use the new deployment workflow without assistance. Would you call the platform adopted? Before reading on, write one sentence that separates team activity from user outcome.

The strongest answer is usually no: the platform team may be active, but the platform product has weak adoption. Ticket closure can still matter as an operational metric, especially when users are blocked, but it does not prove that the platform reduced friction. A better investigation asks which workflows still require tickets, which teams avoid the platform, what failure modes cause abandonment, and whether the platform team has a roadmap tied to user research.

### 2. Golden Paths Are Supported Routes, Not Cages

A golden path is a recommended, well-supported route for a common workflow. It packages decisions that many teams should not have to remake: how to build, deploy, observe, secure, and operate a standard service. The point is not to remove judgment from every team. The point is to make the safest common path the easiest path, while still leaving room for justified exceptions.

This distinction matters because organizations often misuse the language of golden paths to describe hard mandates. A hard mandate can be appropriate for non-negotiable security requirements, such as blocking privileged containers in a shared cluster. A golden path is different: it should be attractive because it reduces cognitive load and operational risk. If engineers experience it as a narrow cage, they will either resist it openly or route around it quietly.

| Mechanism | Primary Purpose | Good Use | Risk When Misused |
|---|---|---|---|
| Golden path | Make the common workflow easy and safe | Standard service deployment with logging, metrics, and rollback built in | Becomes stale ceremony if it ignores developer feedback |
| Guardrail | Prevent dangerous choices while preserving movement | Policy that rejects containers running as root in shared namespaces | Becomes confusing if errors do not explain how to fix the request |
| Hard control | Enforce a non-negotiable boundary | Blocking public object storage for regulated data | Becomes organizational drag if applied to every preference |
| Exception path | Handle legitimate uncommon needs | A latency-sensitive service needing a custom rollout strategy | Becomes shadow governance if exceptions are undocumented |

Golden paths work best when they are opinionated at the right layer. For example, a path might standardize build provenance, deployment health checks, service telemetry, and rollback behavior, while still letting teams choose framework-level details. The platform team should be clear about which parts are recommendations, which parts are guardrails, and which parts are mandatory controls. Ambiguity here creates frustration because users cannot tell whether they are making a design decision or violating a policy.

A useful golden path also has a maintenance loop. Application teams discover edge cases as workloads grow, regulatory demands change, and runtime behavior surprises everyone. If the platform team treats every edge case as user error, the path will decay. If it treats recurring exceptions as product feedback, the path becomes more durable.

> **What would happen if:** A platform team announces that every service must use its deployment template, but the template has no support for canary releases, batch jobs, or services with specialized traffic routing. Which teams will comply, which teams will work around it, and what signal should the platform team capture from that behavior?

The likely result is uneven adoption. Teams with simple services may comply because the template is adequate. Teams with specialized needs may fork the template or bypass it because the official route blocks legitimate work. The signal is not simply “developers are resisting standards.” The better signal is that the golden path does not yet cover enough common workflow variants, or that it lacks a clear exception mechanism.

### 3. Metrics Must Prove User Outcomes

Platform metrics are useful only when they connect platform work to user outcomes. A metric such as “number of dashboards created” may show effort, but it does not show whether teams can diagnose incidents faster. A metric such as “percentage of services using the standard deployment path for routine releases” is stronger because it reflects actual behavior by the target users. The best metrics combine adoption, reliability, speed, safety, and satisfaction so the platform team cannot optimize one dimension while damaging another.

The easiest trap is confusing activity metrics with outcome metrics. Activity metrics are not useless. They help manage work, plan capacity, and notice operational pressure. They become dangerous when leaders treat them as proof of platform success. A platform team can close many tickets because the platform is effective, but it can also close many tickets because the platform has failed to make common tasks self-service.

| Metric Type | Example | What It Can Tell You | What It Cannot Prove Alone |
|---|---|---|---|
| Activity | Tickets closed this month | How much manual work passed through the team | Whether users became more independent |
| Adoption | Teams using paved deployment path | Whether the platform is chosen for a workflow | Whether the path is producing safer delivery |
| Lead time | Time from repo creation to first production deploy | Whether the platform reduces delivery friction | Whether production quality is acceptable |
| Reliability | Failed rollouts by deployment path | Whether the path reduces operational risk | Whether developers find the path usable |
| Satisfaction | Developer survey with comments | Where friction is felt and why | Whether behavior changed in production |

Senior practitioners use metric pairs to avoid self-deception. If adoption rises but incident rates rise too, the platform may be easy but unsafe. If reliability improves but lead time gets worse, the platform may be safe but too slow. If satisfaction is high among a few teams but adoption is low overall, the platform may be valuable for early adopters but not discoverable or general enough for the organization.

A good platform scorecard is also workflow-specific. “Platform adoption” is too broad to guide action. Adoption of the service bootstrap path, adoption of the deployment path, adoption of the observability standard, and adoption of the database provisioning API may all tell different stories. When a CNPA-style question asks for the strongest sign of adoption, prefer evidence that target teams actually use the platform for a defined workflow.

### 4. Monitoring Checks Known Conditions, Observability Supports New Questions

Monitoring and observability overlap, but they are not identical. Monitoring checks predefined conditions: is the service available, is latency above the threshold, is error rate increasing, is the node running out of disk? Observability supports investigation when the failure mode is not fully known in advance. It gives engineers enough telemetry to ask new questions about system behavior without needing to ship new code for every question.

During a familiar failure, monitoring may be enough. If an alert says CPU is saturated because traffic doubled after a launch, a runbook may guide the response. During an unfamiliar failure, dashboards can become a wall of disconnected panels. Engineers need traces, logs, metrics, events, exemplars, and context that let them follow the request path and compare healthy behavior with failing behavior. Observability is less about having more graphs and more about preserving enough high-quality signals to reason under uncertainty.

```text
+-----------------------+          +-----------------------------+
| Monitoring Question   |          | Observability Question      |
+-----------------------+          +-----------------------------+
| Is latency too high?  |          | Which dependency changed?   |
| Did error rate rise?  |          | Why only one tenant fails?  |
| Is disk almost full?  |          | What path did request take? |
| Is pod restarting?    |          | What changed before restart?|
+-----------------------+          +-----------------------------+
```

The practical platform question is not “Should we have monitoring or observability?” A production platform needs both. Monitoring tells teams when known bad conditions occur. Observability helps teams understand the unknown conditions that were not encoded into an alert. The platform team’s job is to make the basic telemetry path easy enough that application teams do not have to reinvent it for every service.

> **Pause and predict:** A service has green uptime checks, but one customer reports that checkout fails only when a specific payment method is selected. Would you start by adding another uptime check, or by inspecting request-level telemetry? Explain which choice creates a new question rather than only checking a known condition.

Request-level telemetry is the better starting point because the failure is conditional and specific. An uptime check may still pass because most routes work. Useful telemetry would let the team filter by customer, payment method, route, dependency call, response code, deployment version, and time window. The platform’s golden path should make this kind of investigation routine, not heroic.

### 5. Self-Service Needs A Contract And A Reconciler

Self-service infrastructure is not the same as letting everyone click around in cloud consoles. Good self-service exposes a safe contract: users declare what they need, the platform validates the request, automation reconciles the desired state, and status tells the user what happened. Kubernetes makes this pattern familiar because users submit resources to an API and controllers continuously work to match actual state to desired state.

A contract can be a custom resource, a portal form backed by an API, a GitOps repository pattern, or a command-line workflow. The interface matters less than the operating model. The user should not need to know every cloud-provider detail, but they should understand the choices the platform exposes. The platform team should not manually translate every request, but it should own the automation, validation, policy, and operational behavior behind the contract.

```text
+------------------+       +------------------+       +-------------------+
| Developer Intent | ----> | Platform API     | ----> | Reconciler        |
+------------------+       +------------------+       +-------------------+
| "Need database"  |       | validates shape  |       | creates resources |
| size: small      |       | applies policy   |       | updates status    |
| env: staging     |       | records owner    |       | repairs drift     |
+------------------+       +------------------+       +-------------------+
```

This pattern is powerful because it separates user intent from implementation detail. A developer can request a staging database with a supported class of service. The platform can decide which cloud resources, network policies, secrets flow, backup settings, and labels are required. If the organization changes providers or improves the implementation, the contract can remain stable while the reconciler evolves.

Here is a simplified example of a request contract. The exact custom resource kind is illustrative, but the YAML is valid and shows the shape a platform might expose in a Kubernetes-native workflow.

```yaml
apiVersion: platform.example.com/v1alpha1
kind: DatabaseRequest
metadata:
  name: checkout-staging
  namespace: payments
spec:
  engine: postgres
  environment: staging
  size: small
  ownerTeam: payments-api
  backupPolicy: standard
```

A senior review of this contract would ask several questions. Are the exposed fields understandable to application teams? Are dangerous choices hidden or guarded by policy? Does status explain whether provisioning succeeded, failed validation, or is waiting on an external dependency? Is ownership recorded for cost, support, and incident routing? Does the contract encourage a standard path while still allowing exception handling for unusual workloads?

Self-service becomes fragile when the platform team exposes implementation details too early. If every developer must choose subnet routing, storage class internals, backup schedule syntax, and cloud IAM policy fragments, the interface is technically self-service but cognitively expensive. The platform has moved toil from the platform team to application teams instead of removing it.

### 6. Worked Example: Choosing The Best Platform Answer

Consider this scenario: a company introduces a new internal developer portal. It can create service repositories, attach deployment templates, provision staging namespaces, and register basic dashboards. After two months, platform leaders report success because the portal generated many repositories. However, most teams still ask the platform team to manually review deployment configuration before every production release. Incidents also show that teams often do not know which dashboard to use during rollbacks.

A weak analysis would say, “The portal exists, so the platform is self-service.” That answer mistakes a tool for an outcome. A stronger analysis separates each workflow. Repository creation may be self-service. Production readiness is not self-service if teams still need manual review for every release. Observability is not mature if dashboards exist but cannot guide action during rollback. The platform team should not declare success from portal-generated repository counts alone.

The best recommendation is to improve the golden path around production deployment and operational feedback. The platform team might encode deployment checks into CI, provide default rollback dashboards linked from each service, expose status in the portal, and measure how many routine releases reach production without manual platform intervention. It should also capture why teams request manual review: missing documentation, unclear errors, weak confidence in guardrails, or legitimate high-risk changes.

This example maps directly to common exam choices. Answers that emphasize “more tickets closed,” “more dashboards created,” or “the platform owns every incident” are usually weaker because they focus on platform activity or centralized ownership. Answers that emphasize supported workflows, developer adoption, measurable outcomes, safe self-service, and feedback loops usually align better with cloud native platform thinking.

### 7. Decision Checklist For Scenario Questions

CNPA practice questions often compress an organizational situation into a short paragraph. Your task is to identify which principle is being tested before evaluating the answer choices. Start by asking whether the scenario is about user adoption, workflow design, policy boundaries, telemetry during uncertainty, or self-service contracts. Once you identify the principle, eliminate answers that optimize the wrong layer.

Use this mental checklist when choices feel similar. If the scenario mentions developers waiting on humans for routine work, think self-service and paved paths. If it mentions many dashboards but weak incident diagnosis, think observability quality rather than dashboard count. If it mentions mandatory templates with growing exceptions, think golden path feedback and coverage. If it mentions ticket volume, commit counts, or meeting frequency, look for an outcome metric that better reflects user success.

```text
+-------------------------+
| Scenario Reading Flow   |
+-------------------------+
| 1. What workflow fails? |
| 2. Who is the user?     |
| 3. What is the outcome? |
| 4. Is it routine work?  |
| 5. Is there a contract? |
| 6. What metric proves it|
+-------------------------+
```

This checklist prevents a common testing mistake: matching keywords instead of reasoning through the system. A question containing the phrase “golden path” may still be testing whether the path is voluntary and useful. A question containing the word “observability” may be testing whether engineers can ask new questions, not whether logs are retained. A question about self-service may be testing the need for validation and status, not simply the existence of a portal.

## Did You Know?

1. **Internal platforms compete with informal alternatives.** Even when leadership mandates a tool, developers still compare it against scripts, direct cloud-console access, old templates, and help from experienced teammates, so voluntary adoption is a strong signal that the platform solves a real workflow problem.

2. **A golden path can include strict guardrails.** The path may feel smooth because mandatory controls are already built in, such as signed images, baseline telemetry, or default network policy, but the controls should be visible enough that teams understand what protection they are receiving.

3. **Self-service without status creates hidden tickets.** If users can submit a request but cannot see validation errors, provisioning progress, ownership, or failure reasons, they will fall back to chat messages and manual escalation even though an API technically exists.

4. **Observability is most valuable when the team did not predict the failure.** Dashboards and alerts are useful for known conditions, but high-cardinality telemetry, traces, structured logs, and deployment context become decisive when the incident does not match an existing runbook.

## Common Mistakes

| Mistake | Why It Fails | Better Practice |
|---|---|---|
| Treating ticket closure as the main platform success metric | It rewards platform team activity even when users remain dependent on manual help for routine workflows | Measure workflow completion, adoption, lead time, reliability, and user feedback together |
| Describing a golden path as the only legal way to deploy | It confuses a supported route with a hard control and often creates workarounds for legitimate exceptions | Make the common path easiest, document mandatory guardrails, and maintain a clear exception process |
| Building dashboards before defining incident questions | Teams may have many panels but still lack the context needed to diagnose unfamiliar failures | Start from operational questions, then design metrics, logs, traces, and links that support investigation |
| Exposing raw infrastructure settings as self-service | Users inherit provider complexity and make risky choices without enough context | Offer a smaller intent-based contract with validation, defaults, policy, and useful status |
| Measuring adoption at the whole-platform level only | A broad adoption number hides which workflows are working and which still require manual intervention | Track adoption by workflow, such as service creation, deployment, database provisioning, and telemetry onboarding |
| Assuming documentation alone creates self-service | Written instructions still require users to perform and interpret manual steps correctly | Encode common steps into APIs, templates, checks, and automated reconciliation wherever practical |
| Centralizing all production incident ownership in the platform team | It can slow diagnosis and separate service behavior from the teams that understand the application | Share responsibility through golden paths, service ownership, usable telemetry, and clear escalation boundaries |

## Quiz

### 1. Your company has a platform team that closes infrastructure tickets quickly, but product teams still wait several days for new service environments because every request needs manual review. Which recommendation best aligns with platform-as-product thinking?

1. Celebrate the ticket closure rate because it proves the platform team is responsive.
2. Replace the ticket workflow with a supported self-service contract for routine environments, then measure how many teams complete the workflow without manual intervention.
3. Require product teams to attend weekly infrastructure training before they can request environments.
4. Move all production ownership to the platform team so product teams no longer need to understand environments.

<details>
<summary>Answer</summary>

**Correct answer: 2**

The scenario shows a routine workflow that still depends on human mediation, so the platform has not converted expertise into a reusable product capability. A self-service contract with validation and status would reduce waiting while preserving safety. Ticket closure is an activity metric, training may help but does not remove workflow friction, and centralizing production ownership undermines shared service ownership.
</details>

### 2. A platform team calls its deployment template a golden path, but teams with batch jobs and canary-release needs keep forking it. What should the platform team evaluate first?

1. Whether the template covers enough common workflow variants and has a clear exception process.
2. Whether all forks can be blocked immediately by policy.
3. Whether the team can rename the template to make it sound more official.
4. Whether application teams should stop using Kubernetes for specialized workloads.

<details>
<summary>Answer</summary>

**Correct answer: 1**

Forking is a signal that the path may not support legitimate needs. The team should inspect whether the golden path is too narrow, stale, or missing documented exception handling. Blocking every fork may be appropriate for a specific safety control, but it does not address the product gap by itself.
</details>

### 3. During a review, leadership asks whether the platform is being adopted. Which evidence is strongest for a standard service deployment workflow?

1. The platform repository had many commits this month.
2. The platform team created additional dashboards for the deployment system.
3. Most service teams use the paved deployment path for routine releases and report fewer manual steps.
4. The platform team held several enablement meetings about deployment standards.

<details>
<summary>Answer</summary>

**Correct answer: 3**

Adoption is demonstrated by target users choosing or successfully using the platform for the intended workflow. Commits, dashboards, and meetings may support the work, but they are activity indicators. The strongest answer combines real usage with reduced friction.
</details>

### 4. A service has normal uptime checks, but one customer segment gets intermittent checkout failures after a dependency change. Which platform capability best supports the investigation?

1. A dashboard that only shows total service uptime.
2. Request-level telemetry that lets engineers filter by customer segment, route, dependency, version, and time window.
3. A monthly ticket report showing how many incidents were closed.
4. A policy requiring every service to have the same number of charts.

<details>
<summary>Answer</summary>

**Correct answer: 2**

The failure is conditional and not fully captured by a predefined uptime check. Observability should support new questions about request behavior, dependency calls, deployment versions, and affected segments. More charts do not automatically improve diagnosis if they cannot answer the relevant question.
</details>

### 5. Your platform exposes a portal form for database requests, but users frequently ask in chat whether provisioning succeeded or why a request failed. What is the most likely design gap?

1. The portal should be replaced with direct cloud-console access for every developer.
2. The request contract lacks clear status, validation feedback, or failure reasons.
3. The platform team should stop offering database self-service.
4. Developers are asking questions only because they dislike automation.

<details>
<summary>Answer</summary>

**Correct answer: 2**

Self-service requires more than a submission form. Users need status, validation errors, ownership information, and failure reasons so they can understand what happened without opening a hidden ticket. Direct console access would likely reduce safety and consistency.
</details>

### 6. A security team requires all containers in shared clusters to run as non-root. The platform team builds this into the standard deployment path and returns clear errors when a manifest violates the rule. How should you classify this design?

1. A useful guardrail embedded in the golden path.
2. A failure of platform thinking because golden paths can never enforce anything.
3. A monitoring feature because it checks a predefined condition.
4. A sign that application teams should own all cluster policy themselves.

<details>
<summary>Answer</summary>

**Correct answer: 1**

Golden paths can include guardrails, especially for non-negotiable safety requirements. The important design detail is that the rule is built into the workflow and provides clear feedback. This preserves movement while preventing a dangerous configuration.
</details>

### 7. A platform team wants to reduce cognitive load for developers creating new services. Which design best supports that goal while keeping teams accountable for their applications?

1. Give every team a blank repository and a long wiki page describing every infrastructure decision.
2. Provide a service template with build, deployment, telemetry, and ownership defaults, while allowing documented customization for justified needs.
3. Require the platform team to approve every application code change before deployment.
4. Hide all operational telemetry from product teams so they can focus only on features.

<details>
<summary>Answer</summary>

**Correct answer: 2**

A good platform removes repeated undifferentiated decisions while preserving application ownership. Defaults for build, deployment, telemetry, and ownership reduce setup load, while documented customization avoids turning the path into a cage. Manual approval and hidden telemetry both weaken team autonomy and learning.
</details>

### 8. Your team is choosing between two metrics for the first quarter of a deployment-platform rollout. Metric A counts how many templates the platform team published. Metric B measures the percentage of routine releases completed through the paved path without manual platform intervention, paired with rollback failure rate. Which metric is better and why?

1. Metric A, because publishing templates is the direct output of the platform team.
2. Metric A, because a larger template catalog always means higher developer productivity.
3. Metric B, because it connects adoption with safety for the target workflow.
4. Neither metric can be useful because platform work cannot be measured.

<details>
<summary>Answer</summary>

**Correct answer: 3**

Metric B is stronger because it measures whether users complete the intended workflow through the platform and whether that workflow remains safe. Pairing adoption with rollback failure rate avoids optimizing only for usage. Template count may show effort, but it does not prove user success.
</details>

## Hands-On Exercise

**Task**: Design and test a small self-service contract for a team namespace using Kubernetes labels and annotations. You will not build a full controller in this exercise. Instead, you will practice the platform-thinking loop: define a user-facing contract, apply it to a cluster, inspect whether the request shape is understandable, and decide which status or validation would be needed before this became a real platform capability.

Before you start, set a short alias so the commands are easier to read. In this module, `k` means `kubectl`; the alias only affects your current shell session and does not change Kubernetes behavior.

```bash
alias k=kubectl
k version --client
```

### Step 1: Create a namespace request shape

Create a file named `team-namespace.yaml` with a namespace that records the intended owner, environment, cost center, and support channel. This is a simplified stand-in for a richer platform API, but it is enough to practice the difference between raw infrastructure and a user-facing contract.

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: cnpa-practice-payments
  labels:
    platform.example.com/environment: staging
    platform.example.com/owner-team: payments-api
    platform.example.com/cost-center: shared-learning
  annotations:
    platform.example.com/support-channel: "#payments-platform"
    platform.example.com/requested-by: "cnpa-learner"
    platform.example.com/purpose: "Practice self-service contract review"
```

Apply the file to a Kubernetes 1.35+ cluster where you have permission to create namespaces. If you do not have a shared cluster, a local kind or minikube cluster is enough because the exercise focuses on API shape and inspection.

```bash
k apply -f team-namespace.yaml
k get namespace cnpa-practice-payments --show-labels
```

### Step 2: Inspect the contract as a platform reviewer

Now inspect the namespace and ask whether a developer could understand what they requested and whether an operator could route support, cost, and ownership questions. The output is intentionally ordinary Kubernetes metadata, but the reasoning is the important part.

```bash
k describe namespace cnpa-practice-payments
k get namespace cnpa-practice-payments -o yaml
```

Write a short review in your notes answering these questions. Which fields are user intent, and which fields are implementation detail? Which labels would be useful for cost allocation, policy selection, or incident routing? What feedback would a developer need if the owner team label were missing? What status would a real self-service API need beyond the fact that a namespace exists?

### Step 3: Simulate a weak request and compare

Create a second file named `weak-namespace.yaml` that technically creates a namespace but provides almost no platform contract. Apply it only in a local or disposable environment, because it represents the kind of vague request a real platform should validate or reject.

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: cnpa-practice-unknown
  labels:
    platform.example.com/environment: staging
```

Apply and inspect the weak request.

```bash
k apply -f weak-namespace.yaml
k describe namespace cnpa-practice-unknown
```

Compare the two namespaces as if you were reviewing a platform design. The weak request may be valid Kubernetes, but it is weak platform product design because ownership, support, purpose, and cost context are missing. This is the same distinction you should bring to CNPA scenario questions: a raw API object is not automatically a good self-service product.

### Step 4: Clean up

Delete the practice namespaces when you are finished.

```bash
k delete namespace cnpa-practice-payments
k delete namespace cnpa-practice-unknown
```

### Success Criteria

- [ ] You created and applied a namespace manifest that records owner team, environment, cost context, support channel, requester, and purpose.
- [ ] You inspected the created namespace with `k describe` and `k get -o yaml`, then identified which fields communicate user intent.
- [ ] You created a weaker namespace request and explained why technically valid infrastructure can still be a poor self-service contract.
- [ ] You wrote at least three validation or status requirements that a real platform API should provide before this workflow is production-ready.
- [ ] You cleaned up both practice namespaces and verified they no longer appear in `k get namespaces`.

## Next Module

Continue with [CNPA Practice Questions Set 2](./module-1.5-practice-questions-set-2/).

---
title: "AI for YAML, Manifests, and Config Review"
slug: ai/ai-for-kubernetes-platform-work/module-1.1-ai-for-yaml-manifests-config-review
sidebar:
  order: 1
---

> **AI for Kubernetes & Platform Work** | Complexity: `[MEDIUM]` | Time: 35-50 min

## Why This Module Matters

Kubernetes and platform work involves a constant stream of configuration:
- manifests
- Helm values
- Kustomize overlays
- policy files
- CI/CD definitions

AI can help you review that material faster.

It can:
- point out suspicious defaults
- explain unfamiliar fields
- compare two versions of a manifest
- help you notice missing probes, limits, labels, or security settings

But AI is dangerous when it is treated like an authority.

A model can confidently:
- invent fields
- misread API versions
- recommend defaults that do not fit your cluster
- suggest insecure or operationally weak changes

So the right pattern is not “AI writes my YAML.”

The right pattern is:

> AI helps me inspect, compare, question, and explain YAML that I still own.

## What You'll Learn

- what AI is good at during manifest review
- what it is bad at
- how to structure a safe manifest-review prompt
- how to verify model output before acting
- how to use AI as a reviewer instead of an untrusted generator

## Use AI For Review First, Generation Second

Many people start with:

> “Generate me a Deployment and Service.”

That is usually the wrong first move.

You learn more and make fewer mistakes when you start with:
- an existing manifest
- a small diff
- a narrow question
- a concrete review objective

Examples:
- “What is suspicious in this Deployment?”
- “Compare these two resource requests and explain the operational tradeoff.”
- “What is missing here for production readiness?”
- “Explain this NetworkPolicy in plain English.”

This keeps the model anchored to real material.
<!-- v4:generated type=thin model=gemini turn=1 -->

In practice, generation-first often leads to "configuration drift" between generic LLM assumptions and your specific cluster constraints, such as Admission Controllers (e.g., Kyverno or OPA Gatekeeper) or Pod Security Standards (PSS). Asking for a "standard" manifest might return code that uses deprecated `apiVersions` or omits critical `resources.limits` required by your local `LimitRange` policies. When you provide an existing manifest for review, you transition the AI from a creative assistant to a specialized auditor. This shift is vital for catching subtle operational anti-patterns—like a `RollingUpdate` strategy with a `maxUnavailable` value that is too high for your current node capacity—which would otherwise pass basic linting but fail during a real-world deployment.

Using the review-first approach allows you to perform "differential debugging" against your specific environment. Instead of asking "How do I secure this pod?", provide the manifest and ask for a threat model based on your known security posture. This forces the model to justify its recommendations with technical rationale rather than just spitting out a generic "best practice" template.

```yaml
# Audit this for Pod Security Standard 'Restricted' violations:
spec:
  containers:
  - name: nginx-ingress
    image: nginx:latest
    securityContext:
      allowPrivilegeEscalation: true
      runAsUser: 0
      capabilities:
        add: ["NET_ADMIN"]
```

The AI's value here isn't just identifying the `runAsUser: 0` violation, but explaining how `NET_ADMIN` capabilities combined with privilege escalation could allow a compromised container to manipulate host-level routing tables. This educational loop transforms a simple config check into a team-wide security upskilling exercise that builds deep internal expertise rather than shallow dependency on AI generation.

This matters operationally because it prevents the accumulation of "prompt-induced technical debt." Engineers who rely solely on generation often stop reading the YAML deeply, trusting the AI's output as long as the resource reaches a `Running` state. By using the AI as a peer reviewer, you maintain high "human-in-the-loop" (HITL) accountability. You are forced to engage with the code to provide it for review, and you must interpret the AI’s critique to implement the fix. This productive friction ensures the final configuration is something the platform team actually understands and can support at 3 AM when the abstraction layers inevitably leak and you need to debug the raw manifest.

<!-- /v4:generated -->
## A Safe Review Pattern

Use this order:

1. show the exact config
2. state the review goal
3. ask for risks, not only suggestions
4. require uncertainty to be stated explicitly
5. verify against docs or cluster reality

Example prompt:

```text
Review this Kubernetes Deployment for operational risks.

Focus on:
- readiness/liveness probes
- resource requests and limits
- security context
- rollout safety

Do not invent fields. If you are unsure, say so explicitly.
Return:
1. confirmed concerns
2. possible concerns requiring verification
3. questions I should answer before changing this manifest
```

That is much stronger than:

```text
Improve this YAML.
```

## What AI Is Actually Good At Here

AI is useful for:
- summarizing what a manifest does
- translating YAML into plain language
- spotting common omissions
- comparing two configs
- suggesting review questions
- helping juniors understand why a field matters

That makes it a strong review assistant.

## What AI Is Weak At Here

AI is weak at:
- cluster-specific truth
- admission controller behavior
- exact controller-version differences
- organizational policy rules
- nuanced production tradeoffs without context

It does not know:
- your SLOs
- your incident history
- your cluster limits
- your real traffic pattern

So even a plausible answer can be wrong for your environment.

## A Good Manifest Review Checklist

When AI reviews a manifest, make it answer questions like:
- what object is this and what controller owns it?
- what could fail at startup?
- what protects rollout safety?
- what resource assumptions does this make?
- what security exposure does this create?
- what information is still missing?

These questions create operator value.

## Example: Better Than “Looks Good”

Bad outcome:

> “This Deployment looks good.”

Useful outcome:

> “This Deployment has no readiness probe, so a rollout may route traffic to an unready pod. The container runs as root by default because no securityContext is set. Resource limits are present, but requests are omitted, which may harm scheduling predictability.”

That is actionable because it explains:
- the issue
- the risk
- why it matters

## Common Mistakes

- asking AI to generate production YAML from nothing
- accepting field names without checking docs
- confusing “possible concern” with “confirmed problem”
- using AI review without looking at the real diff
- skipping human judgment about rollout and security risk

## Quick Practice

Take one Deployment you already understand and ask AI to:
- explain it in plain English
- identify rollout risks
- identify security concerns
- list open questions instead of direct fixes

Then verify every point manually.

The goal is not speed alone.

The goal is learning where AI sharpens your review process and where it must be constrained.

## Summary

AI is useful for manifest review when:
- the input is real
- the question is narrow
- uncertainty is allowed
- verification still happens

Treat AI as a reviewer that helps you think more clearly.

Do not treat it as the source of truth.

<!-- v4:generated type=no_quiz model=codex turn=1 -->
## Quiz


**Q1.** Your team is preparing a production rollout for a `Deployment`, and an AI review says only, “This looks good.” You notice the manifest has no readiness probe. What is the operational risk, and why should you treat the AI response as insufficient?

<details>
<summary>Answer</summary>
The main risk is that traffic could be routed to pods that are not actually ready yet during rollout. A response like “looks good” is insufficient because it does not identify the issue, explain the risk, or tell you why it matters operationally. In this module, a useful AI review is specific and actionable, not vague reassurance.
</details>

**Q2.** A platform engineer asks an AI tool, “Generate me a Deployment and Service for production,” then plans to apply the output directly. Based on this module, what is the safer approach, and why?

<details>
<summary>Answer</summary>
The safer approach is review first, generation second. Start with a real existing manifest, a small diff, a narrow question, and a concrete review goal. That keeps the model anchored to actual configuration and reduces the chance of invented fields, bad defaults, or recommendations that do not match cluster constraints, policies, or operational needs.
</details>

**Q3.** Your team uses admission policies and strict platform defaults. An AI suggests a “standard” manifest that seems plausible, but you are not sure whether it fits your cluster. Which part of the module explains this risk, and what should you do next?

<details>
<summary>Answer</summary>
This falls under AI being weak at cluster-specific truth, admission controller behavior, controller-version differences, and organizational policy rules. The correct next step is to verify the suggestion against official docs and your actual cluster reality before acting. The model may sound confident while still being wrong for your environment.
</details>

**Q4.** During a config review, a junior engineer asks AI to “Improve this YAML.” The reply contains several recommendations, but no distinction between certain and uncertain claims. How should the prompt have been structured to make the review safer?

<details>
<summary>Answer</summary>
The prompt should include the exact config, a clear review goal, a request for risks instead of only suggestions, and an explicit instruction not to invent fields and to state uncertainty clearly. A stronger format is to ask for:
1. confirmed concerns
2. possible concerns requiring verification
3. questions to answer before changing the manifest

That structure reduces ambiguous advice and makes the output easier to validate safely.
</details>

**Q5.** Your team is comparing two versions of a manifest. One version has resource limits but no resource requests. What kind of review insight should you expect from AI if it is being used correctly?

<details>
<summary>Answer</summary>
A good AI review should explain that limits alone are not the full picture and that missing requests can harm scheduling predictability. The module emphasizes that strong reviews do more than point at a field; they explain the issue, the risk, and why it matters operationally.
</details>

**Q6.** A security review shows a container running as root with no meaningful `securityContext`, but the AI reviewer focuses only on formatting and naming consistency. What important review area did the AI miss, and how should you frame the next prompt?

<details>
<summary>Answer</summary>
It missed security exposure. The next prompt should explicitly ask the AI to review security context and risk, not just style or correctness. This module recommends giving a concrete review objective such as checking security context, rollout safety, probes, and resources so the model examines operator-relevant concerns instead of superficial details.
</details>

**Q7.** After an AI review, your teammate wants to treat every flagged item as a confirmed defect and immediately edit the manifest. What mistake does the module warn about, and what is the better practice?

<details>
<summary>Answer</summary>
The mistake is confusing a possible concern with a confirmed problem. The better practice is to separate confirmed concerns from items that require verification, then validate them against documentation or real cluster behavior before making changes. AI should be treated as a reviewer that helps you think more clearly, not as the source of truth.
</details>

<!-- /v4:generated -->
<!-- v4:generated type=no_exercise model=codex turn=1 -->
## Hands-On Exercise


Goal: use AI as a review assistant to inspect a Kubernetes `Deployment`, separate confirmed concerns from uncertain ones, and verify the final YAML with Kubernetes-native checks before accepting any change.

- [ ] Create a working manifest named `deployment.yaml` with a few realistic review targets such as a missing readiness probe, missing resource requests, and no explicit `securityContext`.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: config-review-demo
  labels:
    app: config-review-demo
spec:
  replicas: 2
  selector:
    matchLabels:
      app: config-review-demo
  template:
    metadata:
      labels:
        app: config-review-demo
    spec:
      containers:
        - name: web
          image: nginx:1.27
          ports:
            - containerPort: 80
          resources:
            limits:
              cpu: "500m"
              memory: "256Mi"
```

Verification commands:

```bash
kubectl apply --dry-run=client -f deployment.yaml
kubectl get -f deployment.yaml --dry-run=client -o yaml
```

- [ ] Read the manifest manually and write down three review goals before using AI: rollout safety, resource predictability, and runtime security.

Verification commands:

```bash
grep -nE 'readinessProbe|livenessProbe|resources|securityContext' deployment.yaml
kubectl explain deployment.spec.template.spec.containers
```

- [ ] Send the exact manifest to an AI assistant with a constrained review prompt that asks for confirmed concerns, possible concerns requiring verification, and open questions.

Example prompt:

```text
Review this Kubernetes Deployment for operational risks.

Focus on:
- readiness/liveness probes
- resource requests and limits
- security context
- rollout safety

Do not invent fields. If you are unsure, say so explicitly.
Return:
1. confirmed concerns
2. possible concerns requiring verification
3. questions I should answer before changing this manifest
```

Verification commands:

```bash
kubectl explain deployment.spec.strategy
kubectl explain deployment.spec.template.spec.containers.readinessProbe
kubectl explain deployment.spec.template.spec.containers.resources
kubectl explain deployment.spec.template.spec.containers.securityContext
```

- [ ] Compare the AI output to the manifest and sort each claim into one of two buckets: directly visible in YAML or requires external verification.

Verification commands:

```bash
grep -nE 'resources|limits|requests|securityContext|readinessProbe|livenessProbe' deployment.yaml
kubectl explain deployment.spec.template.spec.containers.livenessProbe
```

- [ ] Create a revised manifest named `deployment-reviewed.yaml` that adds a readiness probe, explicit resource requests, and a minimal non-root security context only if those changes are justified by your review.

Verification commands:

```bash
kubectl apply --dry-run=client -f deployment-reviewed.yaml
kubectl diff --server-side=false -f deployment.yaml -f deployment-reviewed.yaml
```

- [ ] Ask the AI a second, narrower question: explain the operational tradeoff of each change instead of suggesting more edits.

Example prompt:

```text
Explain the operational tradeoff of each change in this revised Deployment.
Do not suggest new fields.
If a tradeoff depends on cluster policy or workload behavior, say that explicitly.
```

Verification commands:

```bash
kubectl get -f deployment-reviewed.yaml --dry-run=client -o yaml
grep -nE 'readinessProbe|requests|securityContext|runAsNonRoot' deployment-reviewed.yaml
```

- [ ] Write a short review note with two sections: confirmed improvements and assumptions that still need cluster-specific validation.

Verification commands:

```bash
kubectl explain deployment.spec.template.spec.containers.securityContext.runAsNonRoot
kubectl explain deployment.spec.template.spec.containers.resources.requests
```

Success criteria:
- The final manifest passes `kubectl apply --dry-run=client`.
- AI feedback is split into confirmed concerns and items that require verification.
- The revised YAML includes only changes that were justified and checked.
- At least one verification command was used for probes, resources, and security settings.
- The exercise ends with a clear record of what is known from YAML and what still depends on cluster reality.

<!-- /v4:generated -->
## Next Module

Continue to [AI for Kubernetes Troubleshooting and Triage](./module-1.2-ai-for-kubernetes-troubleshooting-and-triage/).

## Sources

- [Liveness, Readiness, and Startup Probes](https://kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes/) — Explains how readiness probes affect whether traffic is sent to Pods during rollout and steady-state operation.
- [Configure a Security Context for a Pod or Container](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/) — Describes the Kubernetes securityContext fields used to set runtime user, group, and privilege-related controls.
- [Resource Management for Pods and Containers](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/) — Covers resource requests and limits, including how requests influence scheduling decisions.

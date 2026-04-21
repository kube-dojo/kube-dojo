---
title: "AI for Kubernetes Troubleshooting and Triage"
slug: ai/ai-for-kubernetes-platform-work/module-1.2-ai-for-kubernetes-troubleshooting-and-triage
sidebar:
  order: 2
---

> **AI for Kubernetes & Platform Work** | Complexity: `[MEDIUM]` | Time: 40-55 min

## Why This Module Matters

Troubleshooting is one of the highest-value places to use AI.

During triage, you are often trying to:
- compress unfamiliar signals quickly
- organize symptoms
- generate candidate causes
- decide what to check next

AI is useful here because it can help structure chaos.

But it is also dangerous here because it can produce:
- convincing but invented explanations
- generic advice that ignores the evidence
- noisy command lists with no prioritization

So the operator rule is:

> AI may help structure the investigation. It must not replace the evidence.

## What You'll Learn

- where AI helps during Kubernetes triage
- how to feed AI evidence instead of vague summaries
- how to separate symptoms, hypotheses, and next checks
- how to avoid cargo-cult troubleshooting
- how to use AI to improve investigation quality

## Start With Evidence, Not Anxiety

Bad input:

> “My cluster is broken. What should I do?”

Useful input:

> “A Deployment rollout is stuck. New pods remain Pending. Here are the pod events, node capacity details, and the relevant spec diff.”

AI performs far better when given:
- exact error messages
- event output
- logs
- manifest diffs
- timing and scope

Without evidence, it fills the gap with pattern-matching and guesswork.

### The "Hallucination of Certainty"
When you omit logs or events, you force the AI to rely on its training distribution. Because the internet is full of "how to fix Kubernetes" blogs that blame DNS or OOMKills, the AI will default to those explanations even if your specific issue is an `ImagePullBackOff` due to a credential typo. By withholding evidence, you aren't just making the AI less helpful—you are actively inviting it to mislead you with "confident" but irrelevant advice.

### Example: The Cost of Guessing
Consider a scenario where a pod is stuck in `Pending`.
- **Vague Prompt:** "My pod is Pending. Fix it."
- **AI Guess:** "You probably have a node problem. Try `kubectl drain` and restart your nodes."
- **The Reality:** The `kubectl describe` (which was not provided) shows `0/10 nodes are available: 10 insufficient cpu`. 

Running a node drain in this situation is a **destructive waste of time**. It solves nothing and adds churn to a cluster that is already at capacity. Practitioner-depth troubleshooting means knowing that the AI is effectively a *Bayesian inference machine*: it needs high-quality "priors" (your evidence) to produce a useful "posterior" (the hypothesis).

### Why This Matters for Platform Engineers
As a platform engineer, your value isn't just in fixing things; it's in the **speed and accuracy of the fix**. In an incident, the "Anxiety" lead-in usually results in a 20-minute cycle of trying random AI-generated commands that don't work. Starting with evidence reduces that loop to seconds by narrowing the search space from "the entire Kubernetes API" to "this specific resource bottleneck."

## A Strong Triage Structure

Use this shape:

1. what changed?
2. what is broken?
3. what is the scope?
4. what evidence do we already have?
5. what are the top 3 hypotheses?
6. what checks best separate them?

This turns AI into an investigation organizer rather than a random command generator.

### Why This Structure Works
Standard LLMs are pattern-matchers that default to the most frequent "fix" seen in their training data. By forcing the AI to explicitly state **what changed** and **what is broken** before suggesting a fix, you anchor the model in the current context. This "Chain of Thought" prompting—even when implicitly done through a structure—prevents the model from jumping to a generic `kubectl restart` when the actual problem is a recent `NetworkPolicy` change. It shifts the AI's role from "Support Agent" to "Expert Consultant" by prioritizing context over generic probability.

### The Power of Discriminating Checks
Point #6 is the most critical for a practitioner. A **Discriminating Check** is an action that, once performed, definitively rules out at least one major hypothesis. For example, if you suspect either a `ResourceQuota` exhaustion or a `NodeSelector` mismatch for a `Pending` pod, a discriminating check is `kubectl describe quota -n [namespace]`. If quotas are not reached, you have effectively halved your search space. AI is excellent at generating these "forks in the road" if you ask for them, preventing the common "command spam" anti-pattern where an operator runs 10 unrelated `get` commands without a strategy.

### Defining Scope to Prevent Over-Correction
Platform engineers often fall into the trap of treating a local pod failure as a global cluster issue. By explicitly defining the **scope** (e.g., "Only affecting the `prod` namespace," or "Only affecting nodes in `us-east-1a`"), you provide the AI with the *negative space* of the problem. If the AI knows that Service A is broken but Service B (which shares the same Node Group) is fine, it can automatically deprioritize "Node Failure" or "Kubelet Issue" as a hypothesis and focus on service-specific configurations like IAM roles or Secret mounts. This prevents the "blast radius" of your troubleshooting from exceeding the blast radius of the actual incident.

## Example Investigation Prompt

```text
Help me triage this Kubernetes rollout issue.

Facts:
- namespace: payments
- deployment: api
- old pods healthy
- new pods Pending
- problem began after image + resources change

Evidence:
- pod describe output:
  [paste]
- node allocatable summary:
  [paste]
- deployment diff:
  [paste]

Return:
1. symptoms
2. strongest hypotheses ranked by evidence
3. next 3 checks that would most reduce uncertainty
4. what not to assume yet
```

That is much safer than asking for “the fix.”

### Why "What Not to Assume" is the Secret Weapon
The most critical part of this prompt is point #4: **"What not to assume yet."** In high-pressure incidents, human operators often suffer from *anchoring bias*—the tendency to latch onto the first plausible explanation (e.g., "It's always a resource limit issue"). By explicitly asking the AI to list what remains unproven, you force a cognitive reset. For example, if pods are `Pending`, the AI might remind you: *"Do not assume this is a capacity issue yet; it could also be a `Taint` mismatch or a `PriorityClass` preemption."* This prevents you from wasting time on a "fix" that doesn't match the root cause.

### Leveling Up: Constraint-Driven Triage
For senior practitioners, the goal isn't just to get an answer, but to **bound the search space**. You can do this by adding environmental constraints and "negative evidence" to the prompt:

```text
[Context: Pods stuck in CrashLoopBackOff after ConfigMap update]

Constraints:
- We have already verified the ConfigMap syntax; it is valid YAML.
- This is NOT an OOMKill; memory usage is flat at 12MB.
- Do NOT suggest 'kubectl logs' as the binary crashes before it can write to stdout.

Specific Question:
Given that the binary is written in Go and we recently updated the 'securityContext', 
could this be a 'filesystem-read-only' error or a missing 'cap_net_bind_service' capability?
```

### Practitioner Commentary: Reducing MTTR via Noise Filtration
Why does this matter? During an outage, your Mean Time To Recovery (MTTR) is often gated by how quickly you can ignore irrelevant data. Standard LLMs, by default, will suggest every possible "common" fix. By providing constraints and asking for ranked hypotheses, you transform the AI from a "source of noise" into a **logic filter**. You are outsourcing the high-volume, low-value work of summarizing 1,000 lines of JSON events into a 3-point bulleted list, which preserves your mental "RAM" for making high-stakes decisions about production traffic.

## Use AI To Rank, Not To Conclude

A good investigation has levels:
- symptom
- plausible cause
- tested cause
- confirmed cause

AI should help mostly in the middle:
- forming plausible hypotheses
- ranking them
- proposing discriminating checks

It should not leap from symptom to certainty.

If the model says:

> “This is definitely a DNS issue.”

without direct evidence, that is a process failure.

### Combatting Probabilistic Tunnel Vision
The fundamental risk here is that LLMs are built on token probability, not causal logic. Because "DNS issue" or "OOMKill" appears more frequently in their training corpus than "stale CNI plugin cache on a specific worker node," the model will naturally gravitate toward the former. This creates a **Probabilistic Fallacy**: the AI suggests what is *common* globally rather than what is *likely* in your specific cluster context. As a practitioner, your job is to use AI to generate the full "long tail" of possibilities that you might have forgotten, while remaining the final arbiter of which one fits the current evidence.

### Evidence-Weighted Ranking
To go deeper, ask the AI to provide an **Evidence-Weighted Ranking**. Instead of a simple list, prompt the model to categorize hypotheses by *Confidence* (based on provided logs) vs. *Ease of Verification* (how quickly a human can check it). A high-confidence/low-effort check—like verifying a `ServiceAccount` name in a manifest—should always be prioritized over a high-confidence/high-effort check like a full `tcpdump` analysis. This approach transforms the AI from a search engine into a strategic advisor that respects your MTTR (Mean Time To Recovery) constraints.

### The Power of Negative Evidence
Deep-dive troubleshooting is often about what *isn't* happening. A powerful technique is feeding the AI "Negative Evidence"—a list of things that are working correctly. If you tell the AI that `Service A` can reach the Database but `Service B` (on the same node) cannot, you are providing a logic gate that forces the model to prune entire branches of its hypothesis tree, such as "Node Network Failure" or "VPC Peering Issues." This forces the AI to move past generic pattern matching and into the specific "differential diagnosis" required for complex platform failures.

## Good Uses During Triage

AI is strong at:
- summarizing long logs
- translating `kubectl describe` output into plain language
- spotting patterns in repeated event messages
- organizing a troubleshooting timeline
- proposing what evidence is still missing

It is weak at:
- knowing your cluster state beyond what you provide
- recognizing environment-specific quirks
- choosing between lookalike causes without enough evidence

### Why This Matters: Scaling the "Expert Intuition"
In complex distributed systems, "expert intuition" is often just high-speed pattern matching across multiple layers (networking, storage, compute). AI democratizes this by providing a baseline level of "seniority" to junior on-call engineers. For example, a junior engineer might see a `DeadlineExceeded` error in a log and think "the network is slow." A more experienced practitioner (or an AI fed with the right context) might notice that the error only occurs during a specific CronJob window, suggesting a resource contention issue rather than a transit problem. By using AI to **synthesize cross-resource state**, you turn a 30-minute investigation into a 2-minute "sanity check."

### Concrete Example: The "Silent" Configuration Drift
Consider a scenario where a rollout is successful, but traffic is intermittently dropping.
- **Human Observation:** "Everything looks green, but some requests fail with 502."
- **AI Synthesis:** "I noticed that the new `Deployment` spec increased the `replicaCount`, but the `Service` still uses a `sessionAffinity` of `ClientIP`. Since you didn't update the `loadBalancer` backend timeout, your newer pods may be dropping connections during high-concurrency peaks."
This isn't just "summarizing logs"—it is **context-aware reasoning** that identifies how a change in one resource (Deployment) creates a bottleneck in another (Service/LB) due to a configuration mismatch.

### Practitioner Commentary: Moving from "What?" to "Where?"
During the "Golden Hour" of an incident, the bottleneck is rarely "what" is happening—the logs usually tell you that. The bottleneck is **where** to look next. AI excels at generating a "Short List" of investigation paths. Instead of checking every layer of the OSI model, you can ask: *"Given these specific 503 errors and this healthy CNI status, give me the top 3 most likely misconfigurations in our Istio VirtualService."* This allows you to skip the noise and focus your manual verification on the highest-probability causes.

## A Better Human-AI Division Of Labor

Human owns:
- evidence collection
- prioritization
- production judgment
- final decision

AI helps with:
- summarization
- candidate causes
- investigation structure
- clarifying what to test next

That is the right split.

## Anti-Pattern: Command Spam

Weak AI troubleshooting often looks like:
- 20 commands
- no explanation
- no ranking
- no connection to the specific failure

That feels busy, but it is low-value.

A better answer gives:
- the likely branches of investigation
- the minimum next checks
- the reason each check matters

## Mini Drill

Take a real or historical failure and separate:
- what was observed
- what was guessed
- what was verified

Then ask AI to propose the next 3 checks from only the observed evidence.

Compare that to what actually resolved the incident.

This teaches whether the model is helping you think or only producing noise.

## Summary

AI is useful in Kubernetes troubleshooting when it helps you:
- structure evidence
- rank hypotheses
- reduce uncertainty

It becomes harmful when it:
- invents certainty
- floods you with generic commands
- pulls attention away from actual evidence

<!-- v4:generated type=no_quiz model=codex turn=1 -->
## Quiz

**Q1.** Your team says, "The cluster is broken," after a payment service rollout stalls. You have access to pod events, a `kubectl describe` output, node allocatable capacity, and a deployment diff showing an image and resource change. What is the best way to ask AI for help so it improves the investigation instead of guessing?

<details>
<summary>Answer</summary>
Provide a structured, evidence-first prompt that includes the exact facts, pasted evidence, and a narrow request such as symptoms, ranked hypotheses, the next 3 checks, and what not to assume yet.

This follows the module's guidance to start with evidence, not anxiety. AI performs better when given concrete signals like events, logs, and diffs, and it is safer when asked to organize the investigation rather than jump straight to "the fix."
</details>

**Q2.** A new set of pods is stuck in `Pending` after a rollout, while the old pods are still healthy. An AI assistant immediately says, "This is definitely a DNS issue." How should you treat that response?

<details>
<summary>Answer</summary>
You should treat it as a process failure unless the evidence directly supports DNS as the cause.

The module says AI should help form and rank plausible hypotheses, not leap from symptom to certainty. "New pods Pending" is only a symptom. Without direct evidence, a definite conclusion is unreliable and can pull the investigation away from the real cause.
</details>

**Q3.** During an incident, an AI tool returns 20 Kubernetes commands with no ranking, no reasoning, and no link to the current failure. Your teammate wants to run them all to save time. Based on the module, what is the better approach?

<details>
<summary>Answer</summary>
Reject the command spam and instead ask for the likely investigation branches, the minimum next checks, and why each check matters.

The module calls this anti-pattern "command spam." A high-value AI response should reduce uncertainty with a few discriminating checks tied to the actual evidence, not produce a long generic command list that feels busy but does not improve triage quality.
</details>

**Q4.** Your platform team is reviewing an outage after a recent config change. You want AI to help, but you also want to avoid letting it replace operator judgment. Which responsibilities should stay with the human, and which can be delegated to AI?

<details>
<summary>Answer</summary>
The human should keep ownership of evidence collection, prioritization, production judgment, and the final decision. AI can help with summarization, generating candidate causes, structuring the investigation, and clarifying what to test next.

This matches the module's recommended human-AI split. AI is useful for organizing and compressing information, but it should not replace evidence-based decision-making in production troubleshooting.
</details>

**Q5.** An engineer asks AI to "fix the rollout" after a deployment change. Another engineer suggests asking AI to separate symptoms, ranked hypotheses, and the next checks that would best distinguish them. Which approach is safer and why?

<details>
<summary>Answer</summary>
The second approach is safer because it keeps AI in the role of investigation organizer rather than letting it pretend to know the fix before the cause is verified.

The module emphasizes using AI to rank, not conclude. A good investigation moves from symptom to plausible cause to tested cause to confirmed cause. Asking for ranked hypotheses and discriminating checks supports that process; asking for "the fix" encourages unsupported certainty.
</details>

**Q6.** After a historical Kubernetes incident, your team wants to learn whether AI would have improved the response. What exercise from the module would best test that?

<details>
<summary>Answer</summary>
Separate the incident into what was observed, what was guessed, and what was verified, then ask AI to propose the next 3 checks using only the observed evidence. Compare that to what actually resolved the incident.

The module's mini drill is designed to show whether the model is helping you think more clearly or just producing noise. It tests AI against an evidence-first workflow instead of rewarding confident-sounding guesses.
</details>

**Q7.** You are troubleshooting a network issue and provide the AI with "Negative Evidence" (e.g., "Service A on the same node works fine"). Why is this technically superior to just providing the error logs?

<details>
<summary>Answer</summary>
Providing negative evidence helps combat **Probabilistic Tunnel Vision**. By telling the AI what is *working*, you provide a logic gate that forces the model to prune irrelevant but "common" branches of its hypothesis tree (like node-level failures). This moves the AI's reasoning beyond simple pattern matching and into a more precise "differential diagnosis" that respects the specific topology of your cluster.
</details>

<!-- /v4:generated -->
## Next Module

Continue to [AI for Platform and SRE Workflows](./module-1.3-ai-for-platform-and-sre-workflows/).

## Sources

- [Monitoring, Logging, and Debugging](https://kubernetes.io/docs/tasks/debug/) — Official Kubernetes guidance on collecting evidence and debugging workloads or clusters.
- [Troubleshooting Applications](https://kubernetes.io/docs/tasks/debug/debug-application/) — Covers practical Kubernetes troubleshooting workflows that support an evidence-first triage process.
- [kubectl debug Reference](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_debug/) — Reference for `kubectl debug`, useful as follow-on reading for hands-on debugging after triage.

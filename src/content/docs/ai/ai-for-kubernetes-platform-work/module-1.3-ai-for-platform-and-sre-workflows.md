---
title: "AI for Platform and SRE Workflows"
slug: ai/ai-for-kubernetes-platform-work/module-1.3-ai-for-platform-and-sre-workflows
sidebar:
  order: 3
---

> **AI for Kubernetes & Platform Work** | Complexity: `[MEDIUM]` | Time: 40-55 min

## Why This Module Matters

Platform and SRE work is full of repetitive thinking tasks:
- reading alerts
- drafting runbooks
- comparing incidents
- reviewing change plans
- summarizing postmortems
- checking whether a proposed workflow is missing guardrails

AI can create leverage here because much of the work is:
- text-heavy
- pattern-heavy
- explanation-heavy

But these workflows are high-stakes.

You cannot let AI quietly become:
- the incident commander
- the change approver
- the policy owner

The right question is not:

> “Can AI do SRE work?”

It is:

> “Which parts of SRE and platform work benefit from AI assistance without losing accountability?”

## What You'll Learn

- where AI adds value in platform and SRE workflows
- where it should stay advisory only
- how to use AI in runbooks, postmortems, and alert analysis
- how to preserve ownership and review discipline
- how to avoid shallow automation theater

## Good Workflow Targets

AI works well for:
- summarizing repetitive alert context
- drafting first-pass incident notes
- comparing similar historical incidents
- improving runbook readability
- extracting action items from long discussions
- reviewing whether a platform workflow is missing a step

These are support functions.

They help humans move faster without giving AI control over the system.

## Weak Workflow Targets

AI should not be trusted to independently:
- approve production changes
- decide severity during ambiguous incidents
- choose rollback vs forward-fix on its own
- rewrite policy with no human review
- act on infrastructure directly in high-risk paths

These require human accountability because the cost of a wrong answer is too high.

## A Good SRE Pattern

Use AI in three stages:

### 1. Before the work

Ask AI to:
- clarify the goal
- surface missing assumptions
- suggest a checklist

### 2. During the work

Ask AI to:
- summarize incoming evidence
- compare current symptoms to known patterns
- draft structured notes

### 3. After the work

Ask AI to:
- turn raw notes into a postmortem draft
- extract action items
- identify unclear steps in the runbook

This keeps AI in a support role throughout the lifecycle.

## Example: Runbook Improvement

Bad use:

> “Write me a runbook for database latency.”

Better use:

> “Review this existing runbook for ambiguity, hidden assumptions, and missing verification steps. Do not rewrite the operational decisions. Point out where a junior responder could misread the sequence.”

That protects the actual operational judgment while still using AI to improve clarity.

## Example: Incident Notes

Useful prompt:

```text
Convert these raw incident notes into:
1. timeline
2. observed symptoms
3. actions taken
4. open questions
5. possible follow-up items

Do not infer unverified root cause.
Mark unknowns clearly.
```

That gives you structure without false certainty.

## The Accountability Rule

In platform and SRE work:
- AI can draft
- AI can summarize
- AI can compare
- AI can question

But humans must still:
- decide
- approve
- execute
- accept risk

If that line gets blurry, you are no longer using AI as an accelerator.

You are quietly outsourcing judgment.

## Common Mistakes

- treating AI-written runbooks as validated runbooks
- letting AI summarize away important uncertainty
- asking for action plans before gathering evidence
- using AI to create policies with no operational reviewer
- assuming good writing equals good operational reasoning

## Summary

AI is valuable in platform and SRE workflows when it improves:
- clarity
- structure
- speed of understanding
- documentation quality

It becomes dangerous when it starts to replace:
- operational ownership
- risk judgment
- final approval

## Next Module

Continue to [Trust Boundaries for Infrastructure AI Use](./module-1.4-trust-boundaries-for-infrastructure-ai-use/).

## Sources

- [Logging Architecture](https://kubernetes.io/docs/concepts/cluster-administration/logging/) — Grounds alert analysis and incident-note workflows in the upstream Kubernetes logging model.
- [Debug a Cluster](https://kubernetes.io/docs/tasks/debug/debug-cluster/) — Provides authoritative Kubernetes debugging practices that pair well with AI-assisted summarization and checklist drafting.
- [NIST AI Risk Management Framework](https://nist.gov/itl/ai-risk-management-framework) — Supports the module's accountability theme by framing human oversight, governance, and risk controls for AI-assisted work.

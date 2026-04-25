---
title: "Evaluation, Iteration, and Shipping v1"
slug: ai/ai-building/module-1.4-evaluation-iteration-and-shipping-v1
sidebar:
  order: 4
---

> **AI Building** | Complexity: `[MEDIUM]` | Time: 40-55 min

## Why This Module Matters

Many first AI projects fail because the builder keeps changing prompts without ever deciding what “good enough” means.

That creates a trap:
- the system seems to improve in demos
- but nobody can tell whether it is actually reliable

This module exists to prevent that trap.

## What You'll Learn

- why evaluation matters before optimization
- how to define a useful v1 target
- how to iterate without guessing blindly
- how to ship a small AI feature without pretending it is finished

## Start With The Smallest Honest Question

Before tuning the system, ask:

> What job must this feature do well enough to be useful?

Not:
- “How do I make it amazing?”
- “How do I make it fully autonomous?”

V1 needs a narrow success condition.

Examples:
- summarize internal notes accurately enough that a human can edit them quickly
- classify support tickets well enough to speed up triage
- answer document questions with grounded excerpts

## Evaluation Does Not Need To Be Fancy

For a beginner-friendly first system, evaluation can be simple:
- 10-20 representative examples
- expected output shape
- pass/fail criteria
- notes on failure patterns

The point is not statistical perfection.

The point is to stop relying on cherry-picked impressions.

## A Practical v1 Loop

```text
pick one task
   ->
collect representative examples
   ->
define what success looks like
   ->
run the system
   ->
inspect failures
   ->
change one thing at a time
```

That “one thing at a time” rule matters.

If you change prompt, model, context, and output format together, you learn almost nothing.

## What To Change First

Good order of operations:

1. clarify the task
2. improve context
3. improve output shape
4. add validation
5. only then change model or more advanced settings

This is more effective than immediately reaching for a bigger model.

## What Shipping v1 Really Means

A good v1 is:
- useful
- bounded
- explainable
- reviewable

A bad v1 is:
- open-ended
- hard to evaluate
- trusted too much
- much harder to debug

## Signs You Are Ready To Ship

- the use case is narrow
- failure modes are visible
- humans can review outcomes where needed
- you have examples that show typical success and typical failure
- the system reduces work instead of adding ambiguity

## Signs You Are Not Ready

- you still cannot describe success in one sentence
- every demo depends on a carefully phrased prompt
- wrong outputs look too plausible to detect
- nobody owns validation
- the system performs actions you cannot comfortably audit

## Active Check

If a feature gets good results on 3 hand-picked examples but bad results on normal messy inputs, is it ready?

No.

That is exactly why representative evaluation matters.

## Common Mistakes

| Mistake | Why It Hurts | Better Move |
|---|---|---|
| tuning without examples | progress is imaginary | define a small evaluation set first |
| changing too many things at once | no causal learning | change one variable per iteration |
| shipping broad autonomy first | hard to control | ship bounded usefulness first |
| treating demos as evidence | selection bias | test on representative cases |

## Quick Quiz

1. **Why is “collect representative examples” more valuable than endlessly tweaking prompts from memory?**
   <details>
   <summary>Answer</summary>
   Because representative examples expose real failure patterns. Prompt tweaking without a test set usually optimizes for vibes, not actual reliability.
   </details>

2. **What makes a good v1 for an AI feature?**
   <details>
   <summary>Answer</summary>
   Narrow scope, visible failure modes, reviewable outputs, and clear usefulness without pretending the system is smarter or safer than it is.
   </details>

3. **What should you usually improve before switching to a stronger model?**
   <details>
   <summary>Answer</summary>
   Clarify the task, improve context, improve output structure, and add validation first.
   </details>

## Hands-On Exercise

Choose one candidate AI feature and write:

1. the exact user job
2. 5 example inputs
3. what “good enough” means
4. one review step
5. one likely failure mode

If you cannot do those five things clearly, the feature is not ready for v1.

## Next Module

From here, continue to:
- [AI/ML Engineering: AI-Native Development](../../ai-ml-engineering/ai-native-development/)
- or [AI/ML Engineering: Generative AI](../../ai-ml-engineering/generative-ai/)

## Sources

- [OpenAI Evals](https://github.com/openai/evals) — Concrete examples and tooling for building repeatable eval sets and comparing changes over time.
- [NIST AI RMF Playbook](https://www.nist.gov/itl/ai-risk-management-framework/nist-ai-rmf-playbook) — Useful for turning evaluation and review steps into an explicit shipping and governance practice.
- [OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/) — Relevant when moving from prompt iteration to shipping, because it highlights common security and reliability risks in LLM features.

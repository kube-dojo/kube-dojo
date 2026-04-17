---
title: "Prompting Basics"
slug: ai/foundations/module-1.3-prompting-basics
sidebar:
  order: 3
---

> **AI Foundations** | Complexity: `[QUICK]` | Time: 30-40 min

## Why This Module Matters

Prompting is not magic. It is task framing.

Most bad AI output starts with vague goals, missing constraints, or weak context. Better prompting does not guarantee truth, but it makes the interaction far more useful.

## What You'll Learn

- how to ask for the right kind of output
- how to add context, constraints, and format
- how to iterate instead of expecting one-shot perfection
- when prompting is the wrong fix for a bad workflow
- how to recognize the difference between clarity and prompt superstition

## The Core Idea

A prompt is not a spell.

It is the way you define:
- the task
- the context
- the boundaries
- the output you want

Bad prompts often fail because the task itself is underspecified, not because the model lacks some secret trick.

## A Strong Prompt Usually Includes

- **goal**: what you want
- **context**: what the model needs to know
- **constraints**: limits, tone, format, boundaries
- **evaluation standard**: what counts as good

## Weak Prompt vs Better Prompt

Weak:

```text
Explain Kubernetes.
```

Better:

```text
Explain Kubernetes to a beginner who knows Linux and Docker but has never used a cluster.
Use plain language, one analogy, and a short list of the core objects to learn first.
```

Why the second one is better:
- the audience is clear
- the expected level is clear
- the answer shape is constrained
- the model is less likely to drift into advanced material

## Better Prompting Habits

- ask for a specific output shape
- tell the model what assumptions to avoid
- request uncertainty when the answer is unclear
- prefer short iterative loops over giant kitchen-sink prompts

## A Simple Prompt Framework

Use this mental structure:

```text
Task
Context
Constraints
Output format
```

Example:

```text
Task: Compare Docker and Kubernetes.
Context: Audience is a junior engineer with Linux basics.
Constraints: Keep it under 300 words. Avoid jargon where possible.
Output format: short explanation + 3-bullet comparison table.
```

## Iteration Beats Giant Prompts

Many learners assume the model should give the perfect answer in one try.

That usually creates bloated prompts and messy results.

A better workflow is:
1. ask for a first draft
2. inspect what is missing
3. refine with a narrow follow-up
4. verify the final result

This is faster and more reliable than trying to write one enormous “perfect” prompt.

## When Prompting Is Not The Real Problem

Sometimes the prompt is not the bottleneck.

The real problem may be:
- missing source material
- weak verification
- the wrong tool
- unclear ownership
- a workflow that should not be automated at all

This matters because people often blame prompting for failures that are really process failures.

## Common Mistakes

- asking broad questions with no audience or format
- trying to solve trust problems with prompt wording alone
- overfitting to “prompt tricks” instead of clarity
- treating iterative refinement as failure instead of normal use

## Summary

Good prompting is disciplined communication.

You usually get better results when you are explicit about:
- who the answer is for
- what the answer should do
- what the answer should avoid
- how the answer should be structured

Prompting improves output quality.
It does not replace verification.

## Next Module

Continue to [How to Verify AI Output](./module-1.4-how-to-verify-ai-output/).

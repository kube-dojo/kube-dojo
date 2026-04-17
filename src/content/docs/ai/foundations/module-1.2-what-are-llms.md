---
title: "What Are LLMs?"
slug: ai/foundations/module-1.2-what-are-llms
sidebar:
  order: 2
---

> **AI Foundations** | Complexity: `[QUICK]` | Time: 30-40 min

## Why This Module Matters

Many modern AI tools are powered by large language models, but people often use them without understanding what they actually do.

That creates two bad outcomes:
- unrealistic trust
- unrealistic fear

## What You'll Learn

- what an LLM is in practical terms
- what tokens, context, and next-token prediction mean
- why LLMs sound confident even when they are wrong
- what LLMs are good at and where they are weak
- how to use a realistic mental model instead of magical thinking

## Start With The Simplest Honest Model

An LLM is a model trained on large amounts of text to predict the next most likely token in a sequence.

That sounds simple, but when done at scale it creates useful behaviors:
- summarization
- explanation
- rewriting
- code completion
- question answering
- structured output generation

But prediction is not the same as understanding.

## Tokens, Context, and Prediction

### Tokens

Models do not read text exactly like humans do. They work with tokens:
- pieces of words
- whole words
- punctuation
- formatting symbols

This matters because limits like context windows are measured in tokens, not in pages or paragraphs.

### Context

The context is the text currently available to the model:
- your prompt
- prior messages
- attached material
- tool output or retrieved information

If crucial information is missing from context, the model cannot reliably use it.

### Next-token prediction

The core mechanism is still prediction:

```text
given the text so far, what token is most likely to come next?
```

At scale, this creates outputs that can feel conversational, explanatory, and even strategic.

That is why LLMs are useful.
It is also why they can be wrong in polished language.

## Practical Mental Model

Think of an LLM as:
- a very strong pattern-completion engine
- a language interface over learned statistical structure
- useful, but not automatically truthful

This is a better mental model than:
- “it thinks like a person”
- “it is just autocomplete”

Both of those are too shallow.

## What LLMs Usually Do Well

- drafting and rewriting
- summarizing large inputs
- explaining concepts at different levels
- translating between formats
- helping you explore solution space quickly

These strengths come from pattern fluency, broad language exposure, and flexible response generation.

## Where They Commonly Fail

- factual certainty without evidence
- weak source discipline
- silent fabrication
- poor handling of vague goals
- over-helpful but wrong answers

These failures are not weird edge cases. They are normal outcomes of systems optimized to produce plausible language.

## Why LLMs Sound More Reliable Than They Are

LLMs are often rewarded for:
- coherence
- completeness
- confidence of tone
- conversational smoothness

That makes them pleasant to use.
It does not make them equivalent to verified sources or domain experts.

This is why “it sounded right” is never a good enough validation method.

## Good Questions To Ask When Using An LLM

- is this a drafting task or a truth task?
- what information is actually in context?
- should I expect reasoning, retrieval, or both?
- what part of this answer needs verification?

## Quick Example

If you ask:

```text
Explain Kubernetes to me.
```

you may get a fluent answer.

If you ask:

```text
Explain Kubernetes to a beginner who knows Linux and Docker.
Use one analogy, list the first five objects to learn, and separate what is essential from what is advanced.
```

you are giving the model a clearer task and a better context shape.

The output will usually improve, but it still must be checked if accuracy matters.

## Common Mistakes

- assuming confident wording means correctness
- treating LLMs like search engines
- forgetting that context quality shapes output quality
- assuming a bigger model removes the need to verify

## Summary

LLMs are language models that generate output token by token based on learned patterns and current context.

They are powerful because language is a useful interface to many tasks.

They are risky because plausibility and correctness are not the same thing.

## Next Module

Continue to [Prompting Basics](./module-1.3-prompting-basics/).

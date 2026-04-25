---
title: "Evaluation, Iteration, and Shipping v1"
slug: ai/ai-building/module-1.4-evaluation-iteration-and-shipping-v1
sidebar:
  order: 4
---

> **AI Building** | Complexity: `[MEDIUM]` | Time: 40-55 min

## Learning Outcomes

By the end of this module, you will be able to:

- **Design** a minimal evaluation set that distinguishes real improvement from lucky prompt tweaks
- **Diagnose** why an AI feature is failing by isolating one variable at a time and reading failure patterns
- **Apply** the correct order of iteration interventions before reaching for a larger model
- **Evaluate** whether a v1 feature is ready to ship based on observable evidence, not demo performance
- **Construct** a bounded v1 success definition that a teammate can verify independently

## Why This Module Matters

In 2023, a mid-sized SaaS company shipped an internal tool to classify inbound support tickets by urgency. The product manager demoed it to leadership using five carefully chosen examples. All five were classified correctly. The tool went live.

Three weeks later, the support team was getting paged at midnight. The system was routing time-sensitive delivery failures to a low-priority queue and marking routine billing questions as critical. The product manager could not explain why — because the team had never defined what "urgent" meant in the system prompt. They had tuned the prompt until the five demo examples looked right, then shipped. Nobody had tested it on the messy, ambiguous messages that real customers actually send.

This is not a rare story. It is the default outcome when builders skip evaluation. The discipline that prevents that midnight page is the subject of this module.

## The Evaluation Gap

Most builders skip evaluation for a reason that feels rational in the moment: it seems like extra work when you are already looking at promising results. You ran it on a few examples, it looked good, you want to ship.

That intuition is backward.

When you tune a prompt without a test set, you are not improving the system — you are improving your demo. The difference matters enormously. A demo is a selected scenario that you control. A test set is a representative sample of the chaos your users will actually produce.

Demo performance and real performance diverge the moment a user types something you did not anticipate. On every real system with real traffic, that happens within the first hour.

The cost of building a 10-to-20 example test set is roughly 30 minutes of honest work. You label inputs, describe what good output looks like, and note what failure would look like. The cost of skipping it is days of debugging production failures in a system you cannot explain, combined with the erosion of user trust that is nearly impossible to rebuild once it is lost.

There is also a subtler cost. Without a test set, you have no way to know whether an iteration made things better or worse in aggregate. You change the prompt, try it on the same three examples you have been staring at for a week, and conclude it improved. But maybe those three examples improved and 12 others regressed. A test set makes invisible regressions visible. That is its primary value, and you cannot replicate it by intuition.

## Start With The Smallest Honest Question

Before tuning the system, ask:

> What job must this feature do well enough to be useful?

This question has a discipline built into it. "Well enough" forces you to name a threshold. "Useful" forces you to think about the person on the other side of the feature. Both constraints prevent v1 scope from expanding indefinitely.

Not:
- "How do I make it amazing?"
- "How do I make it fully autonomous?"

Those questions have no finish line. V1 needs a narrow success condition.

Good examples of narrow success conditions:

- "Summarize internal notes accurately enough that a human editor takes less than 5 minutes per note instead of 20"
- "Classify support tickets well enough that triage time drops, even if a human spot-checks the queue daily"
- "Answer document questions with grounded excerpts — the answer must include a direct quote from the source document"

Notice that each of these examples includes a human in the loop. That is intentional. V1 is not about autonomous systems. V1 is about tools that amplify human work without replacing human judgment. A human reviewer catches the errors the system makes. That reviewer also provides the signal you need to understand where the system is failing, which feeds your next iteration cycle.

Narrowing scope this way also makes failure cheap. If the system gets something wrong, the damage is bounded. A human catches it and corrects it. The feature does not need to be right every time to be valuable — it needs to be right often enough, in the narrow domain you have defined, that it saves time compared to doing the job manually.

**Active Check — Before reading further, think through this scenario:**

A product manager proposes the following v1 success condition: "The AI assistant should be as helpful as possible for customer service reps." What is the problem with this definition, and how would you rewrite it?

The problem is that "as helpful as possible" is unmeasurable. There is no threshold that tells you whether v1 is done. There is no way to run an evaluation set against it because you cannot decide what a passing grade looks like. Every iteration will feel like progress and none will feel like completion.

A rewrite: "The AI assistant should answer FAQ-type questions accurately enough that reps spend less than 2 minutes searching the knowledge base per ticket, as measured by a 2-week sample of 50 tickets." Now you have a threshold (2 minutes), a time window (2 weeks), and a sample size (50 tickets). You know what done looks like, and you can test for it.

## Evaluation Does Not Need To Be Fancy

For a first production system, evaluation can be simple:
- 10-20 representative examples
- expected output shape for each example
- pass/fail criteria you can apply consistently
- notes on failure patterns when something goes wrong

The point is not statistical perfection.

The point is to stop relying on cherry-picked impressions.

A good evaluation set for v1 has three properties.

**Representative**: The examples must reflect the real distribution of inputs the system will receive. If your users send short one-sentence questions and long multi-paragraph emails, your eval set needs both. If most inputs are in English but 15% are in Spanish, include Spanish examples. If the system will receive inputs from multiple departments with different vocabulary, include examples from each. A test set that only covers one slice of the input space will mislead you about performance on the other slices.

**Labeled**: For each example, you need a ground-truth answer — not what the system produces, but what the correct output actually is. This is the reference you compare against. For classification tasks, this is the correct label. For summarization, this is a human-written summary you consider acceptable. For question answering, this is the correct answer plus its source location. The labels are written before you run the system, not after — otherwise you will unconsciously adjust them to match the output you see.

**Varied**: Include easy cases, hard cases, and edge cases. A test set that only contains examples your system already handles correctly is worse than useless. It will mislead you into thinking the system is more reliable than it is. The hard cases and edge cases are the ones that will bite you in production. Find them in testing, not after launch.

Building this set takes real work. That work is not wasted — it is the most valuable debugging tool you will have for the entire life of the feature. The eval set is a living document that grows as the input distribution changes and as you discover new failure modes.

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

That "one thing at a time" rule matters more than any other single practice in this module.

If you change the prompt, the model, the context length, and the output format in the same iteration, you cannot determine which change caused any improvement. You might be hiding two changes that hurt performance behind one change that helped dramatically. The system improves on your eval set, you ship, and a week later you have production failures you cannot trace to a root cause.

The rule is not about being slow. It is about learning. Each isolated change teaches you something specific about the system. After several controlled iterations, you develop causal understanding: this system responds strongly to task clarity in the prompt, moderately to context quality, and not at all to temperature adjustments. That understanding is not transferable from someone else's experience — it must be built through your own controlled experiments on your own task.

## A Fully Worked Iteration: From Failure to Fix

This section walks through one complete iteration cycle. The pattern it demonstrates applies to nearly every AI debugging situation you will encounter.

### The Setup

You are building a support ticket classifier. The system reads incoming customer messages and assigns each one to one of three urgency levels: `high`, `medium`, or `low`. A human triage agent uses these labels to prioritize their queue.

Your initial prompt:

```text
You are a support ticket classifier. Read the customer message and assign
it an urgency level: high, medium, or low. Reply with just the label.
```

You test on five hand-picked examples and they all look correct. You share a demo. The team approves. You build a proper 20-example evaluation set from real historical tickets before shipping.

### The Failure

Running the system against the 20-example eval set reveals these failures:

| Input | Expected | System Output |
|-------|----------|---------------|
| "My order hasn't arrived and I need it for tomorrow morning's presentation" | high | medium |
| "I've been trying to cancel my subscription for 3 days and keep getting errors" | high | medium |
| "I accidentally deleted my project and have a client demo in 2 hours" | high | low |
| "The dashboard has been down since this morning and we can't access our data" | high | medium |

The system gets 11 correct and 9 wrong out of 20. All four failures shown above are in the `high` category — the system is systematically under-labeling urgency.

### The Diagnosis

The instinct at this point is to switch to a stronger model. Resist it.

Instead, read the failing inputs and ask: what information is the system missing that a human triage agent would use to make the correct decision?

All four failures share a pattern. The urgency is driven by time pressure ("tomorrow morning," "2 hours"), escalating frustration ("3 days and keep getting errors"), or business impact ("can't access our data"). A human reads these signals immediately. But the prompt says nothing about any of them. The prompt says "high, medium, or low" and provides zero definition of what makes something high.

The diagnosis: **the task is ambiguous**. "High urgency" means something specific to this business, but that meaning is not in the prompt. The model is guessing based on its training data's general understanding of urgency, which does not match what the triage team actually needs.

### The Fix

Change one thing: add urgency definitions to the prompt.

```text
You are a support ticket classifier. Read the customer message and assign
it an urgency level using the definitions below.

Urgency definitions:
- high: the customer has a time-sensitive deadline within 24 hours, is
  experiencing service unavailability that blocks their work, has
  escalated after repeated failed attempts, or describes significant
  business or financial impact
- medium: the customer needs help with a non-blocking issue, has a
  question, or is following up on an existing request without urgency
  signals
- low: general inquiry, feature request, or issue the customer has
  indicated can wait

Reply with just the label: high, medium, or low.
```

The model, the context window, the temperature, the output format — none of these changed. Only the prompt content changed, and only by adding definitions that were always implicitly required but never written down.

### The Result

Re-run the same 20-example eval set. The system now gets 18 correct. All four failures above now produce the correct `high` label. Score improves from 55% to 90%.

### What This Teaches

Several things are worth naming explicitly because they apply beyond this specific scenario.

**Failures cluster around patterns.** The system was not randomly wrong — it was systematically wrong about one type of input. Reading failure patterns is diagnostic work, not discouraging noise. Four failures that all share the same root cause point directly at the fix.

**The prompt is your first lever.** Before changing anything else, read the prompt as if you are the model. Ask: is every relevant concept defined here? Would a new employee understand this instruction without any context? If not, clarify it first. The worked example above shows what happens when you do: most failures disappear in a single iteration.

**Eval sets make progress visible and measurable.** Without the 20-example set, you would have seen four failures in a row and made a random guess about the cause. With the set, you see 11/20 become 18/20 and you know exactly how much you improved. That score also tells you there are still two remaining failures to investigate in the next iteration.

**One change isolates causation.** Because only the urgency definitions changed, you know with certainty why performance improved. That knowledge makes the next iteration faster: you already know the remaining two failures are not caused by missing definitions, so you look elsewhere.

## What To Change First

The order of operations in AI iteration is not arbitrary. Different intervention types have different costs, different implementation times, and different ceilings on how much they can improve a broken system.

```
┌──────────────────────────────────────────────────────────────────────┐
│                    ITERATION PRIORITY ORDER                          │
│                                                                      │
│  1. Clarify the task              lowest cost, often highest impact  │
│     add definitions, scope,                                          │
│     constraints to the prompt                                        │
│                                                                      │
│  2. Improve context               what the model reasons with        │
│     better retrieval, more                                           │
│     relevant source material,                                        │
│     structured input format                                          │
│                                                                      │
│  3. Improve output shape          reduces downstream errors          │
│     structured output, few-shot                                      │
│     examples, explicit format rules                                  │
│                                                                      │
│  4. Add validation                catch failures before they reach   │
│     post-processing checks,       the user                           │
│     confidence thresholds,                                           │
│     human-in-the-loop gates                                          │
│                                                                      │
│  5. Change model or settings      highest cost, marginal gain        │
│     bigger model, fine-tuning,    once task is clear                 │
│     temperature, retrieval                                           │
└──────────────────────────────────────────────────────────────────────┘
```

### Why This Order?

Each step in the priority order has a prerequisite: you cannot extract value from a more capable model if the task is ambiguous. A bigger model will confidently do the wrong thing faster. It will produce more polished outputs in the wrong direction. It will hallucinate more convincingly. Capability amplifies whatever you give it — including unclear instructions.

The worked example from the previous section demonstrates this directly. Switching from a smaller to a larger model would not have fixed the urgency classification failures, because the problem was not model capability. The model did not know what "high urgency" meant in this business context. No amount of raw capability resolves an undefined concept.

### A Priority Inversion Scenario

Consider a team building a document Q&A system. The system retrieves relevant passages from a product manual and uses them to answer customer questions. Early testing shows frequent hallucinations: answers that sound plausible but are not grounded in the retrieved content.

**The wrong approach (priority inversion):** The team schedules a fine-tuning run on a dataset of manual Q&A pairs. Fine-tuning costs money, takes days to prepare the dataset and run the job, and produces a model that is harder to update. The team will not have results until next week.

**The right approach (priority order):** Before fine-tuning, the team reads the current prompt:

```text
Answer the following question based on your knowledge of the product.
```

The problem is immediately visible. The prompt says "your knowledge" — the model is ignoring the retrieved passages entirely and answering from its training data. The retrieved context is being passed in but the prompt is not instructing the model to use it.

Changing "your knowledge of the product" to "the retrieved passages provided below" eliminates the majority of hallucinations in the same afternoon. The fix takes 30 seconds to write and 5 minutes to test. No fine-tuning required.

Fine-tuning might still improve the system at a later stage. But jumping to step 5 when step 1 was broken would have cost a week of calendar time and real money while producing zero improvement, because the capability gap was not the problem.

**Active Check — Before reading the next section, work through this:**

A teammate is building a code review assistant. The system reads pull request diffs and provides feedback. The feedback is verbose and repetitive — it comments on every line, including trivial formatting issues, and often says the same thing in multiple different ways. The teammate says: "I think we need a stronger model with better instruction-following."

Walk through the priority order. What would you check before agreeing to that model switch?

You would start with the prompt. Does the prompt define what a useful code review comment looks like? Does it specify how many comments are appropriate per review? Does it say anything about excluding formatting issues that a linter should catch? Does it give an example of the review style you want? If the answer to any of these is no, you would clarify the task first. A model with better instruction-following will still produce verbose output if the desired output format is not defined. Only after confirming that the task is clearly specified, the context is appropriate, and the output format is explicit would you consider a model upgrade — and at that point, you might find the upgrade is unnecessary.

## What Shipping v1 Really Means

The word "shipping" carries different weight in AI development than in traditional software. When a web form has a bug, users see an error message and stop. When an AI feature has a bug, users often cannot tell — the output looks plausible and wrong at the same time. A classification system silently misroutes tickets. A summarizer silently omits critical details. A Q&A system confidently cites information that does not exist in the source document. That asymmetry changes what "ready to ship" means.

A good v1 is:
- **Useful**: it reduces work or solves a real problem for a real person, measurably
- **Bounded**: it operates in a narrow, well-defined domain where failures are visible and recoverable
- **Explainable**: a teammate can describe in one sentence what it does and what it does not do
- **Reviewable**: outputs can be audited, questioned, and corrected without significant friction

A bad v1 is:
- **Open-ended**: the scope expanded during development and nobody has a clear current definition
- **Hard to evaluate**: you still cannot describe success in one sentence that a skeptic would accept
- **Over-trusted**: the team treats demo performance as a proxy for reliability
- **Opaque**: wrong outputs are indistinguishable from right outputs without domain expertise

The distinction matters most at deployment time. A bounded, reviewable system absorbs mistakes at low cost. A human reviewer catches the error, corrects it, and the system continues. An open-ended, opaque system absorbs mistakes silently, compounds them over time, and eventually produces failures that are expensive to trace and embarrassing to explain.

## Signs You Are Ready To Ship

Use this as a checklist, not a feeling.

The use case is narrow enough that you can describe what the system does in one sentence that a skeptic would accept.

Failure modes are visible — when the system gets something wrong, a reviewer can identify the error without being an AI expert.

Humans can review outcomes in high-stakes cases, even if routine cases are handled automatically.

You have documented examples of typical success and typical failure. Both are written down. New teammates can be onboarded to review outputs without a long verbal explanation.

The system reduces work instead of adding ambiguity. The person using it finishes tasks faster or with less cognitive load than before the feature existed.

Your eval set from development is available to re-run after any future change. You have not lost the test cases.

## Signs You Are Not Ready

You still cannot describe success in one sentence that a skeptic would accept.

Every demo depends on a carefully phrased input. Normal messy user inputs produce inconsistent results.

Wrong outputs look too plausible to detect without domain expertise. A casual reviewer would accept them as correct.

Nobody owns validation. There is no named person or process responsible for checking that the system continues to work correctly.

The system performs actions you cannot comfortably audit — sends emails, deletes records, calls external APIs — without a human review step.

The scope has grown since you started building. The original narrow problem has accumulated features that have not been evaluated against a test set.

## Did You Know?

1. The term "evals" comes from the NLP research community, where it originally referred to standardized benchmarks for comparing language models across research groups. In production AI development, the meaning shifted to mean any structured test of a model's behavior on a specific task — which is why companies now publish internal eval tooling as open-source. OpenAI's evals repository contains over 1,000 community-contributed evaluation sets covering tasks from logical reasoning to translation quality.

2. A 2023 study from Stanford's Center for Research on Foundation Models found that GPT-4's performance on a standard coding benchmark dropped by over 40 percentage points across a 6-month window — without any change to the model version accessed by callers. The degradation came from changes in safety tuning and training distribution applied by the provider. This is why re-running your evaluation set after any model provider update is not optional maintenance — it is the only way to detect a silent regression.

3. The practice of shipping a bounded v1 before expanding autonomy has a formal name in safety engineering: graduated autonomy. Aviation autopilot systems follow the same pattern — the system handles one flight regime reliably before being extended to another. AI features benefit from the same logic: demonstrate reliability in the bounded case first, then extend scope incrementally as each extension is validated.

4. "Prompt drift" is a documented failure mode in long-running AI systems where the effective behavior of a prompt degrades over time even when the prompt text is unchanged. Causes include: underlying model updates by the provider, changes in the data being fed as context, shifts in the vocabulary used by upstream systems, and subtle changes to API defaults. Teams that do not periodically re-run their eval sets often discover prompt drift months after it began, when the system's behavior has already diverged significantly from its original specification.

## Common Mistakes

| Mistake | Why It Hurts | Better Move |
|---------|-------------|-------------|
| Tuning prompts without an eval set | Progress is imaginary — you are optimizing the demo, not the system | Define 10-20 representative examples before the first iteration |
| Changing multiple variables in one iteration | No causal learning; you cannot tell which change helped or hurt | Change exactly one thing per iteration and measure before changing the next |
| Treating three good demo results as reliability evidence | Selection bias; demos are curated, production is not | Test on representative inputs including messy, off-spec, and edge cases |
| Jumping to a bigger model before clarifying the task | Capability amplifies unclear instructions; you get confident wrong answers faster | Work through the priority order: task clarity first, then context, output shape, validation, then model |
| Shipping open-ended scope as v1 | Failures are invisible and expensive to trace after the fact | Narrow the scope until you can describe success in one sentence |
| Skipping documentation of failure modes | New team members have no reference for what "wrong" looks like | Document at least two typical failure examples alongside your eval set |
| Trusting outputs in high-stakes decisions without a review step | AI outputs can be plausibly wrong; users may not detect errors | Add a human review gate for outputs that have significant downstream consequences |
| Abandoning the eval set after initial launch | Models change, prompts drift, upstream data shifts — regressions become invisible | Schedule periodic re-runs of the eval set, especially after provider updates |

## Quick Quiz

1. **Your team spent two weeks improving a document Q&A system by iterating on the prompt. On Friday, the eval score is 74%. On Monday, you changed nothing over the weekend, and the score is 68%. What is the most likely explanation, and what should you do next?**

   <details>
   <summary>Answer</summary>
   The model provider likely updated or rolled back the underlying model version, or the retrieval index was rebuilt with different content. AI systems have external dependencies that can change without your knowledge. You should check the provider's changelog for the weekend, version-pin the model if the API allows it, and re-run your eval set against specific failure cases to identify which input types regressed. This is exactly why a persistent eval set is valuable — it makes silent regressions immediately visible.
   </details>

2. **A data scientist says: "I ran the classifier on 5 example inputs and it got all 5 right. I think we're ready to ship." You look at the examples and notice they are all short, clearly worded, English-language requests from the same product area. What is wrong with this conclusion, and how do you respond?**

   <details>
   <summary>Answer</summary>
   Five examples from a single, narrow slice of the input distribution is not a reliability signal — it demonstrates that the system works on easy cases from one category. The team's real traffic likely includes longer inputs, ambiguous phrasing, edge cases, and potentially multiple languages or product areas. You would ask the data scientist to build a 15-to-20 example eval set drawn from historical production data or realistic synthetic variants that cover the full input distribution, then re-evaluate. A score on that broader set is the first honest signal about readiness.
   </details>

3. **You are iterating on a customer email triage system. After five rounds of changes, performance has not improved. You changed: the prompt wording (round 1), the model from gpt-4o-mini to gpt-4o (round 2), the context window size (round 3), the output format instructions (round 4), and the retrieval strategy (round 5) — one per round. Your eval score is 61%, the same as when you started. What does this tell you, and what should you do?**

   <details>
   <summary>Answer</summary>
   Five iterations with no cumulative improvement suggests the system has a structural problem that none of these variable changes address. Possible root causes: the eval set itself is wrong (labels are inconsistent or incorrect), the task definition is still ambiguous (no amount of prompt tuning will converge on a clear output if the input definition is unclear), or the information needed to make correct decisions is not present in any of the contexts being provided. The right move is to step back from iteration and re-examine first principles: read 10 failing examples carefully, ask what information a human would use to classify them correctly, and check whether that information is present in what the system receives.
   </details>

4. **An AI feature classifies expense reports as "policy-compliant" or "review-required." The team tested it on 50 historical examples and scored 94% accuracy. The product manager wants to ship with full automation — no human review. What would you flag before agreeing?**

   <details>
   <summary>Answer</summary>
   A 94% accuracy rate on 50 examples means approximately 3 misclassifications in the test set. At production scale, that miss rate translates into a concrete volume of misclassified expense reports per day. You would flag: (1) the absolute miss rate at production volume, not the percentage; (2) the asymmetric cost of false negatives — policy violations classified as compliant carry financial and compliance risk, which is much more serious than compliant reports flagged for review; (3) whether the 50-example set included unusual or adversarial expense reports, or only routine cases; (4) the absence of any human catch for the cases the system gets wrong. For a financial compliance feature, a human review gate on borderline confidence cases is appropriate at v1 regardless of the headline accuracy number.
   </details>

5. **Your team is building a feature that summarizes weekly engineering reports for executives. The current eval score is 66%. A teammate proposes fine-tuning on 200 example summaries. Before approving, what do you verify about the current system state?**

   <details>
   <summary>Answer</summary>
   Fine-tuning is a high-cost, high-commitment intervention that should follow, not precede, the priority order. Before approving it, verify: (1) Is the prompt clear about what a good summary includes — audience level, length, what sections to prioritize, what to exclude? (2) Is the context (the report content) well-structured, or is the model receiving unformatted raw text that makes extraction difficult? (3) Is the output format explicit — does the prompt specify sections, maximum length, bullet format? (4) Have you tried few-shot examples of acceptable summaries in the prompt? If any of these are underspecified, address them first. Fine-tuning on 200 examples will not compensate for an unclear task definition — it will teach the model to confidently produce summaries in whatever ambiguous style the 200 examples happen to exhibit.
   </details>

6. **A junior developer changed the output format instructions and the system prompt wording in the same iteration. Performance went from 58% to 76%. They want to commit both changes. How do you advise them?**

   <details>
   <summary>Answer</summary>
   You cannot know which change caused the improvement, or whether both contributed, or whether one change gained 22 points while the other lost 4. You advise the developer to reset to the baseline, apply only the output format change and measure, then reset again and apply only the prompt wording change and measure. If each change shows improvement independently, commit both with confidence. If one change accounts for most of the gain, you understand the system better and can decide whether both are worth carrying. The goal is causal knowledge, not just a higher score — because the next iteration requires knowing what actually worked.
   </details>

7. **You shipped a v1 support ticket classifier three months ago. A new product line launches next week that will introduce a new category of ticket your eval set does not cover. What do you do before those tickets start arriving?**

   <details>
   <summary>Answer</summary>
   Before the new ticket type enters production, you add examples of those tickets to the eval set with correct labels, re-run the full set to measure current performance on the new category, and iterate if performance is below your v1 threshold. Shipping the new product line without updating the eval set means running blind on a new input distribution. The eval set is a living document — it must grow whenever the input distribution changes. Skipping this step is how silent regressions become visible only after users complain.
   </details>

## Hands-On Exercise

This exercise takes you through one complete evaluation-and-iteration cycle. Work through it on a real feature you are building, a feature you have already built, or a plausible scenario you can reason about concretely.

### Step 1: Define the Task

- [ ] Write the user job in one sentence: "The system should [action] for [user] so that [outcome]."
- [ ] Write the input format: what text, data, or content the system receives.
- [ ] Write the output format: what the system should produce.

### Step 2: Build an Evaluation Set

- [ ] Write 15 realistic example inputs. Include at least 3 easy cases, 3 hard cases, and 3 edge cases.
- [ ] For each example, write the expected output before running the system.
- [ ] For each example, write one sentence explaining why that is the correct output.

### Step 3: Define a Success Threshold

- [ ] State the minimum accuracy or quality score that makes the feature useful at v1.
- [ ] State one failure mode that would make the feature harmful or unusable if it occurred frequently.

### Step 4: Run and Diagnose

If you have a working system: run it on your 15 examples, record the score, and identify the most common failure pattern.

If you do not have a working system: write the prompt you would use, predict where it would fail and why, and describe what the failure pattern would look like.

- [ ] Identify which step in the priority order applies to the most common failure: task clarity, context quality, output shape, validation, or model capability.

### Step 5: Change One Thing

- [ ] Write what you changed and why, in one sentence.
- [ ] Re-score (or re-predict). Write the change in performance as a before/after number.
- [ ] If the change helped, explain why you believe it helped. If it did not help, explain what you learned.

### Step 6: Write the Shipping Checklist

For each criterion in the "Signs You Are Ready To Ship" section, evaluate your feature. For any criterion your feature does not meet, write one concrete action that would close the gap.

### Success Criteria

- [ ] The task description passes the "one sentence a skeptic accepts" test
- [ ] The eval set includes easy, hard, and edge cases with documented expected outputs written before running the system
- [ ] The iteration round changed exactly one variable and produced a measurable result
- [ ] The shipping checklist identifies at least one gap and a concrete action to close it

## Next Module

From here, continue to:
- [AI/ML Engineering: AI-Native Development](../../ai-ml-engineering/ai-native-development/)
- or [AI/ML Engineering: Generative AI](../../ai-ml-engineering/generative-ai/)

## Sources

- [OpenAI Evals](https://github.com/openai/evals) — Concrete examples and tooling for building repeatable eval sets and comparing changes over time.
- [NIST AI RMF Playbook](https://www.nist.gov/itl/ai-risk-management-framework/nist-ai-rmf-playbook) — Useful for turning evaluation and review steps into an explicit shipping and governance practice.
- [OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/) — Relevant when moving from prompt iteration to shipping, because it highlights common security and reliability risks in LLM features.

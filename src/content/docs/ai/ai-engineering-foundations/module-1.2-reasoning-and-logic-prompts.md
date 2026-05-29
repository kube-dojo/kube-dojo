---
title: "Reasoning and Logic Prompts"
slug: ai/ai-engineering-foundations/module-1.2-reasoning-and-logic-prompts
sidebar:
  order: 12
revision_pending: false
---

> **AI Engineering Foundations** | Complexity: `[COMPLEX]` | Time: 80-100 min
>
> **Prerequisites**: Prompt Fundamentals from this section, plus comfort comparing model outputs against a task contract. If you need the baseline contract vocabulary first, revisit the [Prompt Fundamentals entry in the section index](../#planned-modules).

---

## Learning Outcomes

By the end of this module, you will be able to:

- **Design** reasoning-eliciting prompts for math, diagnosis, planning, classification, and decision tasks without turning every request into a long chain-of-thought ritual.
- **Distinguish** reasoning prompts from reasoning models by deciding when prompt scaffolding helps an ordinary model and when a model with native thinking budget should be left to use its own internal trace.
- **Compare** zero-shot CoT, few-shot CoT, self-consistency, least-to-most prompting, plan-and-execute, verifier prompts, ReAct, and Tree-of-Thoughts as different cost and control points.
- **Evaluate** reasoning effort controls across Claude, OpenAI, and Gemini APIs by naming what they budget, what they do not guarantee, and when the extra latency is justified.
- **Build** a small experiment that prompts one task with three reasoning strategies, compares outputs against a rubric, and records which strategy should enter a reusable prompt library.

## Why This Module Matters

Prompt fundamentals taught you to write a compact task contract: task, context, constraints, and output shape.
Reasoning prompts add a second question.
They ask how much cognitive work the model should perform before it answers, and how much of that work should be guided by the prompt rather than by the model family itself.

That distinction matters because the most famous chain-of-thought advice was discovered in an earlier model era.
The phrase "Let's think step by step" became memorable because Kojima et al. showed that a simple zero-shot prompt could unlock better multi-step reasoning on several arithmetic, symbolic, and logical tasks in older pretrained and instruction-tuned models.
The lesson was never that every prompt should expose a long scratchpad.

The lesson was that some models needed an external cue to stop answering by pattern completion and begin decomposing a task.
Modern reasoning models changed the baseline.
OpenAI o-series models, GPT-5-series reasoning controls, DeepSeek-R1-style systems, and Claude models with thinking modes are built or served so the model can spend extra hidden or structured thinking budget before the final answer.

That means the prompt engineer's job shifts from "force a chain of thought" to "choose the right reasoning surface."
Sometimes the best prompt says "solve carefully and return only the final answer plus checks."
Sometimes the best API setting raises reasoning effort while the visible prompt stays simple.

Sometimes the best workflow splits the work into a planner, executor, and verifier because the task needs a system, not a smarter paragraph.
The failure mode is easy to miss because bad reasoning prompts often look impressive.
A response with numbered steps, causal language, and a confident conclusion can feel more rigorous than a short answer.

It may also be slower, more expensive, more vulnerable to anchoring, and no more correct.
Forcing visible reasoning on a simple lookup can waste tokens without improving quality.
Forcing a step-by-step scaffold on a true reasoning model can bias the model toward the user's weak plan instead of letting the model use its native hidden trace.

Asking "explain your reasoning" can also cause the model to rationalize an answer it already selected, producing a polished story rather than a reliable proof.
This module treats reasoning prompts as engineering tools.
You will learn when to use a lightweight cue, when to provide examples, when to sample multiple paths, when to decompose the task, when to ask a separate verifier, and when to spend search or reasoning-budget tokens.

You will also learn when to stop.
The senior move is not to apply every reasoning pattern.
The senior move is to match the task class, model capability, latency budget, audit need, and failure cost.

### War Story

Hypothetical scenario: a platform team had a mature incident-triage prompt written for a non-reasoning chat model.
The old prompt began with a long scaffold: identify symptoms, list hypotheses, reason step by step, score each cause, revise the score after each log line, then answer.
On the old model, that scaffold helped because it slowed the model down and forced the answer into an inspectable diagnostic shape.

The team later migrated the same workflow to a Claude Sonnet deployment with thinking enabled.
At first, quality dropped.
The model followed the inherited scaffold too literally, over-weighted early hypotheses, and spent visible output budget narrating checks that the new model could already perform internally.

The fix was not a bigger prompt.
The fix was to remove most of the old chain-of-thought preamble, keep the incident evidence contract, raise thinking budget only for multi-signal cases, and ask for a concise answer with evidence, uncertainty, and next verification commands.
The lesson is not that old prompts are bad.

The lesson is that a prompt can become a compatibility shim for yesterday's model.
When the model family changes, reasoning prompts must be revalidated like any other interface.

### The Prompt-Engineering Angle

The newly merged [Reasoning-Model RL: GRPO, RLVR, and DeepSeek-R1](../../ai-ml-engineering/advanced-genai/module-1.12-reasoning-models-and-grpo/) module explains how reasoning behavior can be trained, rewarded, and evaluated inside model development.
This module stays at inference time.
You are not choosing PPO, GRPO, or a verifier-backed training loop here.

You are choosing the prompt, sampling strategy, tool sequence, verifier prompt, and API reasoning budget for a task you need to solve today.
That boundary keeps the two modules complementary.
The GRPO module asks how a model learns to reason under reward pressure.

This module asks how an application developer should elicit, constrain, and verify reasoning from a model that already exists.
If you remember only one sentence, remember this one: reasoning prompts are external scaffolds, while reasoning models have internal or served-time reasoning machinery.
External scaffolds are useful when they add missing structure.

They become harmful when they duplicate, constrain, or distract a model that already has a better reasoning procedure available.

## Reasoning Prompts Versus Reasoning Models

A reasoning prompt is an instruction pattern that asks a model to do intermediate cognitive work.
It may say "think step by step," provide worked examples, decompose a task into subproblems, sample several candidate paths, or ask a separate verifier to critique the answer.
The scaffold lives in the prompt or harness.

It is visible to you, easy to edit, and often portable across providers.
A reasoning model is different.
It is a model family or serving mode trained and configured to spend extra computation on hard problems before producing a final answer.

The reasoning process may be hidden, summarized, encrypted as state, or exposed only through metadata depending on the vendor and model.
The important control is not the phrase "think step by step."
The important control is the model's ability to allocate reasoning compute, sometimes through an API knob such as `reasoning.effort`, `thinking.budget_tokens`, adaptive thinking, or `thinkingBudget`.

The distinction changes prompt design.
On an older instruction model, a zero-shot CoT cue can convert a one-hop answer into a multi-step attempt.
On a modern reasoning model, the same cue may mostly change the visible style of the final answer.

It can also consume output budget, encourage a rigid path, or leak a partial rationale to a user who needed a short decision.
Treat the prompt as a control surface, not as proof that the model reasoned correctly.
The practical question is whether the task needs external structure.

If the task has hidden dependencies, a decomposition prompt may help because it changes the work plan.
If the task has a single verifiable answer, self-consistency may help because independent paths can converge on the same result.
If the task is a simple lookup, a chain-of-thought scaffold usually adds cost without changing the answer.

If the task is served by a reasoning model with a configured thinking budget, prompt the outcome and verification criteria before prescribing the path.
The table below is a useful first-pass classifier.

| Task class | CoT scaffold likely helps? | Reasoning model likely helps? | Preferred prompt surface |
|---|---:|---:|---|
| Simple lookup from supplied text | No | Usually no | Direct answer with citation or field reference |
| Multi-step arithmetic or symbolic manipulation | Often | Often | Minimal reasoning cue or reasoning effort, plus final check |
| Incident triage with mixed evidence | Sometimes | Often | Evidence table, hypotheses, missing information, verifier pass |
| Long planning with dependencies | Often | Often | Decomposition, plan-and-execute, tool checkpoints |
| Creative ideation with no objective answer | Sometimes | Sometimes | Diverse candidates and selection criteria, not long CoT |
| Safety-sensitive recommendation | CoT alone is insufficient | Sometimes | Separate safety/evidence verifier and policy constraints |

Do not read the table as a benchmark claim.
Read it as a routing checklist.
The model, domain, data quality, and evaluation rubric still decide the answer.

For every repeated workflow, run a small comparison before standardizing the prompt.
The comparison should include at least one direct prompt, one scaffolded prompt, and one provider-native reasoning setting when available.

### A Minimal Decision Rule

Use a visible reasoning scaffold when the scaffold changes the task structure.
For example, "decompose this migration into dependency-ordered steps before drafting the runbook" changes the work because a dependency graph is the artifact.
Use model-native reasoning effort when the task is hard but the desired final answer is concise.

For example, "solve the scheduling conflict and return the selected plan plus the two rejected alternatives" benefits from private search without showing every path.
Use a verifier prompt when correctness can be checked from criteria separate from the draft.
For example, "check whether the plan violates any stated rollout constraint" gives the model a different role and a narrower target.

Use search-based reasoning only when wrong answers are expensive enough to justify multiple branches.
For example, a production remediation plan may justify candidate generation, branch scoring, and backtracking.
A feature-name lookup does not.

### Why "Explain Your Reasoning" Is Not Enough

"Explain your reasoning" asks for a narrative.
It does not specify whether the reasoning should be exhaustive, faithful, concise, checked, or separated from the final answer.
It also invites the model to make the answer sound justified after the fact.

That is useful for teaching, but weak for production decisions.
A better prompt names the reasoning artifact you need.
Ask for "assumptions, evidence, and unresolved risks" when the issue is uncertainty.

Ask for "subproblems and dependency order" when the issue is decomposition.
Ask for "candidate answers and a majority vote" when the issue is brittle single-path decoding.
Ask for "verifier findings against these acceptance criteria" when the issue is correctness.

The output should match the human review job.
When the reviewer needs to audit evidence, ask for evidence links and inferences.
When the reviewer needs only the answer, ask for the answer and a short confidence check.

When the reviewer is a program, ask for structured fields and run a separate verifier.
Reasoning prompts are only good when they make the next review step easier.

## Chain-of-Thought Variants

Chain-of-thought prompting asks the model to produce or use intermediate reasoning before the final answer.
The original family of techniques matters because it gave practitioners a way to elicit multi-step behavior without changing model weights.
It also created a bad habit: treating "CoT" as one technique instead of a family of controls.

Zero-shot CoT is the smallest member of the family.
It appends a cue such as "Let's think step by step" before the answer.
Kojima et al. showed that this simple cue improved several reasoning benchmarks for the models they studied.

The cue is attractive because it is cheap to try, easy to remember, and does not require examples.
It is also blunt.
It does not teach the task-specific reasoning pattern, constrain the final answer, or verify the result.

Few-shot CoT adds examples that show the desired reasoning pattern.
Instead of merely telling the model to reason, it demonstrates how a problem should be broken down and solved.
This helps when the task has a reusable structure: word problems, classification rationales, rule application, or structured diagnosis.

The risk is example overfitting.
The model may copy the example's surface form, wrong assumptions, or verbosity rather than the underlying reasoning strategy.
Self-consistency changes decoding rather than the visible prompt alone.

Wang et al. proposed sampling a diverse set of reasoning paths and selecting the most consistent final answer.
In application terms, you ask the model several times, extract final answers, and use a vote or verifier to select the result.
This can improve reliability when a problem has one correct answer but many possible solution paths.

It is less useful when the task is subjective, under-specified, or expensive to sample.
The following table separates the variants by what you control.

| Variant | What you provide | What you pay for | Best fit | Main risk |
|---|---|---|---|---|
| Zero-shot CoT | A short reasoning cue | One longer answer | Quick test on older or non-reasoning models | Verbose rationalization without better accuracy |
| Few-shot CoT | Worked examples with reasoning | Prompt tokens plus one answer | Repeated task family with stable pattern | Examples teach accidental style or assumptions |
| Self-consistency | Multiple sampled reasoning paths | Several completions and selection logic | Objective answers with path diversity | Cost rises quickly and voting can reward common wrong answers |

Use zero-shot CoT as a probe, not as a default.
If the direct answer fails because it skipped steps, try a lightweight cue.
If the cue helps, replace it with a more task-specific artifact before production.

For example, "list constraints, solve, then check the final answer" is usually better than a generic step-by-step phrase because it names the work you need.
Use few-shot CoT when examples define the method.
The examples should be short, correct, representative, and separated from the live input.

They should also follow the same output contract as the desired answer.
If the examples include long hidden calculations but the production answer should be concise, show a concise reasoning summary rather than a sprawling scratchpad.
Use self-consistency when one sampled path is too fragile.

A single generation can take a wrong turn early and never recover.
Multiple paths reduce that fragility if the task has a stable final answer.
However, majority vote is not a truth oracle.

If all samples share the same misconception or retrieve the same wrong assumption from the prompt, the vote only makes the wrong answer look more stable.

### Prompt Templates

The direct prompt should remain your baseline.
It gives you the fastest, cheapest answer and reveals whether the model already handles the task.
If the baseline passes your rubric, do not add CoT just because it feels more serious.

```text
Task: Solve the scheduling puzzle below.
Output: Return the final assignment and one sentence naming the binding constraint.
```

The zero-shot CoT probe should be small.
It should ask for a final answer separately so you can compare final correctness without being distracted by the explanation.

```text
Task: Solve the scheduling puzzle below.
Method: Work through the constraints carefully before answering.
Output: Return "Final assignment:" followed by the answer, then "Check:" with one sentence.
```

The few-shot CoT prompt should show the reasoning format without burying the live task.
Use one or two examples when the pattern is clear.
Use more only when the task boundary is subtle enough to justify the extra prompt tokens.

```text
Example:
Input: A must be before B. C cannot be first. Order A, B, C.
Reasoning summary: A before B leaves A-C-B or C-A-B. C cannot be first, so A-C-B remains.
Final: A-C-B

New input:
{{puzzle}}

Return the same two fields: Reasoning summary and Final.
```

The self-consistency harness is usually outside the prompt.
It samples several completions, extracts the final answer, and selects by vote or verifier.
If you implement it manually, record the sample count, temperature, extraction rule, and tie-break rule.

Otherwise, a later reviewer cannot reproduce why one answer won.

```text
Run N independent samples with the same task contract.
Extract only the value after "Final:" from each sample.
Choose the answer with the most votes.
If the vote is tied, send the tied answers to a verifier prompt with the original constraints.
```

### When CoT Is Redundant

CoT is redundant when the task does not require intermediate reasoning.
If the answer is literally present in the supplied text, ask for a cited extraction.
If the task is a format conversion, use a schema or example rather than a reasoning trace.

If the model already solves the task directly with high reliability, the scaffold is mostly latency and style.
CoT is also redundant when the model's native reasoning mode is doing the heavy work.
For Claude thinking, OpenAI reasoning effort, and Gemini thinking budgets, the provider is already allocating hidden or structured thinking resources.

In that setting, your prompt should define the goal, constraints, evidence boundaries, and final answer shape.
Prescribing a human-designed step list can be useful for compliance or audit, but it should be tested rather than assumed.
The best compromise is often a "reasoning summary" rather than full reasoning.

Ask the model to provide the final answer, the key constraint that decided the answer, and a short verification.
That gives a reviewer enough to inspect without forcing the model to expose or imitate a long scratchpad.
For safety-sensitive settings, use a separate verifier instead of asking the same answer to justify itself.

## Decomposition Prompting

Decomposition prompting breaks a hard task into smaller tasks before solving.
It is different from generic CoT because the intermediate artifact is not merely a narrative.
The artifact is a set of subproblems, a plan, a graph, or an execution order that can be reviewed.

Decomposition helps when the task has dependency structure.
Least-to-Most prompting, introduced by Zhou et al., asks the model to break a complex problem into simpler subproblems and solve them in sequence.
Each solved subproblem becomes context for the next one.

That pattern is useful when the final problem is harder than the examples or when easy-to-hard generalization matters.
For prompt engineers, the key idea is not the paper's exact benchmark setup.
The key idea is that solving smaller problems can create reliable stepping stones.

Plan-and-execute prompting separates "decide what to do" from "do it."
The planner writes a compact plan with dependencies, assumptions, and stopping conditions.
The executor performs each step, often using tools or documents.

The verifier checks whether the result satisfies the original goal.
This pattern fits agentic work because tool outputs can change the next step.
A structured task graph goes one level further.

Instead of a linear list, the prompt asks for nodes, dependencies, inputs, outputs, and validation checks.
This is useful when several subproblems can run in parallel or when one decision gates another.
It is overkill for a small answer, but valuable for migrations, incident response, release planning, and multi-file code changes.

### Diagram: Choosing a Decomposition Strategy

```text
+------------------+       +----------------------+       +----------------------+
| Zero-shot CoT    |       | Least-to-Most        |       | Tree-of-Thoughts     |
+------------------+       +----------------------+       +----------------------+
| One path         |       | Ordered subproblems  |       | Branching candidates |
| Low setup cost   |       | Medium setup cost    |       | High setup cost      |
| Good probe       |       | Good for dependency  |       | Good for search      |
| Weak audit trail |       | Reviewable sequence  |       | Reviewable pruning   |
+------------------+       +----------------------+       +----------------------+
         |                          |                              |
         v                          v                              v
Use when the model        Use when the problem          Use when several plausible
skips obvious steps       must be made easier           paths compete and wrong
but the task is small.    through solved pieces.        branches are costly.
```

The diagram is intentionally practical.
It does not say Tree-of-Thoughts is always better than Least-to-Most.
It says Tree-of-Thoughts spends more budget to explore branches, so the task must justify that budget.

For most everyday engineering prompts, a small decomposition or plan-and-execute loop is enough.

### Least-to-Most Template

Use this template when the final task can be decomposed into simpler subproblems whose answers feed later steps.
The prompt asks for the decomposition first, then solves each subproblem, then gives the final answer.

```text
Task: Solve the problem below.

First, decompose the problem into the smallest useful subproblems.
Second, solve the subproblems in dependency order.
Third, use the solved subproblems to produce the final answer.

Output:
- Subproblems
- Solutions
- Final answer
- Check against original constraints
```

The common mistake is letting the decomposition become decorative.
If the subproblems do not feed the solution, the model has merely written a longer answer.
Ask the model to reference earlier subproblem answers explicitly in later steps.

That makes the dependency chain visible enough to inspect.

### Plan-And-Execute Template

Use plan-and-execute when the task requires actions, tool calls, or multiple documents.
The planner should be short enough to review.
The executor should be allowed to revise the plan only when new evidence invalidates an assumption.

```text
Task: Complete the engineering change described below.

Planning phase:
- Identify the required files or data sources.
- List the steps in dependency order.
- Name assumptions and stop conditions.

Execution phase:
- Perform one step at a time.
- After each step, record evidence and any plan change.

Final output:
- Summary of changes
- Evidence checked
- Remaining risks
```

This pattern matters for AI agents because the prompt becomes a lightweight harness.
It prevents the model from jumping directly from goal to edit.
It also gives a human reviewer checkpoints: did the plan match the task, did execution follow evidence, and did the final answer close the original contract?

### Structured Task Graph Template

Use a task graph when the work has branching dependencies.
The graph does not need a heavy formal language.
A table is often enough.

```text
Return a task graph with these columns:

Node: short ID
Goal: what this node decides or produces
Inputs: evidence or prior nodes required
Output: artifact created by the node
Validation: how to check the node
Depends on: node IDs that must finish first
```

Graph prompts help avoid a common planning failure: doing work in the order it is mentioned rather than the order it depends on.
They also reveal parallel work.
If two nodes share no dependency, a harness can run them independently or ask different agents to investigate them.

That is where prompt engineering begins to touch harness engineering.

### Decomposition Failure Modes

Decomposition can fail by creating false certainty.
A neat list of subproblems can hide the fact that the model invented missing information.
Require the decomposition to mark unknown inputs.

If a subproblem cannot be solved from the supplied context, the correct answer is "blocked by missing evidence," not a guessed value.
Decomposition can also fail by freezing an early bad plan.
If the first subproblem is wrong, every later answer may inherit the error.

For agentic workflows, add a revision rule: after new evidence appears, compare it to the plan and revise only the affected nodes.
That rule keeps the model from either blindly following a stale plan or constantly replanning without progress.
Finally, decomposition can be too expensive.

If the task is a one-step transformation, decomposition adds latency and review burden.
The test is simple: if removing the decomposition does not make the answer harder to check, you probably did not need it.
Use decomposition when it produces a useful intermediate artifact, not when it merely decorates the answer.

## Reasoning Verification

Reasoning verification uses a separate prompt, pass, model, tool, or rubric to check the output.
The verifier is not the same as asking the original answer to "be careful."
It receives the original task, the proposed answer, and explicit criteria.

Its job is to find violations, missing evidence, inconsistent steps, or unsafe assumptions.
A verifier prompt works best when the criteria are external to the draft.
For example, a schema, test suite, policy, arithmetic answer key, acceptance criteria, or incident evidence set gives the verifier something concrete to compare against.

The verifier works less well when the only criterion is "does this sound reasonable?"
In that case, it may become a second generation of the same bias.
The simplest verifier prompt is adversarial but narrow.

It should not rewrite the answer first.
It should inspect the answer, return findings, and cite the exact criterion violated.
Only after findings are listed should a repair prompt produce a new answer.

```text
Verifier task: Check the proposed answer against the original task and criteria.

Inputs:
<task>
{{original_task}}
</task>

<criteria>
{{acceptance_criteria}}
</criteria>

<proposed_answer>
{{draft_answer}}
</proposed_answer>

Output:
- Pass/fail decision
- Findings, each tied to one criterion
- Missing evidence
- Minimal repair suggestion
```

Self-verification works for some classes of problems.
It can catch format violations, missing sections, arithmetic slips, contradictions between answer fields, and obvious unsupported claims.
It is especially useful when the answer can be checked by a rubric that was not already satisfied by style.

It also helps when the verification prompt changes the model's role from creator to auditor.
Self-verification fails when the model lacks the evidence needed to check the answer.
It also fails when the draft and verifier share the same misconception, when the acceptance criteria are vague, or when the output is persuasive but not grounded.

If the task is high-risk, use a different model, a deterministic tool, a human reviewer, or a test harness in addition to self-verification.
The important point is independence.
A verifier that sees the same misleading evidence and receives the same broad instruction may reproduce the same mistake.

Increase independence by changing the role, narrowing the criteria, hiding the draft until after criteria are restated, using a separate model family, or adding tool-based checks.
Do not call it verification if it is only another pass at writing.

### Verifier Patterns

Use an evidence verifier when claims must be grounded in supplied documents.
The verifier checks whether each claim has a source line, citation, or log entry.
It should distinguish "unsupported" from "false."

Unsupported means the source set does not prove the claim.
False means the source set contradicts the claim.
Use a logic verifier when constraints interact.

For scheduling, dependency ordering, access-control decisions, or puzzle-like tasks, the verifier should restate constraints and test the final answer against each one.
This is a better use of visible reasoning than asking the original answer to narrate every step.
The verifier's output is a checklist.

Use a safety verifier when the answer could cause harm or policy violation.
The verifier checks data exposure, permission assumptions, destructive operations, privacy boundaries, and escalation conditions.
This module only introduces the pattern.

The next module, [Prompt Safety and Evaluation in the section plan](../#planned-modules), goes deeper on safety and evaluation of reasoning chains.
Use a contract verifier when the output will enter a prompt library or automation.
The verifier checks placeholders, input fields, output schema, refusal behavior, failure modes, and version notes.

That connects directly to [Prompt Libraries and Contracts in the section plan](../#planned-modules), where the prompt becomes a maintained artifact rather than a one-off message.

### Repair After Verification

Do not ask the verifier to silently fix everything.
Silent repair hides the defect pattern from the reviewer.
Ask for findings first, then repair in a separate step using only those findings and the original task.

This creates a small audit trail.
The repair prompt should preserve correct parts of the draft.
Otherwise, a model can fix one issue while regressing another.

A good repair instruction says: "Revise only the sections named in verifier findings, preserve all passing sections, and rerun the acceptance checklist."
That is slower than "try again," but easier to trust.
When verification fails repeatedly, stop changing prompts and inspect the task.

The evidence may be insufficient, the criteria may conflict, or the model may be the wrong tool.
Repeated self-verification loops can create the illusion of rigor while the system remains under-specified.
Good prompt engineers know when the prompt is no longer the bottleneck.

## Tree-of-Thoughts and Search-Based Reasoning

Tree-of-Thoughts generalizes chain-of-thought from one path to many candidate paths.
Yao et al. describe a framework where the model explores coherent intermediate thoughts, evaluates choices, and can look ahead or backtrack.
In application terms, you generate several candidate next steps, score them, keep promising branches, and continue until a final answer emerges.

Search-based reasoning is useful when the first plausible path is often wrong.
Examples include combinatorial puzzles, planning under constraints, strategy design, complex debugging, and decisions where early assumptions can trap the answer.
The method is not free.

If you generate three branches for four steps, you have already multiplied calls and tokens.
Add verification at each step and the budget rises again.
The budget is justified when the cost of a wrong answer is higher than the cost of search.

A production incident remediation plan may justify branch exploration because the wrong path can waste human time or increase outage risk.
A product tagline probably does not need a thought tree.
Use cheaper diversity methods first unless the task has real search structure.

A simple ToT-style prompt has three roles: generator, evaluator, and controller.
The generator proposes candidate thoughts.
The evaluator scores them against criteria.

The controller chooses which branches continue.
Those roles can be one model in separate prompts, multiple models, or a harness around one API.

```text
Generator prompt:
Given the current state and goal, propose three distinct next reasoning moves.
Each move must name the assumption it tests and the evidence it needs.

Evaluator prompt:
Score each move from 1 to 5 against feasibility, evidence fit, and risk.
Reject any move that violates a stated constraint.

Controller rule:
Keep the top two moves unless both score below 3.
If all moves score below 3, stop and ask for missing information.
```

The controller rule is the part many teams skip.
Without it, Tree-of-Thoughts becomes "ask for many ideas."
The harness needs branch limits, stopping conditions, tie-breaks, and a way to prevent the model from repeatedly exploring the same idea in different words.

Search is an algorithmic pattern, not a vibe.

### When To Spend Search Budget

Spend search budget when tasks are hard, branchy, and checkable.
Hard means the direct prompt often fails.
Branchy means there are several plausible paths that cannot all be correct.

Checkable means you have criteria, tests, or evidence that can score branches before final selection.
If any of those conditions is missing, search may be theater.
For subjective tasks, use candidate generation and ranking rather than Tree-of-Thoughts language.

For ambiguous tasks, ask clarifying questions before branching.
For simple tasks, use a direct prompt and spend the saved tokens on evaluation coverage elsewhere.
Search-based reasoning earns its place only when the search tree has something real to search.

### A Small Search Harness

The following pseudo-harness is enough for many prompt experiments.
It is not production code.
It names the state you must track if you later automate the pattern.

```text
state = original_problem
branches = [state]

for depth in 1..max_depth:
  candidates = generate_next_moves(branches)
  scored = evaluate_candidates(candidates, criteria)
  branches = keep_top_k(scored, k=2, min_score=3)
  if solved(branches) or no_viable_branch(branches):
    break

return best_final_answer(branches)
```

Track the number of model calls, generated tokens, verifier tokens, and wall-clock time.
If the search harness improves correctness but triples latency, the product decision may still be no.
Reasoning quality is not the only metric.

Cost, latency, user patience, and review burden are part of the prompt design.


## ReAct: Interleaving Reasoning and Action

Chain-of-thought, decomposition, and Tree-of-Thoughts all improve how a model reasons from the information already inside the prompt or candidate branch. ReAct, short for reasoning and acting, changes the loop. The model alternates between a reasoning step, a tool action, and an observation, then uses the observation to decide what to do next. That makes ReAct useful when correctness depends on facts, calculations, repository state, logs, search results, or other information the model should not invent from memory.

The important shift is that the reasoning trace is no longer just explanatory text. It becomes a controller for tool use. A ReAct harness usually enforces a small grammar such as `Thought`, `Action`, `Observation`, and `Final Answer`; the model proposes the next action, the application executes only allowed tools, and the observation is appended to the next model turn. This is why ReAct belongs between reasoning prompts and agent frameworks: it is still a prompt pattern, but it only becomes dependable when a harness parses actions, records observations, limits iterations, and rejects unknown tools.

```text
Question: How tall is the Eiffel Tower in feet?
Thought: I need the trusted height in meters before converting units.
Action: lookup("eiffel tower height meters")
Observation: 330
Thought: I need the meters-to-feet conversion factor.
Action: lookup("meters to feet")
Observation: 3.28084
Thought: Now I can calculate 330 * 3.28084.
Action: calculate("330 * 3.28084")
Observation: 1082.6772
Thought: I have the source value, conversion factor, and calculation.
Final Answer: The Eiffel Tower is about 1,083 feet tall.
```

Use ReAct when the model must leave the prompt to gather or transform information. Do not use it as a more dramatic form of chain-of-thought for tasks that are already fully specified. A license-date extraction prompt probably does not need ReAct. A support assistant that must inspect current deployment events, check read-only constraints, and calculate an error-budget impact may need it because each observation can change the next safe action.

The following mini-harness is deliberately deterministic so you can run it without an API key. In a real application, `scripted_reasoner` would be replaced by a model call, but the parser, allow-listed tools, observation log, and max-step guard are the pieces you still need to test.

```python
from __future__ import annotations

import ast
import operator
import re
from collections.abc import Callable


ACTION_RE = re.compile(r'^Action:\s*(\w+)\("([^"]*)"\)', re.MULTILINE)
FINAL_RE = re.compile(r'^Final Answer:\s*(.+)$', re.MULTILINE)
OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
}


def safe_eval(expression: str) -> float:
    """Evaluate a tiny arithmetic expression without exposing Python eval."""
    tree = ast.parse(expression, mode='eval')

    def walk(node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return walk(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.UnaryOp) and type(node.op) in OPERATORS:
            return OPERATORS[type(node.op)](walk(node.operand))
        if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
            return OPERATORS[type(node.op)](walk(node.left), walk(node.right))
        raise ValueError(f'Unsupported expression: {expression}')

    return walk(tree)


def lookup(query: str) -> str:
    facts = {
        'eiffel tower height meters': '330',
        'meters to feet': '3.28084',
    }
    return facts.get(query.lower(), 'unknown')


def calculate(expression: str) -> str:
    return f'{safe_eval(expression):.4f}'


def scripted_reasoner(transcript: str) -> str:
    """Stand in for an LLM so this example stays runnable and repeatable."""
    if 'Observation:' not in transcript:
        return 'Thought: I need the trusted height in meters.\nAction: lookup("eiffel tower height meters")'
    if '330' in transcript and '3.28084' not in transcript:
        return 'Thought: I need the unit conversion factor.\nAction: lookup("meters to feet")'
    if '3.28084' in transcript and '1082.6772' not in transcript:
        return 'Thought: I can now calculate meters to feet.\nAction: calculate("330 * 3.28084")'
    return 'Thought: I have the facts and calculation.\nFinal Answer: The Eiffel Tower is about 1,083 feet tall.'


def run_react(question: str, max_steps: int = 5) -> str:
    tools: dict[str, Callable[[str], str]] = {
        'lookup': lookup,
        'calculate': calculate,
    }
    transcript = f'Question: {question}\n'

    for _ in range(max_steps):
        response = scripted_reasoner(transcript)
        transcript += response + '\n'

        if FINAL_RE.search(response):
            return transcript

        match = ACTION_RE.search(response)
        if not match:
            raise RuntimeError(f'Could not parse action from: {response}')

        tool_name, argument = match.groups()
        if tool_name not in tools:
            raise RuntimeError(f'Tool is not allow-listed: {tool_name}')

        transcript += f'Observation: {tools[tool_name](argument)}\n'

    raise RuntimeError('ReAct loop stopped before a final answer')


if __name__ == '__main__':
    print(run_react('How tall is the Eiffel Tower in feet?'))
```

The harness shows the minimum safety shape. The model does not execute arbitrary code; it emits an action string that the application parses. The application owns the tool registry, the tool arguments, the observation log, and the stopping rule. If those boundaries are weak, ReAct can fail in ordinary ways: looping forever, calling a tool that should not be available, accepting stale observations, or treating an observation as proof when it is only another uncertain input.

A practical ReAct prompt should therefore name the available tools, require one action per turn, require `Final Answer` when no further tool is needed, and tell the model to stop when observations are insufficient. The harness should then enforce those rules instead of trusting the prompt to enforce itself. Once you add durable state, branching, human interrupts, or multiple workers, the same reasoning-and-action loop becomes the conceptual bridge to LangGraph-style agent orchestration.

## Reasoning Effort APIs

Vendor reasoning controls are easy to misunderstand.
They do not make every answer correct.
They do not replace task context, evidence boundaries, or evaluation.

They allocate or guide additional model-side thinking budget before or during response generation.
That budget can improve difficult reasoning tasks, but it also consumes time, tokens, context, and money.
Anthropic's Claude docs describe extended and adaptive thinking modes.

Older manual extended thinking uses a `thinking` object with a `budget_tokens` value.
Current Claude docs also describe adaptive thinking for newer models, where the model decides when and how much to think, guided by effort and query complexity.
Anthropic's prompting guidance explicitly prefers general thinking guidance over overly prescriptive human step lists for many extended-thinking tasks.

OpenAI's reasoning docs describe reasoning models that think before answering and expose controls such as `reasoning.effort` in current API guidance.
The exact supported values vary by model generation, but the practical effect is the same: lower effort can reduce latency and reasoning-token use, while higher effort can spend more compute on difficult tasks.
OpenAI's docs and cookbook examples also emphasize that reasoning tokens may be hidden from the user while still consuming context and budget.

Gemini's API docs describe `thinkingBudget` for Gemini 2.5-series models and `thinkingLevel` for Gemini 3 models.
The docs state that `thinkingBudget` guides the number of thinking tokens, that zero can disable thinking for supported models, and that dynamic thinking can let the model adjust budget to request complexity.
They also warn that the model may underflow or overflow the requested budget depending on the prompt.

The API lesson is straightforward.
Reasoning effort is a serving control, not a prompt incantation.
Use it when a task is hard enough that extra model computation is likely to change the outcome.

Avoid it when the task is a simple extraction, formatting job, or lookup.
Measure both quality and cost before making it the default.

| Provider surface | What you control | What it buys | What it costs | Prompt implication |
|---|---|---|---|---|
| Claude extended or adaptive thinking | Thinking mode, budget, or effort depending on model | More internal reflection for hard tasks | Latency, output or thinking budget, cached thinking considerations | Prefer high-level goals and criteria before prescriptive step lists |
| OpenAI reasoning effort | Model-native effort level for reasoning models | More or less hidden reasoning compute | Reasoning tokens, context use, latency, price | Keep visible prompt focused on task, evidence, and final answer contract |
| Gemini thinking budget or level | Thinking tokens or model-specific thinking level | Guided reasoning budget for Gemini thinking models | Token budget variance, latency, state handling complexity | Treat budget as a hint and evaluate actual outputs |

### When Reasoning Effort Pays Off

Reasoning effort pays off when the model needs to maintain several constraints, explore alternatives, or verify a derived answer.
Examples include mathematical derivations, nontrivial code design, multi-step planning, tool-heavy agent work, and decisions with tradeoffs.
It is especially useful when the final answer should be short but the internal search is hard.

Reasoning effort does not pay off when the answer is already obvious from context.
If a user asks for the value of a visible field, extra thinking is waste.
If a prompt asks for a JSON conversion, structured output or schema validation matters more than hidden reasoning.

If a retrieval step returns the exact answer, cite the source instead of spending a large reasoning budget.
Use a budget ladder.
Start with the cheapest prompt and model setting that plausibly solves the task.

Escalate to a scaffold, native reasoning effort, self-consistency, or search only after you observe failures.
Record the failure mode that justified escalation.
That habit keeps prompt libraries from accumulating expensive rituals nobody can defend.

### Cost Implications

Reasoning effort affects cost in three places.
First, hidden or thinking tokens may be billable or may count against generation limits depending on provider policy.
Second, longer reasoning increases wall-clock latency, which can break user expectations or service timeouts.

Third, thinking state can consume context or cache budget, reducing how much room remains for evidence and tool results.
Cost also affects evaluation.
If you test only the highest reasoning setting, you may ship a workflow that is too expensive for routine use.

If you test only the cheapest setting, you may miss the model's real capability on hard cases.
A good eval includes cheap, medium, and expensive settings on a representative sample.
The result should be a routing rule, not one global setting.

For example, route simple extraction to direct prompts, route medium diagnostic tasks to structured decomposition, and route high-risk multi-step tasks to reasoning effort plus verifier.
That is more operationally honest than telling every prompt to think harder.
It also makes cost visible to reviewers.

## Anti-Patterns and Decision Rules

The first anti-pattern is forcing CoT on simple lookups.
If the answer is in the source text, ask for the exact answer and source location.
A chain-of-thought scaffold gives the model more room to paraphrase, misread, or invent a connection.

The right verification is citation, not more reasoning.
The second anti-pattern is forcing CoT on a true reasoning model without testing.
The model's native hidden trace may be better than your prompt-level path.

If you need auditability, ask for a concise reasoning summary, assumptions, evidence, and checks.
Do not automatically demand a long visible scratchpad.
The third anti-pattern is using "explain your reasoning" as a quality tag.

The phrase changes presentation more reliably than correctness.
It can bias the answer toward a plausible story, especially when the model already guessed the conclusion.
Ask for the specific reasoning artifact instead: constraints, subproblems, candidates, evidence, verifier findings, or rejected alternatives.

The fourth anti-pattern is hiding the final answer inside the reasoning.
This makes automated extraction, human review, and self-consistency voting harder.
Always separate final answer from reasoning summary or checks.

For repeated workflows, make the final field machine-readable.
The fifth anti-pattern is using self-consistency without an extraction rule.
If each sample formats the answer differently, the vote becomes manual interpretation.

Define the answer marker, normalization rule, sample count, temperature, and tie-breaker before running the samples.
Otherwise, you cannot tell whether the method improved reasoning or just produced more text to choose from.
The sixth anti-pattern is treating the verifier as independent when it is not.

If the verifier receives the same vague criteria, same misleading context, and same broad role as the generator, it may bless the same error.
Make verification narrower, criteria-based, and preferably separated by role, model, or tool.
The seventh anti-pattern is turning every hard prompt into Tree-of-Thoughts.

Search-based reasoning is expensive and needs branch scoring.
If you cannot define a branch, score, and stopping rule, you probably do not have ToT.
You have a request for multiple drafts.

The eighth anti-pattern is preserving old scaffolds after a model upgrade.
Prompt libraries often encode workarounds for previous models.
When you move to a reasoning model or change API effort settings, rerun prompt comparisons.

Delete the scaffolds that no longer earn their keep.

### Decision Checklist

Ask seven questions before adding reasoning machinery.
The answer decides the pattern.

```text
1. Is the answer directly present in trusted context?
   Use extraction with citation.

2. Does correctness depend on external facts, calculations, or system
   state the model should not invent from memory?
   Use ReAct: interleave reasoning with allow-listed tool actions and
   observations, under a harness with iteration limits.

3. Does the task require several dependent steps?
   Use decomposition or plan-and-execute.

4. Does the task have one objective final answer but fragile paths?
   Use self-consistency or a verifier.

5. Does the model family already support native reasoning effort?
   Try effort controls before writing a rigid visible scratchpad.

6. Is the wrong answer expensive enough to justify branch search?
   Use Tree-of-Thoughts with branch scoring and stop rules.

7. Can the result be checked by criteria, tests, or evidence?
   Add a verifier pass before adding more generation.
```

The checklist keeps reasoning design connected to task shape.
It also prevents a common organizational failure: one successful prompt becomes a universal template.
Reasoning prompts should be modular.

A math tutor, incident triage assistant, code reviewer, and policy summarizer do not need the same thinking scaffold.

## Did You Know?

- Kojima et al.'s zero-shot CoT paper made one short phrase famous, but the paper's broader lesson was that prompting can elicit latent reasoning behavior without task-specific examples.
- Self-consistency is a decoding and selection strategy, not merely a longer prompt; it needs multiple sampled paths and a rule for choosing the final answer.
- Least-to-Most prompting is most useful when the subproblem answers actually feed later subproblems, which makes the intermediate work a dependency chain rather than decoration.
- Vendor thinking budgets and reasoning effort controls can improve hard tasks, but they are also cost controls because hidden reasoning may consume tokens, context, latency, or cache budget.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---|---|---|
| Adding "think step by step" to every prompt | The phrase is memorable and feels rigorous even when the task is a lookup | Use direct extraction for simple tasks and reserve CoT probes for observed multi-step failures |
| Keeping an old CoT scaffold after upgrading to a reasoning model | The prompt library preserves compatibility workarounds from the previous model | Re-run direct, scaffolded, and reasoning-effort variants after every model change |
| Asking for full reasoning when a summary is enough | Reviewers want confidence but receive a long scratchpad they will not audit | Ask for final answer, key evidence, assumptions, and one verification check |
| Using few-shot CoT examples with mismatched style | Examples teach verbosity, assumptions, or format along with the reasoning pattern | Keep examples short, representative, correct, and aligned with the production output contract |
| Running self-consistency without normalization | The vote is based on human interpretation rather than a reproducible answer field | Define the final-answer marker, normalization rule, sample count, and tie-breaker |
| Letting decomposition invent missing evidence | The model fills unknown subproblems to keep the sequence moving | Require each subproblem to mark missing inputs and stop when evidence is insufficient |
| Treating a verifier prompt as independent by default | The verifier shares the generator's context, model bias, and vague criteria | Give the verifier explicit criteria, a narrow role, and tool or model separation when risk is high |
| Using Tree-of-Thoughts without branch scoring | The prompt asks for many ideas but never controls search | Define branch generation, scoring criteria, pruning, max depth, and stop conditions |

## Quiz

<details>
<summary>1. A prompt asks a model to extract the expiration date from a pasted license. Should you add "Let's think step by step"?</summary>

No. This is a direct extraction task. The better prompt asks for the exact date and the source line or field where it appears. Chain-of-thought adds latency and gives the model more room to paraphrase or infer. If the source is ambiguous, ask for "date candidates and why each might be the expiration date" rather than a generic step-by-step scaffold.
</details>

<details>
<summary>2. A non-reasoning model fails a three-step arithmetic word problem by jumping to the wrong operation. Which CoT variant is the cheapest first probe?</summary>

Use a small zero-shot CoT-style cue, but make it task-specific: "work through the quantities carefully, then return Final and Check." If that helps, replace the generic cue with a clearer task contract or few-shot example. Do not jump directly to self-consistency or Tree-of-Thoughts until you know one scaffolded path still fails.
</details>

<details>
<summary>3. A team migrates from an older chat model to a model with native thinking budget, and its old step-by-step scaffold starts reducing answer quality. What should they test?</summary>

They should compare the direct task contract, a concise reasoning-summary prompt, and the provider-native reasoning effort or thinking setting. The old scaffold may be constraining the new model's internal reasoning path. Keep evidence boundaries and output criteria, but remove prescriptive steps unless they produce measurable gains on the team's eval set.
</details>

<details>
<summary>4. When does Least-to-Most prompting beat a generic chain-of-thought instruction?</summary>

Least-to-Most is better when the task can be decomposed into smaller subproblems and each solved subproblem becomes input to later work. The value is the dependency chain. If the subproblems do not feed the solution, the prompt only produced a longer explanation, not a stronger reasoning process.
</details>

<details>
<summary>5. Why can self-consistency still choose the wrong answer?</summary>

Self-consistency samples multiple paths and selects a common final answer, but common does not mean correct. If every sample shares the same false assumption, prompt ambiguity, or misleading context, the vote can amplify the error. Use normalization, tie-break rules, and a verifier when the task has constraints that can be checked.
</details>

<details>
<summary>6. What makes a verifier prompt stronger than asking the original answer to "double-check"?</summary>

A strong verifier has a narrow role, receives the original task and proposed answer, and checks against explicit external criteria. It returns findings tied to criteria before repair. "Double-check" is weak because it often asks the same model, with the same broad context, to produce another helpful answer rather than inspect a contract.
</details>

<details>
<summary>7. When is Tree-of-Thoughts worth the budget?</summary>

It is worth considering when the task is hard, branchy, and checkable. There must be several plausible paths, a way to score branches, and enough risk in a wrong answer to justify multiple calls. Without branch scoring and stopping rules, ToT becomes an expensive request for many drafts.
</details>

<details>
<summary>8. What do reasoning effort and thinking budget APIs actually control?</summary>

They guide or allocate model-side thinking work, often through hidden reasoning tokens, structured thinking blocks, adaptive effort, or thinking token budgets. They do not guarantee correctness, replace context, or remove the need for verification. Higher settings can improve hard tasks, but they can also increase latency, token use, context pressure, and cost.
</details>

## Hands-On Exercise: Compare Three Reasoning Strategies

Exercise scenario: you are designing a prompt for a support assistant that triages a failed deployment from limited evidence.
The task is intentionally small enough to run by hand, but realistic enough to show differences between direct answering, decomposition, and verification.
Use the same model for all three strategies unless you are explicitly testing provider-native reasoning effort.

Keep the temperature, context, and output format stable so the reasoning strategy is the main variable.

### Source Task

```text
Evidence:
- A Deployment named web was updated at 10:20 UTC.
- New Pods are stuck in ImagePullBackOff.
- The image field is registry.example.com/web:2026-05-25.
- The previous image tag was registry.example.com/web:2026-05-24.
- No container logs are available because the container never starts.
- The engineer has read-only namespace access.

Question:
What is the most likely next diagnostic step, and what should the assistant avoid recommending?
```

### Strategy A: Direct Prompt

```text
Task: Answer the deployment triage question using only the evidence below.

Output:
- Next diagnostic step
- Reason
- Avoid recommending
```

Run the prompt once.
Record whether the answer stays inside the evidence, whether it avoids logs-based claims, and whether it respects read-only access.
This is the baseline.

If it passes, a more expensive reasoning scaffold must earn its place.

### Strategy B: Decomposition Prompt

```text
Task: Answer the deployment triage question using only the evidence below.

First decompose the evidence into:
- Observed facts
- Inferences supported by those facts
- Missing information
- Actions allowed under read-only access

Then answer:
- Next diagnostic step
- Reason
- Avoid recommending
```

Run the prompt once.
Compare it with the direct prompt.
Look for better evidence separation, not just more words.

If the decomposition invents registry state or suggests a write action, mark it as a failure.

### Strategy C: Draft Plus Verifier

```text
Generator task:
Answer the deployment triage question using only the evidence below.
Return next diagnostic step, reason, and avoid recommending.

Verifier task:
Check the proposed answer against these criteria:
- Uses only supplied evidence
- Does not claim container logs exist
- Does not recommend mutating cluster state
- Names a read-only next diagnostic step
Return pass/fail and findings.
```

Run the generator, then run the verifier on the generator's answer.
If the verifier finds a problem, repair only the failing field and run the verifier again.
Do not let the verifier silently rewrite the whole answer.

### Comparison Table

Fill this table with your outputs.

| Strategy | Correct next step? | Respects evidence? | Respects read-only access? | Cost and latency | Library decision |
|---|---|---|---|---|---|
| Direct |  |  |  |  |  |
| Decomposition |  |  |  |  |  |
| Draft plus verifier |  |  |  |  |  |

### Success Criteria

- [ ] You ran the same source task with a direct prompt, a decomposition prompt, and a draft-plus-verifier workflow.
- [ ] You compared final answers against evidence use, read-only access, missing information, and cost rather than judging by which response sounded smartest.
- [ ] You identified at least one case where visible reasoning helped, was redundant, or made the answer worse.
- [ ] You wrote a one-paragraph recommendation that designs reasoning-eliciting prompts for diagnosis, planning, and decision tasks without turning the reusable support prompt into a generic chain-of-thought ritual.
- [ ] You named the next evaluation you would run before applying the chosen strategy to production incidents.

### Expected Analysis

The direct prompt may already find the correct next diagnostic step: inspect image pull events, image name, tag existence, or registry access with read-only commands.
It should avoid recommending container logs because the evidence says the container never starts.
It should also avoid rollout restarts, image changes, or secret edits because the engineer has read-only namespace access.

The decomposition prompt is better only if it improves grounding.
A strong decomposition will separate observed facts from likely inference: ImagePullBackOff points toward image reference, registry authentication, pull policy, or network path rather than application runtime failure.
A weak decomposition will pad the answer with a long incident story.

The verifier workflow is strongest when the generator makes a subtle violation.
For example, if the generator says "check logs" or "restart the deployment," the verifier criteria should catch it.
The workflow is slower, but the extra pass may be justified for support prompts that repeatedly affect operator behavior.

## Sources

- [Large Language Models are Zero-Shot Reasoners](https://arxiv.org/abs/2205.11916) - Kojima et al.; verified source for zero-shot CoT and the "Let's think step by step" cue.
- [Self-Consistency Improves Chain of Thought Reasoning in Language Models](https://arxiv.org/abs/2203.11171) - Wang et al.; verified source for multiple sampled reasoning paths and answer selection.
- [Least-to-Most Prompting Enables Complex Reasoning in Large Language Models](https://arxiv.org/abs/2205.10625) - Zhou et al.; verified source for decomposition into simpler subproblems.
- [Tree of Thoughts: Deliberate Problem Solving with Large Language Models](https://arxiv.org/abs/2305.10601) - Yao et al.; verified source for search over intermediate thoughts.
- [ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629) - Yao et al.; verified source for interleaving reasoning traces with tool actions and observations.
- [Chain-of-Thought Prompting Elicits Reasoning in Large Language Models](https://arxiv.org/abs/2201.11903) - Wei et al.; verified background source for few-shot CoT examples.
- [Plan-and-Solve Prompting: Improving Zero-Shot Chain-of-Thought Reasoning by Large Language Models](https://arxiv.org/abs/2305.04091) - Wang et al.; verified background source for planning before solving.
- [Let's Verify Step by Step](https://arxiv.org/abs/2305.20050) - Lightman et al.; verified background source for process and outcome verification concerns.
- [DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning](https://arxiv.org/abs/2501.12948) - verified background source for reasoning-model training, cross-linked here only to distinguish inference-time prompting from model training.
- [Anthropic extended thinking docs](https://platform.claude.com/docs/en/build-with-claude/extended-thinking) - verified vendor documentation for Claude thinking modes and token budgets.
- [Anthropic Claude prompting best practices: thinking capabilities](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices#leverage-thinking-and-interleaved-thinking-capabilities) - verified vendor guidance on thinking prompts and adaptive thinking behavior.
- [OpenAI reasoning models docs](https://platform.openai.com/docs/guides/Reasoning?api-mode=response) - verified vendor documentation for reasoning models and reasoning effort.
- [OpenAI latest model guidance: using reasoning models](https://developers.openai.com/api/docs/guides/latest-model#using-reasoning-models) - verified vendor guidance for current reasoning controls and routing considerations.
- [Gemini thinking docs](https://ai.google.dev/gemini-api/docs/thinking) - verified vendor documentation for `thinkingBudget`, dynamic thinking, and Gemini thinking controls.

## Next Module

Continue to [Prompt Safety and Evaluation in the section plan](../#planned-modules), where the verification patterns from this module become safety gates, evaluation datasets, and regression tests for reasoning-heavy prompts.

---
title: "Evaluation, Iteration, and Shipping v1"
slug: ai/ai-building/module-1.4-evaluation-iteration-and-shipping-v1
sidebar:
  order: 4
---

> **AI Building** | Complexity: `[MEDIUM]` | Time: 40-55 min | Prerequisites: AI Building Modules 1.1-1.3, basic prompting, basic JSON, basic command-line usage

## Learning Outcomes

By the end of this module, you will be able to:

- **Design** a small evaluation set that represents the real job an AI feature must perform.
- **Debug** AI output failures by separating task clarity, context quality, output shape, validation, and model choice.
- **Evaluate** whether a v1 AI feature is bounded, reviewable, and safe enough to ship.
- **Iterate** on one variable at a time so each change teaches you something causal.
- **Compare** prompt changes, context changes, validation changes, and model changes using evidence instead of demos.

## Why This Module Matters

A product team ships an AI assistant into its internal support workflow.

In the demo, it looks excellent.

The assistant summarizes tickets cleanly.

It finds the right product area.

It drafts polite responses.

The team celebrates because the assistant worked on the three examples everyone practiced with.

Then Monday morning arrives.

A customer reports a billing failure, but includes screenshots, partial account IDs, and a long complaint thread.

The assistant summarizes the emotion well, misses the billing detail, and routes the ticket to the wrong queue.

A second ticket mentions an outage and a refund request.

The assistant treats the refund request as the main issue, even though the outage is urgent.

A third ticket includes copied logs.

The assistant invents an explanation because the logs are unfamiliar.

The system did not suddenly become worse.

The team finally saw normal inputs.

That is the moment many AI projects fail.

Not because the model is useless.

Not because the team lacked intelligence.

They failed because they shipped impressions instead of evaluation.

This module teaches the discipline that prevents that failure.

Evaluation is how a team learns what the system can do.

Iteration is how a team improves it without guessing.

Shipping v1 is how a team delivers value without pretending the system is finished.

The senior habit is simple to state and hard to practice:

Change one thing at a time, measure it against representative examples, and ship only inside the boundary you can explain.

## Start With The Smallest Honest Question

Before tuning the system, ask:

> What job must this feature do well enough to be useful?

Not:

- “How do I make it amazing?”
- “How do I make it fully autonomous?”
- “How do I make it handle every possible user request?”
- “How do I make the model sound more confident?”

Those questions are too broad for v1.

They invite vague success.

They encourage impressive demos.

They hide failure modes.

A better v1 question is narrow enough to test.

A useful v1 question has a user, an input type, a task, and a review boundary.

For example:

> Can this feature classify incoming support tickets into one of five queues using only the ticket subject and body, while showing the sentence that justifies the classification?

That question is testable.

It tells you what input the system receives.

It tells you what output the system must produce.

It tells you how many labels are allowed.

It tells you what evidence the system must provide.

It also tells you what the system is not allowed to do.

It is not resolving the ticket.

It is not sending the reply.

It is not changing customer data.

It is not acting without review.

That boundary is not a weakness.

That boundary is what makes v1 shippable.

A vague AI feature creates vague responsibility.

A bounded AI feature creates visible work.

### From Idea To v1 Contract

Use a v1 contract before you write prompts.

A v1 contract is a small agreement between the builder, the reviewer, and the user.

It says what the feature does.

It says what it refuses to do.

It says how people will judge output quality.

It says what happens when the feature is uncertain.

A simple v1 contract looks like this:

| Contract Field | Good v1 Example | Weak v1 Example |
|---|---|---|
| User job | Route support tickets to the right queue faster | Help support with tickets |
| Input | Ticket subject and body only | Any customer conversation |
| Output | One queue label, confidence note, supporting quote | Helpful analysis |
| Success condition | Correct queue on at least most representative examples, with no unsupported quote | Looks useful in demos |
| Human review | Triage owner accepts or changes the queue before routing | The system routes directly |
| Refusal behavior | Mark as `needs_human_review` when no evidence supports a queue | Guess the most likely queue |

The weak version is tempting because it feels flexible.

The strong version is useful because it creates a testable surface.

A senior builder does not ask whether the feature feels intelligent.

A senior builder asks whether the feature performs a defined job under known constraints.

### Active Check: Tighten The Job

Your team proposes this feature:

> “Use AI to handle customer escalations.”

Before reading further, rewrite that into a testable v1 contract.

Include the user, input, output, review boundary, and refusal behavior.

A stronger version might be:

> “For new customer escalation emails, draft a two-paragraph internal summary for the escalation manager, including the requested action, the affected account, and a quote from the email for each claim. If any field is missing, mark it as `unknown` instead of guessing.”

Notice what changed.

The feature no longer handles the escalation.

It prepares a reviewable summary.

It names required fields.

It requires evidence.

It defines uncertainty.

That narrower version is much easier to evaluate.

It is also much easier to ship responsibly.

## Evaluation Does Not Need To Be Fancy

For a beginner-friendly first system, evaluation can be simple:

- 10-20 representative examples
- expected output shape
- pass/fail criteria
- notes on failure patterns

The point is not statistical perfection.

The point is to stop relying on cherry-picked impressions.

A tiny evaluation set is not a scientific benchmark.

It is a steering wheel.

It tells you whether a change moved the system in the direction you intended.

It helps you notice regression.

It gives reviewers shared evidence.

It forces the team to define quality before arguing about optimization.

The first evaluation set should contain ordinary examples.

Not only clean examples.

Not only dramatic examples.

Not only examples that make the model look good.

You want the messy middle because that is where the feature will live.

A useful first evaluation set usually includes:

- easy successes
- normal cases
- ambiguous cases
- malformed inputs
- edge cases with high business risk
- cases where the correct answer is “I do not know”
- cases where the model must cite evidence
- cases where the model must refuse unsupported action

The evaluation set should be small enough that a human can inspect it.

If nobody reads the outputs, the evaluation is theater.

If nobody writes down why an output failed, iteration becomes guesswork again.

### What Representative Means

Representative does not mean random.

Representative means the examples resemble the work the system will actually face.

If the feature handles support tickets, include real support ticket shapes.

If the feature summarizes meetings, include meetings with interruptions, action items, decisions, and unclear ownership.

If the feature answers document questions, include questions where the answer is absent.

If the feature extracts fields, include missing fields, repeated fields, and conflicting fields.

A representative set should include the failure modes you fear most.

That is not pessimism.

That is responsible engineering.

### A Minimal Eval Record

One evaluation record can be written as JSON.

The format below is deliberately plain.

It is not tied to a specific evaluation framework.

It is just structured enough to compare expected and actual behavior.

```json
{
  "id": "ticket-routing-001",
  "input": {
    "subject": "Refund requested after duplicate billing",
    "body": "I was charged twice for my April invoice. Please refund the duplicate charge."
  },
  "expected": {
    "queue": "billing",
    "required_evidence": "charged twice"
  },
  "risk": "low",
  "notes": "Straightforward billing ticket."
}
```

This record gives the system an input.

It gives the reviewer an expected result.

It gives the evaluator evidence to check.

It gives the team a place to record risk.

The exact schema can vary.

The habit matters more than the tool.

### Pass And Fail Criteria

A pass/fail rule should be concrete enough that two reviewers usually agree.

Weak criteria sound like this:

- “Good summary.”
- “Helpful answer.”
- “Mostly correct.”
- “Looks reasonable.”
- “User would like it.”

Stronger criteria sound like this:

- “Output includes the requested action, the affected account, and no unsupported claims.”
- “Classification uses only one label from the approved label set.”
- “Answer cites a document excerpt that contains the answer.”
- “If evidence is missing, output uses `unknown` instead of guessing.”
- “The draft does not perform the action; it only prepares text for human review.”

AI systems fail in subtle ways.

Pass criteria need to expose those failures.

A beautiful answer with one unsupported claim is not a pass if groundedness is required.

A confident classification is not a pass if the label is outside the allowed list.

A useful draft is not a pass if it silently changes the user's intent.

### Active Check: Design One Failure Case

Choose one AI feature idea you have seen recently.

Now write one evaluation example where the correct behavior is refusal, uncertainty, or escalation.

The point is to test whether the system knows when not to answer.

A support assistant might receive:

> “The customer wants a refund, but the account ID is missing.”

The expected output might be:

> “queue: billing, account_id: unknown, next_step: ask human for account lookup”

This is a better test than another clean success case.

Clean success proves the happy path.

A refusal case proves the boundary.

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

The loop is small on purpose.

It keeps learning fast.

It makes each improvement attributable.

It prevents the common habit of making five changes, seeing better output, and declaring victory without knowing which change helped.

A team that cannot explain why quality improved cannot reliably improve it again.

A team that cannot identify what caused a regression cannot safely ship.

### The One-Variable Rule

Change one variable per iteration.

A variable can be:

- the task definition
- the examples in the evaluation set
- the context retrieved for the model
- the prompt instruction
- the output schema
- the validation rule
- the review workflow
- the model choice
- a model parameter
- a fallback path

Changing one variable does not mean making one word edit.

It means making one kind of intervention.

For example, you may rewrite the prompt to clarify citation requirements.

That is one intervention.

You should not rewrite the prompt, add retrieval, change the label set, and switch models in the same iteration.

If results improve, you will not know why.

If results worsen, you will not know what to undo.

### Worked Iteration Scenario: Ticket Routing

Here is a fully worked scenario.

The team is building a v1 support-ticket router.

The system must output:

- one queue label
- one supporting quote from the ticket
- `needs_human_review` when evidence is insufficient

The allowed queues are:

- `billing`
- `technical_support`
- `account_access`
- `sales`
- `needs_human_review`

The team starts with this input:

```json
{
  "subject": "Charged twice and cannot access invoice",
  "body": "I was charged twice this month. I also cannot open the invoice page because it says permission denied. Please fix this today."
}
```

The expected behavior is not obvious at first.

There are two issues.

Billing is important.

Access is also important.

The team decides that duplicate charge takes priority because money-impacting tickets route to billing first.

The expected output becomes:

```json
{
  "queue": "billing",
  "supporting_quote": "I was charged twice this month.",
  "secondary_issue": "account_access"
}
```

Now the team runs the first prompt.

```text
Classify this support ticket into the best queue:
billing, technical_support, account_access, or sales.

Ticket:
Subject: Charged twice and cannot access invoice
Body: I was charged twice this month. I also cannot open the invoice page because it says permission denied. Please fix this today.
```

The model returns:

```json
{
  "queue": "account_access",
  "reason": "The user cannot open the invoice page because of permission denied."
}
```

This is a failure.

It is not a random failure.

It reveals a priority problem.

The prompt listed labels but did not explain conflict handling.

The model selected the most concrete technical symptom.

The team records the failure:

| Iteration | Input | Failure | Diagnosis | Change | Result |
|---|---|---|---|---|---|
| baseline | duplicate charge plus invoice access error | routed to `account_access` | no priority rule for mixed tickets | add priority rule only | pending |

The team changes one thing.

They do not change the model.

They do not add retrieval.

They do not change the output schema.

They only add a priority rule.

```text
Classify this support ticket into one queue:
billing, technical_support, account_access, sales, or needs_human_review.

Priority rule:
If the ticket includes a billing problem and another problem, choose billing first.
If evidence is insufficient, choose needs_human_review.

Return JSON with:
queue
supporting_quote
secondary_issue

Ticket:
Subject: Charged twice and cannot access invoice
Body: I was charged twice this month. I also cannot open the invoice page because it says permission denied. Please fix this today.
```

The model returns:

```json
{
  "queue": "billing",
  "supporting_quote": "I was charged twice this month.",
  "secondary_issue": "account_access"
}
```

This is a success on the target example.

The team now runs the same changed prompt against the rest of the evaluation set.

That matters.

A fix for one example can break another example.

The next example is:

```json
{
  "subject": "Cannot log in after password reset",
  "body": "I reset my password, but the login page still rejects it. I do not have any billing issue."
}
```

The model returns:

```json
{
  "queue": "account_access",
  "supporting_quote": "the login page still rejects it",
  "secondary_issue": null
}
```

That is still correct.

The priority rule did not over-route to billing.

Now the team can say something precise:

> Adding a billing-first conflict rule fixed the mixed billing/access example without breaking the tested account-access example.

That is real learning.

It is not just better output.

It is a causal improvement.

### What The Team Did Not Do

The team did not immediately switch to a larger model.

The team did not add more examples before diagnosing the visible failure.

The team did not rewrite the whole prompt in a new style.

The team did not add a second classifier.

The team did not hide the failure because the answer looked reasonable.

They inspected the failure.

They named the cause.

They made one targeted change.

They reran the example.

They checked for regression.

That is the v1 loop.

### Why This Scenario Matters

The failure was not that the model was “bad.”

The failure was that the task was underspecified.

The model could not infer the business priority.

The fix belonged in the task definition, not in the model choice.

This is common.

Many early AI failures are not model failures.

They are product-definition failures.

Senior practitioners look for missing task rules before blaming model capability.

### Active Check: Diagnose Before Fixing

Suppose the same ticket router returns this output:

```json
{
  "queue": "billing",
  "supporting_quote": "Please fix this today.",
  "secondary_issue": "account_access"
}
```

The queue is correct, but the quote is weak.

What should you change first?

Do not answer “use a better model.”

A better first change is to clarify the evidence rule:

> The supporting quote must contain the phrase or sentence that directly proves the selected queue.

That diagnosis targets the failure.

The failure is not classification.

The failure is evidence selection.

Changing the model would make the experiment noisier.

## What To Change First

Good order of operations:

1. clarify the task
2. improve context
3. improve output shape
4. add validation
5. only then change model or more advanced settings

This is more effective than immediately reaching for a bigger model.

The order exists because some fixes remove entire classes of confusion.

If the task is vague, more context may not help.

If the context is missing, a stricter JSON schema will not create facts.

If the output shape is unclear, validation will be hard to write.

If validation is absent, a stronger model can still produce unsafe output.

The hierarchy is not a law.

It is a debugging default.

Start with the cheapest explanation that would account for the failure.

Then move outward.

### Scenario: Why The Priority Order Matters

A team builds an AI feature that answers questions about an internal deployment runbook.

The user asks:

> “Can I restart the payment worker during business hours?”

The system answers:

> “Yes, restarting the worker is usually safe if you monitor logs afterward.”

The expected answer is:

> “No. The runbook says payment workers must be restarted only during the approved maintenance window unless incident command approves an exception.”

The team wants to fix the failure.

There are several possible changes.

They could use a larger model.

They could add a stricter answer format.

They could add validation.

They could improve retrieval.

They could clarify the task.

A weak iteration plan jumps straight to the model.

A stronger plan follows the priority order.

### Step One: Clarify The Task

The current task says:

```text
Answer the user's question using the runbook.
```

That sounds reasonable.

It is still underspecified.

It does not say what to do when the runbook contains a policy restriction.

It does not say whether safety constraints override general advice.

It does not require a quote.

The first fix clarifies the task:

```text
Answer the user's question using only the runbook excerpt.
If the runbook includes a restriction, state the restriction before any operational advice.
Include one exact quote from the excerpt.
If the excerpt does not answer the question, say "not enough information."
```

The team reruns the example with the same model and same context.

The answer becomes:

```json
{
  "answer": "No. The runbook restricts payment worker restarts to the approved maintenance window unless incident command approves an exception.",
  "quote": "Payment workers must be restarted only during the approved maintenance window unless incident command approves an exception.",
  "status": "answered"
}
```

The failure is fixed.

The model was not the first problem.

The task was too loose.

### Step Two: Improve Context When Task Clarity Is Not Enough

Now consider another input:

> “Who can approve an exception?”

The system answers:

```json
{
  "answer": "Incident command can approve an exception.",
  "quote": "unless incident command approves an exception",
  "status": "answered"
}
```

That answer may be incomplete.

The runbook excerpt might not define who incident command is.

If the full documentation has a separate section defining incident command, the next change is context.

The task is already clear.

The missing piece is information.

The team improves retrieval so the policy definition section is included with the restart section.

They rerun the same input.

Now the system can answer with the correct owner.

This is the second priority: improve context.

### Step Three: Improve Output Shape

Suppose the model now gives correct prose but reviewers struggle to audit it.

The answer is a paragraph.

The quote is embedded awkwardly.

The status is inconsistent.

Now the task and context may be good, but the output shape is weak.

The team changes the output to a schema:

```json
{
  "status": "answered | not_enough_information",
  "decision": "yes | no | conditional | unknown",
  "answer": "string",
  "supporting_quote": "string",
  "review_note": "string"
}
```

That schema does not make the model smarter.

It makes review easier.

It also makes validation possible.

### Step Four: Add Validation

Once the output shape is stable, validation becomes useful.

Validation can check that:

- `status` is one of the allowed values
- `decision` is one of the allowed values
- `supporting_quote` is not empty when `status` is `answered`
- `answer` does not claim certainty when `status` is `not_enough_information`
- the quote appears in the supplied context
- the output is parseable JSON

Validation catches broken outputs before a person trusts them.

It also helps you separate formatting failures from reasoning failures.

### Step Five: Change Model Or Advanced Settings

Only after the task, context, shape, and validation are reasonable should model choice become the main lever.

There are legitimate reasons to change models.

A stronger model may handle more complex reasoning.

A smaller model may be cheaper and sufficient.

A model with larger context may support longer documents.

A model with better structured-output behavior may reduce parsing failures.

The point is not “never change models.”

The point is “do not use model choice to avoid diagnosis.”

Model changes are more expensive to interpret.

They can improve one behavior while changing others.

They also hide missing product rules.

### The Priority Ladder In Practice

Here is the same failure viewed through the hierarchy:

| Observed Failure | First Suspect | Better First Change | Why |
|---|---|---|---|
| Answer violates business priority | Task clarity | Add explicit priority rule | The model cannot infer private policy |
| Answer lacks required fact | Context | Retrieve or supply the missing source | The model cannot cite absent information |
| Answer is correct but hard to review | Output shape | Use a stable schema | Review needs predictable fields |
| Answer has invalid JSON | Validation and schema | Validate and retry or fail closed | Broken structure blocks automation |
| Answer requires complex judgment after other fixes | Model choice | Compare models on the same eval set | Capability may now be the constraint |

This table is not just a checklist.

It is a debugging strategy.

It protects you from wasting time on expensive changes before cheap causes are ruled out.

### Active Check: Pick The First Change

Your document Q&A assistant gives this answer:

> “The policy allows contractors to access staging.”

The retrieved context says:

> “Contractors may access staging only after manager approval and security training.”

The output is fluent.

The quote is missing.

The answer drops the condition.

What should you change first?

A good first change is task clarity:

> Require the answer to preserve conditions and quote the exact sentence that contains the condition.

A good second change is output shape:

> Add separate fields for `decision`, `conditions`, and `supporting_quote`.

A model switch is not the first move because the supplied context already contains the answer.

The failure is instruction and structure.

## Build A Runnable Eval Harness

A v1 eval can start as a small script.

You do not need a complex platform to learn from examples.

You need repeatable inputs.

You need visible expectations.

You need consistent scoring.

The following harness does not call an AI model.

It simulates evaluation mechanics using saved outputs.

That makes it runnable anywhere.

It also teaches the shape of a useful evaluation loop.

Create a file named `eval_cases.jsonl`:

```json
{"id":"ticket-001","expected_queue":"billing","required_evidence":"charged twice","actual":{"queue":"billing","supporting_quote":"I was charged twice this month."}}
{"id":"ticket-002","expected_queue":"account_access","required_evidence":"login page still rejects it","actual":{"queue":"account_access","supporting_quote":"the login page still rejects it"}}
{"id":"ticket-003","expected_queue":"needs_human_review","required_evidence":"missing account ID","actual":{"queue":"billing","supporting_quote":"customer wants a refund"}}
```

Create a file named `run_eval.py`:

```python
import json
from pathlib import Path


def evidence_matches(required: str, quote: str) -> bool:
    return required.lower() in quote.lower()


def score_case(case: dict) -> dict:
    actual = case["actual"]
    queue_ok = actual.get("queue") == case["expected_queue"]
    quote_ok = evidence_matches(
        case["required_evidence"],
        actual.get("supporting_quote", ""),
    )
    passed = queue_ok and quote_ok
    return {
        "id": case["id"],
        "passed": passed,
        "queue_ok": queue_ok,
        "quote_ok": quote_ok,
        "expected_queue": case["expected_queue"],
        "actual_queue": actual.get("queue"),
    }


def main() -> None:
    path = Path("eval_cases.jsonl")
    cases = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    results = [score_case(case) for case in cases]
    passed = sum(1 for result in results if result["passed"])

    for result in results:
        status = "PASS" if result["passed"] else "FAIL"
        print(
            f"{status} {result['id']} "
            f"queue_ok={result['queue_ok']} "
            f"quote_ok={result['quote_ok']} "
            f"expected={result['expected_queue']} "
            f"actual={result['actual_queue']}"
        )

    print(f"\npassed={passed} total={len(results)}")


if __name__ == "__main__":
    main()
```

Run it:

```bash
.venv/bin/python run_eval.py
```

You should see two passes and one failure.

The failure is useful.

It tells the team that `ticket-003` was routed to billing when the expected output was `needs_human_review`.

It also tells the team that the quote did not contain the required evidence.

A real AI eval would call the model before scoring.

This simple harness skips that integration so the scoring idea is easy to inspect.

### Reading Eval Output

A score is a signal, not a verdict.

When an example fails, inspect the reason.

Was the expected answer wrong?

Was the input ambiguous?

Was the system missing context?

Was the output schema too loose?

Was validation too strict?

Did the model ignore an instruction?

Did the task definition omit a business rule?

A failing example can mean the system is wrong.

It can also mean the evaluation needs refinement.

Do not silently edit expected outputs to make the score better.

If expectations change, record why.

Evaluation is part of the product specification.

Changing it should be as deliberate as changing code.

### Eval Notes Are Part Of The Artifact

Keep notes beside results.

A useful eval note names the failure pattern.

Weak note:

> “Bad answer.”

Better note:

> “Routed refund case to billing even though account ID was missing; expected `needs_human_review` because workflow cannot process refund without account lookup.”

The better note teaches the next iteration.

It also helps another reviewer understand the intended behavior.

Over time, notes become a map of product decisions.

They show why the feature behaves as it does.

They also show where risk remains.

### Senior Practice: Separate Quality Gates

A v1 AI feature often needs more than one gate.

Different gates catch different failures.

A small system might use these gates:

| Gate | Catches | Example |
|---|---|---|
| Schema validation | malformed output | missing `queue` field |
| Grounding check | unsupported claims | quote not found in context |
| Policy check | unsafe action | suggests refund without account ID |
| Human review | judgment failures | ambiguous customer intent |
| Regression eval | quality drift | old success case starts failing |

Do not make one gate responsible for everything.

Schema validation cannot judge business policy.

Human review should not waste time fixing invalid JSON.

Regression examples cannot prove all safety properties.

Layered gates make failure visible earlier.

## Inspect Failures Like A Practitioner

Inspection is where the real learning happens.

A passing score can hide weak reasoning.

A failing score can reveal a missing rule.

A confusing score can reveal ambiguity in the product.

Treat each failure as a diagnostic case.

You are not asking, “How do I make this example pass?”

You are asking, “What class of failure does this example represent?”

That question prevents overfitting.

### The Failure Taxonomy

Use a simple taxonomy when reviewing outputs.

| Failure Type | Symptom | Usual First Move |
|---|---|---|
| Task ambiguity | output chooses a reasonable but wrong interpretation | clarify task or priority |
| Missing context | output guesses or gives generic advice | improve retrieval or supplied context |
| Bad evidence | output conclusion is right but quote is weak | tighten evidence rules |
| Shape drift | fields missing or inconsistent | define schema and validation |
| Unsafe action | output exceeds allowed authority | add boundary and review rule |
| Hallucinated detail | output invents facts | require grounding and fail closed |
| Over-refusal | output says unknown when evidence exists | improve context selection or instruction balance |
| Regression | old passing case fails after change | isolate the changed variable |

This taxonomy keeps reviews specific.

Specific diagnosis leads to specific fixes.

Generic frustration leads to random prompt edits.

### Do Not Overfit One Example

When you fix one example, ask whether the fix generalizes.

A bad fix mentions the exact input phrase.

A good fix names the underlying rule.

Bad fix:

```text
If the user says "charged twice and cannot access invoice", choose billing.
```

Good fix:

```text
If a ticket includes both a billing problem and another problem, choose billing first.
```

The bad fix passes one case.

The good fix improves a class of cases.

Overfitting is especially easy with prompts because wording changes are cheap.

Cheap changes still need discipline.

### Compare Before And After

A useful iteration record includes before and after.

At minimum, record:

- date
- evaluation set version
- change made
- examples improved
- examples worsened
- remaining failure pattern
- decision

This does not need to be bureaucratic.

A small table is enough.

| Date | Change | Improved | Worsened | Decision |
|---|---|---|---|---|
| 2026-04-25 | Added billing-first priority rule | mixed billing/access case | none in small set | keep and expand mixed-issue cases |
| 2026-04-25 | Required quote to contain queue evidence | weak quote case | one account case now over-refuses | revise evidence instruction |

The second row is important.

Not every change is clean.

A change can improve evidence quality while increasing refusal.

That does not mean the change is bad.

It means the team must decide which tradeoff is acceptable.

### Active Check: Spot Overfitting

A prompt includes this instruction:

```text
If the ticket mentions "April invoice", route to billing.
```

Why is that risky?

It routes one known example correctly but fails the class of related examples.

A May duplicate charge should still route to billing.

A tax invoice permission issue may not be a billing problem.

The rule is phrase-specific instead of behavior-specific.

A better instruction describes the category:

```text
If the ticket reports a charge, refund, invoice amount, payment failure, or duplicate billing, route to billing unless required account information is missing.
```

That rule is still imperfect.

It is much more likely to generalize.

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

Shipping v1 does not mean shipping a toy.

It means shipping the smallest version that creates real value inside a controlled boundary.

The boundary is the product.

If the feature summarizes tickets for humans, do not silently route tickets.

If the feature drafts replies, do not send them automatically.

If the feature answers document questions, do not answer without source text.

If the feature extracts fields, do not invent missing fields.

If the feature recommends actions, do not execute actions until the review path is mature.

The v1 boundary should match the evidence you have.

Evidence from a small eval set supports a small launch.

It does not support broad autonomy.

### Signs You Are Ready To Ship

- the use case is narrow
- failure modes are visible
- humans can review outcomes where needed
- you have examples that show typical success and typical failure
- the system reduces work instead of adding ambiguity

Those signs are practical.

They do not require perfection.

They require honesty.

A v1 can ship with known limitations.

It should not ship with hidden limitations.

A known limitation can be documented, reviewed, and improved.

A hidden limitation becomes a production surprise.

### Signs You Are Not Ready

- you still cannot describe success in one sentence
- every demo depends on a carefully phrased prompt
- wrong outputs look too plausible to detect
- nobody owns validation
- the system performs actions you cannot comfortably audit

These signs are warnings.

They do not mean the idea is bad.

They mean the boundary is not ready.

Narrow the scope.

Add examples.

Clarify success.

Add review.

Reduce authority.

Then evaluate again.

### Shipping Checklist For v1

Use this checklist before launch.

- [ ] The feature has a one-sentence job statement.
- [ ] The input boundary is clear.
- [ ] The output schema is stable.
- [ ] The allowed actions are explicit.
- [ ] The disallowed actions are explicit.
- [ ] There is a representative evaluation set.
- [ ] There are examples where the system should refuse or escalate.
- [ ] There is a record of at least one iteration.
- [ ] Failure modes are documented.
- [ ] A human review path exists for risky outputs.
- [ ] Validation catches malformed output.
- [ ] Rollback or disablement is possible.
- [ ] Users know the feature is assistive, not authoritative.
- [ ] Ownership for monitoring and follow-up is assigned.

The checklist is intentionally operational.

A feature that cannot be disabled is risky.

A feature nobody monitors will decay.

A feature users misunderstand will be misused.

### The v1 Launch Boundary

A launch boundary should answer four questions.

First, who can use the feature?

Second, what inputs are allowed?

Third, what outputs can the feature produce?

Fourth, what happens when confidence is low or evidence is missing?

For the ticket router, a launch boundary might be:

| Boundary | v1 Decision |
|---|---|
| Users | internal triage team only |
| Inputs | new English-language support tickets with subject and body |
| Outputs | suggested queue, supporting quote, secondary issue |
| Authority | suggestion only; no automatic routing |
| Escalation | `needs_human_review` for missing or conflicting evidence |
| Monitoring | weekly review of failed and overridden suggestions |

This launch is not glamorous.

It is shippable.

It creates value by reducing triage effort.

It avoids pretending the classifier is an autonomous support agent.

### Active Check: Reduce Authority

Your team wants the AI system to read a ticket, choose a refund amount, and issue the refund.

You have a small eval set and no production history.

What is a safer v1?

A safer v1 is:

> Read the ticket, identify whether a refund may be relevant, extract the requested amount and evidence, and prepare a review note for a billing specialist.

This version still helps.

It reduces reading and summarization work.

It does not move money.

It keeps authority with a person.

That is how v1 shipping should feel.

Useful, bounded, and reviewable.

## Operating The Loop After Launch

Shipping v1 is not the end of evaluation.

It is the beginning of real feedback.

Production inputs will teach you things the first eval set missed.

That does not mean the first eval set failed.

It means the world is larger than your sample.

The right response is not panic.

The right response is to fold new learning back into the loop.

When reviewers override outputs, sample those cases.

When users complain, convert complaints into examples.

When validation fails, inspect whether the schema or system behavior needs adjustment.

When a serious failure appears, decide whether to narrow the launch boundary.

### Post-Launch Signals

Track signals that match the v1 job.

For a ticket router, useful signals include:

- percentage of suggestions accepted by humans
- percentage changed by humans
- top queue confusion pairs
- examples marked `needs_human_review`
- validation failure rate
- unsupported quote rate
- time saved during triage
- user comments from reviewers

Avoid vanity metrics.

Total number of AI calls does not prove value.

Average response length does not prove quality.

Demo applause does not prove reliability.

Track behavior that maps to the job.

### Override Review

Human overrides are not embarrassing.

They are training signals for the product team.

When a triage owner changes `account_access` to `billing`, ask why.

Was the priority rule missing?

Was the evidence present but ignored?

Was the ticket ambiguous?

Was the expected label wrong?

Was the label taxonomy too coarse?

Each answer leads to a different change.

Do not treat all overrides as model errors.

Some are product taxonomy errors.

Some are workflow errors.

Some are unclear policy decisions.

### When To Expand Scope

Expand scope only when the current boundary is stable.

Stable does not mean perfect.

Stable means failure modes are known, reviewable, and acceptable for the use case.

A reasonable expansion might be:

- from one support queue to five queues
- from internal-only users to a larger internal group
- from suggestion-only to auto-routing low-risk cases
- from English tickets to a second supported language
- from weekly review to daily monitoring during a high-volume launch

Each expansion should bring new examples.

A broader launch needs broader evaluation.

Do not reuse a narrow eval set as proof for a wider system.

### Senior Practice: Treat Evals As Product Assets

Evaluation examples are not throwaway test data.

They are product assets.

They encode user jobs.

They encode policy decisions.

They encode failure boundaries.

They help onboard new builders.

They help reviewers challenge changes.

They help future teams understand why v1 behaves the way it does.

Store them where the team can review them.

Version them.

Discuss disputed examples.

Retire examples only when the product boundary changes and the reason is clear.

A mature AI team does not just have prompts.

It has evals, notes, review rules, and launch boundaries.

## Did You Know?

1. **Small eval sets are useful when they are representative**: A carefully chosen set of normal, ambiguous, and risky examples can reveal more than a large set of clean demo cases.

2. **A correct answer can still fail evaluation**: If the answer lacks required evidence, uses the wrong schema, or exceeds its authority, it should fail even when the prose sounds right.

3. **Changing models can hide product bugs**: A stronger model may compensate for vague instructions during demos, but the missing task rule can still cause production failures later.

4. **Refusal behavior is part of quality**: A system that says `not enough information` at the right time is often safer and more useful than a system that always tries to answer.

## Common Mistakes

| Mistake | Why It Hurts | Better Move |
|---|---|---|
| tuning without examples | progress is imaginary | define a small evaluation set first |
| changing too many things at once | no causal learning | change one variable per iteration |
| shipping broad autonomy first | hard to control | ship bounded usefulness first |
| treating demos as evidence | selection bias | test on representative cases |
| fixing one example with phrase-specific rules | creates brittle behavior | write rules for the failure class |
| switching models before diagnosing failures | hides task, context, or schema problems | follow the priority order before model changes |
| ignoring refusal cases | system guesses when evidence is missing | include examples where escalation is correct |

## Quiz

1. **Your team builds a meeting-summary feature. It works on three clean meetings but fails when a meeting has unclear ownership for action items. What should you do before rewriting the whole prompt?**

   <details>
   <summary>Answer</summary>

   Add representative evaluation examples that include unclear ownership, then define what the system should do in that case.

   For example, the expected behavior might be to write `owner_unknown` instead of inventing an owner.

   This is better than a full prompt rewrite because the failure first needs a clear success rule.

   </details>

2. **A support-ticket classifier routes “charged twice and cannot access invoice” to `account_access`, but your business rule says billing issues take priority. Which first change best follows the one-variable rule?**

   <details>
   <summary>Answer</summary>

   Add one explicit priority rule that says billing issues take precedence when a ticket contains billing plus another issue.

   Keep the model, context, and output schema unchanged for that iteration.

   Then rerun the failing case and check whether other account-access examples still pass.

   </details>

3. **A document Q&A system answers from the right policy section but does not include a quote. Reviewers cannot tell whether the answer is grounded. What should you change before changing models?**

   <details>
   <summary>Answer</summary>

   Improve the output shape and evidence instruction.

   Require fields such as `answer`, `supporting_quote`, and `status`.

   Add validation that the quote must appear in the supplied context.

   The issue is reviewability and grounding, not necessarily model capability.

   </details>

4. **Your eval score improves after you change the prompt, switch models, add retrieval, and rewrite the schema in the same run. Why is this result hard to trust?**

   <details>
   <summary>Answer</summary>

   The team cannot tell which change caused the improvement.

   The model switch may have helped.

   The retrieval change may have helped.

   The schema may have made scoring easier.

   The prompt may have fixed the actual issue.

   Because too many variables changed, the iteration produced a result but not clear learning.

   </details>

5. **A refund assistant correctly identifies refund intent, but the customer account ID is missing. The system suggests issuing a refund anyway. What should the expected v1 behavior be?**

   <details>
   <summary>Answer</summary>

   The system should escalate or mark the output as not ready for action.

   A strong v1 behavior would extract the refund request, mark `account_id` as `unknown`, and route the case for human review.

   It should not perform or recommend an irreversible action when required information is missing.

   </details>

6. **A team wants to expand an internal ticket-suggestion feature into automatic routing for all queues. Their current eval set only covers one queue and ten examples. What should you recommend?**

   <details>
   <summary>Answer</summary>

   Do not expand directly to all automatic routing.

   First broaden the evaluation set across the target queues, include ambiguous and risky examples, and verify the review or rollback path.

   A safer expansion might auto-route only low-risk cases while keeping human review for ambiguous cases.

   The launch boundary should grow with the evidence.

   </details>

7. **A model gives a fluent answer that says contractors may access staging. The supplied policy says contractors may access staging only after manager approval and security training. What is the best diagnosis?**

   <details>
   <summary>Answer</summary>

   The system dropped an important condition from the context.

   The first fix should clarify that conditions must be preserved and require a supporting quote.

   A structured output with a `conditions` field can also help.

   Switching models is not the first move because the necessary information was already present.

   </details>

## Hands-On Exercise

You will design and iterate a v1 evaluation plan for one AI feature.

Choose a feature that is small enough to test.

Good options include:

- support ticket routing
- meeting action-item extraction
- internal document Q&A
- release-note summarization
- incident update drafting
- sales lead classification

Avoid broad ideas like “AI support agent” or “AI operations assistant.”

Your goal is to turn a vague feature into a bounded v1 with evidence.

### Step 1: Write The v1 Contract

Write a short contract with these fields:

- user
- input
- output
- allowed actions
- disallowed actions
- success condition
- review boundary
- refusal or escalation behavior

Success criteria:

- [ ] The job can be described in one sentence.
- [ ] The input boundary is clear.
- [ ] The output is reviewable by a human.
- [ ] The feature has at least one explicit disallowed action.
- [ ] The refusal behavior is defined.

### Step 2: Create Five Evaluation Examples

Create five examples.

Include:

- one easy success
- two normal cases
- one ambiguous case
- one case where refusal or escalation is correct

For each example, write:

- input
- expected output
- required evidence
- risk level
- notes about why the example matters

Success criteria:

- [ ] At least one example is messy or ambiguous.
- [ ] At least one example expects refusal or escalation.
- [ ] Every expected output maps to the v1 contract.
- [ ] Required evidence is specific enough to inspect.
- [ ] The examples are not all hand-picked happy paths.

### Step 3: Run A Manual Evaluation

You do not need a production model integration.

You may use manual outputs, saved model outputs, or a simple script like the one in this module.

For each example, mark:

- pass or fail
- failure type
- likely diagnosis
- first change to try

Use this failure taxonomy:

- task ambiguity
- missing context
- bad evidence
- shape drift
- unsafe action
- hallucinated detail
- over-refusal
- regression

Success criteria:

- [ ] Every failure has a named failure type.
- [ ] Every failure has a diagnosis, not just a complaint.
- [ ] The first proposed change targets the diagnosis.
- [ ] You do not change more than one variable in the proposed iteration.
- [ ] You record at least one case that should be rerun for regression.

### Step 4: Perform One Iteration

Choose one failure.

Apply one change.

Examples of valid one-variable changes:

- add a priority rule
- add missing context
- require a supporting quote
- change the output schema
- add validation for missing fields
- narrow the allowed labels
- add a refusal rule

Rerun the same example.

Then rerun at least two other examples to check for regression.

Success criteria:

- [ ] The iteration changes one variable only.
- [ ] The before and after outputs are recorded.
- [ ] The diagnosis explains why the change should help.
- [ ] At least two non-target examples are rerun.
- [ ] You can state whether the change improved, worsened, or did not affect the eval set.

### Step 5: Decide Whether v1 Can Ship

Make a launch recommendation.

Choose one:

- ship to a small internal group
- run another iteration before shipping
- narrow the scope and retest
- do not ship yet

Justify the recommendation with evidence.

Include:

- what works
- what still fails
- what humans must review
- what the system must not do
- what signal you will monitor after launch

Success criteria:

- [ ] The recommendation is tied to eval results.
- [ ] Known failure modes are documented.
- [ ] The launch boundary is explicit.
- [ ] Human review is assigned where risk remains.
- [ ] The system has a rollback, disablement, or fallback plan.

## Next Module

From here, continue to:
- [AI/ML Engineering: AI-Native Development](../../ai-ml-engineering/ai-native-development/)
- or [AI/ML Engineering: Generative AI](../../ai-ml-engineering/generative-ai/)

## Sources

- [OpenAI Evals](https://github.com/openai/evals) — Provides concrete patterns for building repeatable evaluation sets and comparing prompt or model changes over time.
- [NIST AI RMF Playbook](https://www.nist.gov/itl/ai-risk-management-framework/nist-ai-rmf-playbook) — Useful for connecting evaluation, governance, and operational risk controls when deciding what is safe enough to ship.
- [OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/) — Relevant when turning an eval loop into a production feature because it highlights common LLM security and reliability failure modes.

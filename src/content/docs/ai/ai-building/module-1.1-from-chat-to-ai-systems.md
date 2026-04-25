---
title: "From Chat To AI Systems"
slug: ai/ai-building/module-1.1-from-chat-to-ai-systems
sidebar:
  order: 1
---

> **AI Building** | Complexity: `[QUICK]` | Time: 35-45 min | Prerequisites: basic web application concepts, basic API awareness, comfort reading simple diagrams

## Learning Outcomes

By the end of this module, you will be able to:

- **Design** a simple AI-powered feature by separating interface, orchestration, model call, and guardrails.
- **Analyze** where deterministic software should control a workflow and where a model can safely help.
- **Evaluate** whether an AI idea is a toy demo, a real v1 system, or an unsafe first project.
- **Debug** early AI system designs by finding missing validation, review, logging, or failure handling.
- **Compare** feature ideas and choose a beginner-safe AI use case with clear scope and verification.

## Why This Module Matters

A product manager watches a support team spend hours each week reading long customer emails.

A developer opens a chatbot and asks it to summarize one of those emails.

The summary looks useful.

The team gets excited.

Someone says, "Can we ship this?"

That moment is where many AI projects fail.

The prototype worked because one person pasted one message into one chat window.

A product feature has to work for many users, many inputs, many failure modes, and many organizational rules.

The difference is not just an API key.

It is a system design problem.

A chat session hides the engineering choices.

A product feature exposes them.

The app must know who the user is.

The app must know which data the user may access.

The app must decide what context to send.

The app must decide what the model is allowed to do.

The app must check whether the result is useful enough.

The app must handle slow responses, malformed outputs, missing data, and risky suggestions.

The app must give humans the right amount of control.

Many learners can use a chatbot, but they do not yet understand what changes when AI becomes part of a product, workflow, or internal tool.

That gap matters because building even a simple AI feature requires choices that normal chat use hides.

You need to decide where the model sits in the workflow.

You need to decide what the model is allowed to do.

You need to decide what must be verified.

You need to decide what should stay deterministic.

If you miss that transition, you either overengineer too early or ship something fragile that feels impressive but breaks under real use.

This module gives you the first mental model for building with AI.

It treats the model as one component inside a larger software system.

That framing is the foundation for the rest of the AI Building track.

## Start With The Simplest Shift

When you use AI directly, the workflow usually looks like this:

```text
You -> prompt -> model -> answer
```

That workflow is powerful because it is direct.

You decide what to ask.

You decide what context to include.

You judge the answer yourself.

You can re-prompt when the answer is weak.

You can ignore the answer when it is wrong.

The human is doing much more system work than it first appears.

The human is the interface.

The human is the orchestrator.

The human is the validator.

The human is the fallback path.

When you build an AI feature, the workflow usually becomes:

```text
user -> app -> prompt construction -> model -> app logic -> output
```

That is the first important shift:

> the model is rarely the whole system

Instead, it is one component inside a bigger system that still needs application logic.

It still needs access control.

It still needs error handling.

It still needs logging.

It still needs evaluation.

It still needs user experience design.

It still needs a plan for wrong answers.

That sounds less magical, but it is the useful part.

Software engineering turns a useful model response into a repeatable feature.

A good AI system does not ask the model to own the whole workflow.

It gives the model a narrow job inside a controlled workflow.

A weak system says, "The model will figure it out."

A stronger system says, "The model will summarize this bounded input, return this shape, and the app will verify it before showing it."

Those two designs can use the same model.

They will behave very differently in production.

### Active Check: Find The Hidden Human Work

Imagine a teammate says, "I already built the feature manually. I paste customer emails into chat and paste the summary into our CRM."

Before reading on, name three jobs the teammate is doing besides typing.

Good answers include judging which email content is safe to paste.

Good answers include deciding what summary format the CRM needs.

Good answers include checking whether the summary is accurate.

Good answers include deciding whether a human should edit the result.

Good answers include copying the final answer into the correct customer record.

Those jobs do not disappear when you add an API.

They move into the product design.

If the app does not handle them, the feature will depend on luck and user discipline.

The rest of this module gives names to those jobs.

## The Four Parts Of A Simple AI System

A simple AI feature usually has four parts.

The names are not sacred.

The separation is what matters.

You need a place where the user interacts.

You need application code that prepares and controls the task.

You need the model call.

You need checks that keep the result usable and safe.

Here is the protected base picture from the original module, expanded into the product workflow you will use throughout this lesson:

```text
+----------------+      +----------------------+      +----------------+
|     User       | ---> |        App UI        | ---> | Orchestration  |
| wants outcome  |      | form, panel, button  |      | task workflow  |
+----------------+      +----------------------+      +----------------+
                                                              |
                                                              v
+----------------+      +----------------------+      +----------------+
| Final Output   | <--- |     Guardrails       | <--- |   Model Call   |
| shown or held  |      | validate and review  |      | probabilistic  |
+----------------+      +----------------------+      +----------------+
```

The user does not experience four parts.

The user experiences one feature.

The builder must see the four parts anyway.

That separation helps you debug a design before you write code.

If the interface promises too much, users will overtrust the output.

If orchestration sends the wrong context, the model will answer the wrong question.

If the model call is underspecified, outputs will drift.

If guardrails are missing, weak results will look like product behavior.

Each part has a different responsibility.

Each part also has a different failure mode.

A senior engineer does not ask, "Can the model do this?"

A senior engineer asks, "Which part of the system should own each decision?"

### 1. The Interface

This is what the user sees.

It may be a chat box.

It may be an assistant panel.

It may be a code review surface.

It may be a support workflow.

It may be a single "Summarize" button beside a document.

The interface creates expectations.

If the interface looks authoritative, users trust it more.

If the interface looks like a draft helper, users expect to review it.

That difference matters.

A beginner often starts by copying a chat interface.

That is not always wrong.

It is just not automatically right.

For a bounded product feature, a form, button, preview panel, or review queue may be clearer than chat.

A chat box invites open-ended requests.

A focused button communicates a focused job.

Concrete example:

A support tool adds a button labeled "Draft Summary" beside each incoming customer email.

The interface does not ask the model to chat with the agent.

It gives the agent a controlled workflow.

The agent clicks the button.

The system shows a short summary, a sentiment label, and a list of unresolved questions.

The agent can edit the result before saving it to the customer record.

In that design, the interface teaches the user that the output is a draft.

It also keeps the feature aligned with a real work task.

A less careful interface might show a confident full answer with no edit step.

That would push users toward blind trust.

The same model can feel safe or risky depending on the interface around it.

Good interface questions include:

What action is the user trying to complete?

What does the user already know at that moment?

What output shape would help the user decide faster?

Where should the user be able to edit, reject, or retry?

What wording makes the model's role clear without adding clutter?

The interface is not decoration.

It is part of the control system.

### 2. The Orchestration Layer

This is the application code around the model.

It handles system prompt or task framing.

It handles context assembly.

It handles tool permissions.

It handles retries.

It handles output parsing.

It handles routing.

It handles what happens before and after the model call.

This layer determines whether the model is just producing text or participating in a structured workflow.

Concrete example:

A support summarizer receives a customer email ID.

The orchestration layer loads the email body from the database.

It checks that the support agent is assigned to that account.

It removes internal routing headers that the model does not need.

It adds the customer's plan type and open ticket count only if the agent is allowed to see them.

It builds a task prompt that asks for a summary, customer intent, urgency, and unresolved questions.

It asks for structured output instead of free-form prose.

It sets a timeout.

It records a trace ID.

It sends the request to the model.

It parses the response.

It passes the parsed result to validation before showing it.

The orchestration layer is where most production AI engineering happens.

The model call might be one function.

The workflow around it is the system.

Good orchestration questions include:

Which data should be included?

Which data must never be included?

What task should the model perform?

What output format does the rest of the app need?

What happens if the model times out?

What happens if the output cannot be parsed?

What should be logged for debugging without leaking sensitive data?

Orchestration is also where you avoid accidental autonomy.

A model that can write text is one risk level.

A model that can send emails, update tickets, or issue refunds is another risk level.

The orchestration layer decides which tools exist and when they can be used.

For a first system, prefer suggestions over actions.

Let the model draft.

Let the human commit.

### 3. The Model Call

This is the probabilistic part.

It includes model choice.

It includes prompt content.

It includes temperature or reasoning settings.

It includes token budget.

It includes structured output configuration when the platform supports it.

It includes the exact inputs sent at runtime.

This part is important, but it is only one layer.

Concrete example:

The support summarizer calls a model with a bounded task:

Summarize one email thread.

Return a short summary.

Return a customer intent.

Return urgency as one of a small set of labels.

Return unresolved questions as a short list.

Do not invent policy details.

Do not claim that an action has been taken.

That task is narrower than "help with this customer."

The narrower task is easier to test.

It is also easier to review.

A model call can fail even when the service is available.

It can produce a plausible but unsupported claim.

It can ignore part of the instruction.

It can return a value outside the expected schema.

It can over-compress important details.

It can preserve irrelevant details.

It can expose ambiguity instead of resolving it.

Good model-call questions include:

Is this task language-heavy enough to justify a model?

Can the expected answer be checked?

Does the model need private context?

How much context is enough?

Should the output be free text or structured data?

What temperature or sampling behavior fits the task?

What are the examples of bad output we must test?

The model call is not where access control belongs.

It is not where billing rules belong.

It is not where database integrity belongs.

Those responsibilities should stay in normal application code.

The model helps with uncertainty.

The software owns authority.

### 4. The Guardrails

This is what keeps the system usable.

It includes validation.

It includes output checks.

It includes human review.

It includes policy limits.

It includes fallbacks.

It includes observability.

Without this layer, most AI apps are really demos with good wording.

Concrete example:

The support summarizer validates that the model returned every required field.

It checks that urgency is one of `low`, `normal`, or `high`.

It checks that the summary is below the display limit.

It checks that the summary does not claim a refund was issued.

It checks that unresolved questions are framed as questions, not instructions.

It shows the result as a draft.

It requires the support agent to click "Save" before writing to the CRM.

It records whether the agent edited the summary.

It provides a fallback message when summarization fails.

The guardrail layer does not make the model perfect.

It reduces predictable damage.

It catches format problems.

It catches obvious policy violations.

It keeps humans in control where the risk requires it.

It gives the team evidence for improving the system.

Good guardrail questions include:

What output would be harmful if shown directly?

What output would be merely inconvenient?

What can be checked automatically?

What requires human judgment?

What should happen when checks fail?

What evidence will help us debug failures later?

What behavior should cause the feature to be disabled or rolled back?

Guardrails should match the risk.

A lunch recommendation assistant needs lighter controls than a medical intake summarizer.

An internal draft helper needs lighter controls than an automated customer-facing action.

The practical question is not, "Do we have guardrails?"

The practical question is, "Are the guardrails strong enough for this workflow?"

### Active Check: Place The Responsibility

Your team wants an AI assistant that answers billing questions.

A stakeholder asks the model to decide whether a user is eligible for a refund.

Which part of the system should own the refund eligibility rule?

The deterministic application logic should own it.

The model may explain the rule in plain language after the software determines the result.

The model may draft a response for a human to review.

The model should not be the source of truth for the refund decision.

This is the core habit.

Use the model for language and ambiguity.

Use deterministic code for authority and policy.

## A Fully Worked Example: Email Summarizer

Before you design your own feature, study one complete breakdown.

The feature idea is simple:

A support agent opens a long customer email thread and clicks "Summarize."

The system returns a short draft summary that the agent can edit before saving.

This is a good teaching example because it is useful, bounded, and reviewable.

It is not risk-free.

It is manageable.

The user goal is clear.

The model task is language-heavy.

The human can review the result.

The feature can fail gracefully.

Here is the same system mapped to the four parts:

| Part | Email Summarizer Design | Why It Belongs There |
|---|---|---|
| Interface | A "Draft Summary" button, editable summary panel, and "Save to ticket" action | The user needs a focused workflow, not an open-ended chat |
| Orchestration | Load the email thread, check permissions, remove irrelevant headers, build the task prompt, request structured output, parse the response | The app must control context, task framing, and workflow state |
| Model Call | Ask the model to produce summary, customer intent, urgency label, and unresolved questions | The model is useful for compressing messy language into a helpful draft |
| Guardrails | Validate fields, limit length, block unsupported action claims, require human save, log edits and failures | The system must prevent weak output from silently becoming record data |

Now walk through the flow as if you were debugging it.

A support agent opens ticket `T-1182`.

The app checks that the agent belongs to the assigned support group.

The agent clicks "Draft Summary."

The app loads the latest customer-visible email messages.

The app excludes private internal notes.

The app builds a prompt that says the output is a draft for a support agent.

The app requests a structured response.

The model returns a summary, an intent, an urgency label, and questions.

The app validates the urgency label.

The app checks the summary length.

The app checks for forbidden claims such as "we refunded the customer."

The app shows the result in an editable panel.

The support agent edits one sentence.

The support agent saves the summary.

The app records the final saved text and whether it was edited.

Notice what the model did.

It did not decide who may access the ticket.

It did not choose which records to load.

It did not decide whether a refund is allowed.

It did not write directly to the CRM.

It did not send a customer email.

It performed a bounded language task.

That is what makes the system a good first AI feature.

The architecture can still improve later.

You might add better evaluation data.

You might add source highlighting.

You might add confidence signals based on validation results.

You might add per-account policy context.

You might add a review queue for high-priority accounts.

But the v1 is already shaped like a real system.

It has a user workflow.

It has orchestration.

It has a model call.

It has guardrails.

It has a failure path.

It keeps the human in control.

### Worked Example Failure Review

A strong breakdown also asks what can go wrong.

Suppose the model summarizes a customer complaint as "asking about pricing" when the email actually says "cancel my account."

That is not a syntax failure.

The JSON might parse correctly.

The urgency label might be valid.

The output might still be wrong.

A good v1 system cannot eliminate every semantic error.

It can reduce the impact.

The interface calls the output a draft.

The agent can edit it.

The app logs that the agent changed the generated summary.

The team can later sample edited summaries to find patterns.

If many cancellation emails are mislabeled, the team can improve the prompt, add examples, adjust validation, or change the output labels.

That is how real AI systems improve.

They do not depend on one perfect prompt.

They create a workflow where failures can be observed and corrected.

### Active Check: Improve The Example

Change one design choice in the email summarizer.

Pretend the app saves the summary automatically without human review.

What new risks appear?

The system might store inaccurate summaries as official record data.

The support team might stop reading the original email.

A wrong summary might influence later customer decisions.

The team might have no signal that agents would have edited the draft.

The feature has moved from suggestion to action.

That one change requires stronger validation, monitoring, and rollback planning.

This is why "autonomy" is not a vibe.

It is a concrete change in who commits the result.

## A Better Mental Model

Do not think:

> “I am building an AI app.”

Think:

> “I am building a software system that happens to use a model at specific decision points.”

That framing makes better engineering decisions.

It reminds you to keep deterministic parts deterministic.

Authentication should stay deterministic.

Billing should stay deterministic.

Permissions should stay deterministic.

Database writes should stay deterministic.

Policy enforcement should stay deterministic.

Audit logging should stay deterministic.

The model should help with uncertain or language-heavy work, not replace hard controls.

This does not make the model unimportant.

It makes the model usable.

A model can classify intent from messy text.

A model can summarize a long incident report.

A model can draft a response for a human.

A model can extract structured fields from inconsistent documents.

A model can explain an error log in plain language.

A model can propose next diagnostic steps.

Those are valuable jobs.

They are also different from authoritative jobs.

An authoritative job changes the world.

It approves a refund.

It grants access.

It deploys production changes.

It sends a legal notice.

It changes a customer record.

It deletes data.

Those jobs require stronger controls.

Sometimes a mature AI system can participate in them.

A beginner's first system usually should not.

The safest early design pattern is:

Model suggests.

Software checks.

Human decides.

System records.

That pattern is simple enough to build and serious enough to teach good habits.

It also scales.

As your evaluation improves, you can decide which steps can become more automated.

You earn autonomy by measuring reliability and reducing risk.

You do not start with autonomy because the demo looked good.

## Choosing A Good First Use Case

A beginner-friendly AI feature usually looks like one of these:

- summarize a document
- extract structured fields from messy text
- generate a first draft for human editing
- explain code or logs
- answer questions over a bounded internal knowledge source

These are good first use cases because the scope is narrow.

They are good because humans can review results.

They are good because the damage from mistakes is limited.

They are good because they create useful evaluation examples.

They are good because the model has a reason to exist.

A model is often useful when input is messy and output can be reviewed.

A model is often useful when language variation makes rule-based parsing brittle.

A model is often useful when the user needs a starting point rather than a final authority.

A model is often useful when the product can tolerate uncertainty through review and correction.

A model is less useful when the problem is already deterministic.

If a rule can solve the problem exactly, use the rule.

If a database query can answer the question exactly, use the database query.

If a permission check can be expressed in code, use code.

If a calculation must be exact, use normal software.

A good first use case also has a clear "done" state.

"Help support agents summarize emails" is clearer than "make support smarter."

"Extract invoice number, vendor, due date, and total" is clearer than "understand invoices."

"Draft a release note from merged pull requests" is clearer than "manage releases."

Specificity reduces cognitive load.

It also reduces product risk.

When the task is narrow, you can test it.

When you can test it, you can improve it.

When you can improve it, you can ship responsibly.

### A Bad First Use Case

These are poor first projects:

- fully autonomous business actions
- legal or compliance wording with no review
- hidden decision systems with no audit path
- open-ended agent workflows with unclear boundaries
- systems that write to important records without validation
- systems that answer from unbounded sources without source control

These fail because the learner has not yet built the habits needed to control the system.

They also fail because stakeholders misread demos.

A demo shows possibility.

Production reveals responsibility.

An AI assistant that drafts a contract clause for a lawyer to review may be useful.

An AI assistant that sends contract language to customers without review is a different system.

An AI assistant that suggests a Kubernetes diagnostic command may be useful.

An AI assistant that runs production commands without boundaries is a different system.

An AI assistant that summarizes a customer complaint may be useful.

An AI assistant that closes the complaint automatically is a different system.

The difference is not just confidence.

The difference is authority.

Authority changes risk.

Risk changes required controls.

Required controls change the system design.

### Active Check: Rank The Use Cases

Rank these from safest first project to riskiest first project.

A. Draft a summary of a long internal meeting transcript for the meeting owner to edit.

B. Automatically approve or deny customer refund requests based on email sentiment.

C. Extract invoice fields into a review queue where an accountant verifies them.

A reasonable ranking is A or C first, then the other, then B last.

A is bounded and reviewable.

C is bounded and reviewable, but it touches financial records, so validation and review matter more.

B combines model interpretation with an authoritative business decision.

B should not be a beginner's first AI system.

The important skill is not memorizing that ranking.

The important skill is explaining why.

## Toy Demo vs Real v1

A toy demo is not bad.

A toy demo is often the right way to learn whether a feature is possible.

The mistake is pretending the demo is a production system.

Here is the protected comparison table from the original module, expanded with the system-design reason behind each difference:

| Toy Demo | Real v1 |
|---|---|
| works for the author’s example prompt | works across varied real inputs |
| has one happy path | handles failure paths |
| no output validation | parses or checks outputs |
| no logging | captures useful traces |
| no review gate | keeps human review where needed |

The difference is not "bigger model."

The difference is system design.

A toy demo proves that a model can produce a useful-looking answer once.

A real v1 proves that the product can handle enough variation to be useful.

A toy demo can live in a notebook.

A real v1 needs a user workflow.

A toy demo can rely on the author's judgment.

A real v1 needs explicit validation.

A toy demo can fail silently.

A real v1 needs visible fallback behavior.

A toy demo can ignore observability.

A real v1 needs traces that help the team understand failures.

A toy demo can use whatever context the author pasted.

A real v1 needs controlled context assembly.

A toy demo can trust the person running it.

A real v1 needs permissions and data boundaries.

You do not need to build an enterprise platform on day one.

You do need to know which parts are missing.

That awareness lets you make honest decisions.

You can say, "This is a demo."

You can say, "This is a v1 draft helper."

You can say, "This is not ready for autonomous action."

Those labels prevent confusion.

They also protect the team from overcommitting.

## Debugging An AI Feature Design

Before writing code, you can debug a feature design with a simple review.

Ask what happens at each step.

Ask who owns each decision.

Ask what happens when the model is wrong.

Ask what evidence you will have after failure.

This is not paperwork.

It is cheaper than discovering the gaps in production.

Start with the user goal.

If the user goal is vague, the system will be vague.

Then identify the model job.

If the model job is "do everything," the system is not designed yet.

Then identify deterministic controls.

If permissions, policy, and writes are left to the model, the design is too risky.

Then identify output checks.

If nothing checks the model output, the app is just relaying text.

Then identify the human role.

If the human must review the result, the interface should make that review natural.

Then identify the fallback.

If the model is unavailable, the user should still know what to do.

Then identify observability.

If the feature fails, the team needs enough data to debug without exposing private content unnecessarily.

Here is a design review checklist you can apply to any first AI feature.

| Review Question | Weak Answer | Stronger Answer |
|---|---|---|
| What is the user trying to accomplish? | "Use AI in support" | "Summarize long support emails before an agent replies" |
| What is the model's bounded job? | "Handle the ticket" | "Draft a summary, intent, urgency, and open questions" |
| What stays deterministic? | "The model can decide" | "Permissions, record writes, policy checks, and save actions stay in code" |
| How is context selected? | "Send the ticket" | "Send only customer-visible messages the agent may access" |
| How is output checked? | "The answer should look good" | "Validate fields, labels, length, and forbidden claims" |
| What can the human change? | "They can ignore it" | "They can edit, reject, retry, or save explicitly" |
| What happens on failure? | "Try again later" | "Show a fallback, log a trace, and preserve the normal workflow" |

This table is not meant to slow you down.

It is meant to reveal missing design work.

A single weak answer can be acceptable in a prototype.

Several weak answers mean the system is not ready to be treated as a product.

Senior-level judgment is often the ability to say exactly which risks are acceptable for this stage.

Not all risk is failure.

Unclear risk is failure.

## From Beginner Thinking To Senior Thinking

Beginner thinking often starts with model capability.

Can the model summarize?

Can the model extract fields?

Can the model answer questions?

Those are reasonable starting questions.

They are not enough.

Intermediate thinking adds workflow.

Where does the feature sit?

Who uses it?

What data does it need?

What output does the app need?

What happens when the model fails?

Senior thinking adds operational responsibility.

How will we evaluate quality over time?

How will we notice drift?

How will we protect sensitive data?

How will we avoid hidden automation?

How will we design review into the product instead of bolting it on?

How will we decide when more autonomy is justified?

How will we prove that the system is improving?

This does not mean every first module must build all of that.

It means you should recognize the shape of the path.

A quick prototype can be useful.

A v1 needs control.

A mature system needs measurement.

A critical system needs governance.

Those stages should not be blurred.

If a stakeholder asks, "Can we just let the model do it?", your answer should be specific.

You can say, "For this first version, the model can draft the response, but the user should send it."

You can say, "The model can classify the request, but the refund rule must stay in code."

You can say, "The model can extract fields, but the accountant should verify before posting."

You can say, "We need logs and reviewed examples before considering automation."

That is practical engineering.

It avoids both hype and fear.

It turns AI into a component you can reason about.

## Designing The First Version

A real v1 should be boring in the right places.

The user flow should be clear.

The model task should be bounded.

The output should be shaped.

The checks should be explicit.

The human role should be visible.

The fallback should be acceptable.

A useful v1 does not require a complex agent.

It does not require every possible tool.

It does not require a custom evaluation platform on day one.

It does require honesty about what the system can and cannot do.

Here is a simple v1 planning sequence.

First, write the user goal in one sentence.

Second, write the model job in one sentence.

Third, write what stays deterministic.

Fourth, write what data the model receives.

Fifth, write the expected output shape.

Sixth, write what the app checks.

Seventh, write what the human can do.

Eighth, write how failure is handled.

This sequence is intentionally plain.

If you cannot fill it out, the design is not ready for implementation.

If you can fill it out, you can usually build a small feature without losing the plot.

Consider another example.

Feature idea:

"Generate a release note draft from merged pull requests."

User goal:

A maintainer wants a first draft of release notes for a version.

Model job:

Summarize merged pull request titles and descriptions into user-facing release note sections.

Deterministic controls:

The app decides which pull requests belong to the release.

The app decides which repository the user may access.

The app decides where the draft is stored.

The app decides who can publish.

Context:

Merged pull request titles, descriptions, labels, and linked issue titles.

Expected output:

Sections for features, fixes, breaking changes, and known issues.

Checks:

The app validates that every mentioned pull request ID exists in the selected release range.

The app flags claims about breaking changes unless the source label supports them.

Human role:

The maintainer edits the draft and publishes manually.

Failure handling:

If generation fails, the app shows the pull request list and lets the maintainer write manually.

This is the same pattern as the email summarizer.

Different domain.

Same system shape.

That reuse is the point.

Once you see the four parts, you can apply them across features.

## What To Keep Deterministic

The word deterministic means the same input should reliably produce the same result.

Normal software is excellent at deterministic work.

Models are excellent at fuzzy language work.

Confusing those strengths creates fragile systems.

Keep identity deterministic.

A model should not decide who the user is.

Keep authorization deterministic.

A model should not decide what records a user may access.

Keep money movement deterministic.

A model should not decide whether a transaction is valid.

Keep irreversible writes deterministic.

A model should not directly delete, publish, refund, or deploy without controls.

Keep policy enforcement deterministic.

A model can explain a policy, but code should enforce it.

Keep audit trails deterministic.

A model should not be the only place where a decision is recorded.

This does not mean the model has no role near these areas.

The model can help users understand why a rule applied.

The model can draft a message about a deterministic decision.

The model can extract evidence for a human reviewer.

The model can summarize policy-relevant facts.

The model can propose next steps.

The authority remains outside the model.

This separation is how you build features that feel intelligent without becoming ungovernable.

## What Models Are Good For

Models are useful when language is messy.

Customer emails are messy.

Incident reports are messy.

Meeting transcripts are messy.

Support logs are messy.

Pull request discussions are messy.

Requirements documents are messy.

Models are useful when output needs judgment but can be reviewed.

A draft can be reviewed.

A summary can be checked.

An extraction can be verified against the source.

A classification can be sampled.

A suggested next step can be accepted or rejected.

Models are useful when the user needs acceleration, not replacement.

A support agent still owns the response.

A maintainer still owns the release notes.

An accountant still owns the invoice approval.

An engineer still owns the production change.

The best first systems make people faster while keeping them responsible.

That is not a compromise.

It is a strong product design.

It gives users leverage without hiding uncertainty.

It also creates feedback.

When users edit drafts, reject suggestions, or correct classifications, the team learns what to improve.

A fully hidden system often loses that feedback.

## What To Measure First

You cannot improve an AI system you cannot observe.

For a first v1, measurement can be simple.

Track whether generation succeeds.

Track whether output validation passes.

Track whether users edit the output.

Track whether users reject the output.

Track common failure reasons.

Track latency.

Track fallback frequency.

Track a small sample of reviewed examples.

Do not collect sensitive data casually.

Observability should respect privacy and security.

You can often log metadata instead of full content.

You can record output length, validation status, label values, edit distance, and trace IDs.

You can sample with controls.

You can keep raw content out of logs unless you have a clear policy and need.

The goal is to answer practical questions.

Is the feature being used?

Is it saving time?

Where does it fail?

Which inputs cause weak output?

Are users editing everything?

Are users accepting risky answers too quickly?

Did a prompt change improve or degrade quality?

These questions turn AI development into engineering.

Without them, every prompt change is a guess.

## Did You Know?

- **Many AI failures are workflow failures, not model failures.** A model can produce a decent answer and the product can still fail because the wrong data was sent, the user could not review it, or the app treated a draft as final.

- **A smaller scoped feature can be more valuable than a larger vague assistant.** Users often trust a focused tool more because they understand what it is supposed to do and where they still own the decision.

- **Human review is a design element, not an apology.** When review is built into the flow, users can correct output quickly and the team can learn from those corrections.

- **Structured outputs change the engineering problem.** Instead of asking the app to interpret arbitrary prose, a structured response lets normal software validate fields, route results, and fail predictably.

## Common Mistakes

| Mistake | Why It Fails | Better Move |
|---|---|---|
| treating the model as the whole product | ignores workflow and controls | design the whole path around the model call |
| starting with autonomy | too much risk too early | start with suggestion or draft generation |
| using AI where rules are enough | adds cost and unpredictability | keep deterministic logic in normal code |
| optimizing prompts before use case clarity | solves the wrong problem | define the task and failure modes first |
| copying a chat interface for every feature | invites open-ended use when the task is bounded | choose a form, button, panel, or review queue when it fits the job |
| skipping output validation | lets malformed or risky responses become product behavior | validate structure, labels, length, and forbidden claims before display or save |
| hiding the human review step | makes users overtrust drafts or miss accountability | make edit, reject, retry, and save actions explicit in the interface |

## Quiz

1. **Your team builds an AI feature that drafts summaries of customer tickets. In the prototype, the model writes directly to the ticket history. During testing, agents say the summaries are often useful but sometimes miss cancellation requests. What should you change before calling this a real v1?**

   <details>
   <summary>Answer</summary>

   Move the model output into a draft review flow instead of writing directly to the ticket history. The interface should let agents edit, reject, retry, and explicitly save. The app should validate the output shape and log review behavior so the team can learn where summaries fail. The key issue is not that summarization is useless; the issue is that an uncertain draft is being treated as authoritative record data.

   </details>

2. **A stakeholder asks for an AI billing assistant that decides whether a customer qualifies for a refund and then explains the decision. How should you divide responsibility between deterministic software and the model?**

   <details>
   <summary>Answer</summary>

   Deterministic software should decide refund eligibility using the actual policy, account data, and authorization rules. The model may summarize the customer's request, extract relevant facts for review, or draft a plain-language explanation after the deterministic decision is made. The model should not be the source of truth for the refund decision because policy enforcement and money movement require predictable controls.

   </details>

3. **You are reviewing an AI release-note generator. It sends all recent pull request text to the model and asks for a release note. The output looks good, but it mentions a breaking change from a pull request outside the release range. Which layer is weak, and what should the team add?**

   <details>
   <summary>Answer</summary>

   The orchestration and guardrail layers are weak. Orchestration should select only the pull requests that belong to the release range. Guardrails should check that every referenced pull request exists in the selected input and that breaking-change claims are supported by labels or explicit source data. A good-looking answer is not enough if the system cannot verify its claims against the chosen context.

   </details>

4. **Your teammate proposes a general chat box for an invoice-processing tool. Users would paste invoices and ask the model what to do. You think a focused workflow is safer. What interface would you recommend for a first version, and why?**

   <details>
   <summary>Answer</summary>

   Recommend a focused upload or review workflow that extracts specific fields such as vendor, invoice number, due date, total, and line-item notes into an editable review panel. This interface matches the real task and keeps the user in a verification role. A general chat box invites open-ended requests, hides the expected output shape, and makes validation harder.

   </details>

5. **An internal assistant answers questions over company policies. It sometimes answers from memory instead of the current policy document. The team wants to improve reliability without making the model responsible for policy enforcement. What design changes should you make?**

   <details>
   <summary>Answer</summary>

   Bound the context to approved policy documents, show or store source references, and instruct the model to answer only from provided context. The app should handle retrieval and document permissions deterministically. The model can explain the relevant policy in plain language, but actual enforcement should remain in normal software or human review. Add guardrails that detect missing sources or unsupported claims.

   </details>

6. **A demo summarizes meeting transcripts well when the author chooses clean examples. In real use, transcripts include multiple speakers, incomplete sentences, and sensitive HR discussions. What questions determine whether this is ready for v1?**

   <details>
   <summary>Answer</summary>

   Ask who may access each transcript, which parts of the transcript should be sent, what summary format users need, what sensitive topics require filtering or review, how users can edit or reject the summary, what validation is possible, and what fallback appears when generation fails. The demo shows model capability; v1 readiness depends on workflow, permissions, context control, guardrails, and review.

   </details>

7. **Your team wants to reduce latency by removing validation from a structured extraction feature. The model output usually parses correctly, and users want the screen to feel faster. How should you evaluate that tradeoff?**

   <details>
   <summary>Answer</summary>

   Do not remove validation just because the happy path is common. First identify what bad output could do. If malformed or unsupported fields can corrupt records, mislead users, or trigger downstream work, validation is required. You might optimize validation, run lightweight checks first, stream a draft state, or improve model settings, but the system still needs explicit checks before treating output as product data.

   </details>

## Hands-On Exercise

Design a first-version AI feature using the four-part model.

Choose one feature idea from your own work or use one of these prompts.

You may design a meeting summarizer.

You may design an invoice field extractor.

You may design a support email summarizer.

You may design a release-note draft generator.

You may design a log explanation assistant.

Do not start by writing prompts.

Start by designing the system.

Step 1: Write the user goal.

Use one sentence.

Make it concrete.

Weak goal:

"Use AI for support."

Stronger goal:

"Help a support agent draft a short editable summary of a long customer email thread."

Step 2: Identify the interface.

Describe what the user sees.

Decide whether the feature should be chat, a button, a form, a side panel, a review queue, or another focused interface.

Explain why that interface fits the task.

Step 3: Identify the orchestration layer.

List what the app must do before calling the model.

Include data loading.

Include permission checks.

Include context selection.

Include task framing.

Include timeout or retry behavior if relevant.

Step 4: Identify the model call.

Write the model's bounded job in one sentence.

Define the expected output shape in plain language.

Avoid asking the model to own policy, access control, billing, publishing, or irreversible actions.

Step 5: Identify the guardrails.

List at least three checks or controls.

Include one automatic check.

Include one human review point.

Include one fallback behavior.

Step 6: Classify deterministic logic.

Write down every part of the feature that should stay in normal software.

Include permissions.

Include record writes.

Include source selection.

Include policy decisions if your feature has them.

Step 7: Describe a likely failure.

Pick one realistic failure.

Do not choose only "the API is down."

Choose something semantic, such as a misleading summary, missing field, unsupported claim, wrong label, or unsafe recommendation.

Explain how your system reduces the damage.

Step 8: Decide whether the feature is a toy demo, real v1, or unsafe first project.

Justify the label.

Use the four parts as evidence.

A real v1 should have a user workflow, orchestration, model call, guardrails, and failure handling.

A toy demo may prove the model can respond but lacks product controls.

An unsafe first project gives the model too much authority before the team can verify reliability.

**Success criteria**

- [ ] You wrote a concrete user goal in one sentence.
- [ ] You mapped the feature to interface, orchestration, model call, and guardrails.
- [ ] You identified at least three deterministic responsibilities that should stay in normal software.
- [ ] You defined a bounded model job instead of asking the model to own the whole workflow.
- [ ] You included at least one automatic validation step.
- [ ] You included at least one human review or approval point where risk requires it.
- [ ] You described a realistic failure and how the design limits its impact.
- [ ] You classified the design as toy demo, real v1, or unsafe first project with a clear justification.

## Next Module

Continue to [Models, APIs, Context, and Structured Output](./module-1.2-models-apis-context-structured-output/).

## Sources

- [Building Effective AI Agents](https://www.anthropic.com/research/building-effective-agents/) — Explains the difference between controlled workflows and more autonomous agents, which maps directly to this module's system-design framing.
- [Structured model outputs](https://platform.openai.com/docs/guides/structured-outputs?api-mode=chat) — Shows how schema-shaped outputs make validation, routing, and predictable failure handling easier in real AI features.
- [AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework) — Provides a practical risk and control framework for guardrails, review, measurement, and governance around AI systems.

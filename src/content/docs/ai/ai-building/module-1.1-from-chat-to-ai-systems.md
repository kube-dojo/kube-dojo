---
title: "From Chat To AI Systems"
slug: ai/ai-building/module-1.1-from-chat-to-ai-systems
sidebar:
  order: 1
revision_pending: false
---

> **Complexity**: `[QUICK]`
>
> **Time to Complete**: 35-45 min
>
> **Prerequisites**: basic web application concepts, basic API awareness, comfort reading simple diagrams

---

## Learning Outcomes

By the end of this module, you will be able to:

- **Design** a simple AI-powered feature by separating the interface, orchestration layer, model call, and guardrails into responsibilities that normal software can implement and test.
- **Analyze** where deterministic software should control a workflow and where a model can safely help with uncertain, language-heavy, or reviewable work.
- **Evaluate** whether an AI idea is a toy demo, a real v1 system, or an unsafe first project by comparing scope, authority, validation, and fallback behavior.
- **Debug** early AI system designs by finding missing context selection, output validation, human review, observability, and failure handling before the first production user sees the feature.
- **Compare** beginner-safe AI use cases and choose one with clear boundaries, measurable quality, human review where risk requires it, and a model job narrow enough to verify.

## Why This Module Matters

Hypothetical scenario: a product manager watches a support team spend hours each week reading long customer emails, and a developer opens a chatbot to summarize one of those emails. The result looks useful, the team can imagine the time savings, and someone naturally asks whether the same behavior can be shipped inside the support tool. That question is the moment where many AI projects become confusing, because the successful chat session hides work that the human was doing manually.

In the chat version, the human chose the input, decided which details were safe to paste, judged whether the answer sounded right, edited the result, and copied the final text into the correct place. In a product feature, those responsibilities cannot be left as invisible assumptions. The app must know who the user is, which data the user may access, what context the model should receive, what the model is allowed to do, how the output will be checked, and what happens when the model is slow, malformed, or confidently wrong.

This module gives you the first mental model for building with AI: the model is one component inside a larger software system, not the whole system. You will practice separating user interface, orchestration, model call, and guardrails, then use that separation to compare toy demos with real v1 features. The same habit will matter later when AI features run beside Kubernetes 1.35+ workloads, call internal APIs, or sit inside operational tools where permissions and audit trails cannot be improvised.

## Start With The Simplest Shift

When you use AI directly, the workflow often looks simple because one person is doing several jobs at once. You decide what to ask, choose the context, notice whether the answer is useful, retry when the answer is weak, and ignore the output when it is wrong. The chat box feels like one interaction, but the human is also acting as interface designer, orchestrator, validator, reviewer, and fallback path.

```text
You -> prompt -> model -> answer
```

The moment you build a product feature, the workflow gains explicit software boundaries. A user action enters the application, application code gathers context and frames the task, the model produces a probabilistic result, and ordinary software decides what to parse, validate, show, save, retry, or reject. This expanded path is less magical, but it is also what makes the feature repeatable for more than one careful person with one clean example.

```text
user -> app -> prompt construction -> model -> app logic -> output
```

The first important shift is that the model is rarely the whole system. It still needs application logic around it: authentication, authorization, context selection, timeouts, parsing, logging, validation, user experience design, and a plan for wrong answers. A weak design says, "The model will figure it out." A stronger design says, "The model will summarize this bounded input, return this shape, and the app will verify it before showing it."

Pause and predict: if a teammate says, "I already built this manually by pasting customer emails into chat and copying the summary into our CRM," what three jobs is the teammate doing besides typing? Good answers include choosing safe input, deciding the output format the CRM needs, checking accuracy, editing the answer, and saving it to the right record. Those jobs do not disappear when you add an API; they move into product design.

The practical lesson is not that chat is bad. Chat is a powerful exploration interface, and it can be the right interface for open-ended assistance. The lesson is that a product feature must make hidden human work explicit enough to test, support, and improve. If the app does not own those responsibilities, the feature depends on user discipline and lucky examples rather than engineering.

## The Four Parts Of A Simple AI System

A simple AI feature usually has four parts, even when the user experiences it as one button, panel, or assistant. The names are not sacred; the separation is what matters. You need a place where the user acts, application code that prepares and controls the task, a model call that handles the uncertain language work, and guardrails that keep the result usable, reviewable, and safe enough for the workflow.

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

The interface is what the user sees, and it shapes the user's expectations before the model says anything. A chat box invites open-ended requests, which may be useful for exploration but risky for a narrow workflow. A button, form, side panel, or review queue can communicate a focused job more clearly, especially when the output is a draft that should be edited before it becomes record data.

Exercise scenario: a support tool adds a button labeled "Draft Summary" beside each incoming customer email. The agent clicks the button, the system shows a short summary with customer intent, urgency, and unresolved questions, and the agent can edit the result before saving it. The interface teaches the user that the output is a draft, not an authoritative decision, while still reducing the work of reading a long thread from scratch.

The orchestration layer is the application code around the model call, and it is where much of production AI engineering actually happens. It loads the source record, checks permissions, removes irrelevant or sensitive details, builds the task framing, requests a structured response, applies timeouts, records a trace identifier, parses the result, and sends the parsed output into validation. The model call may be one function, but the workflow around it is the system.

Before running this mental design review, what output do you expect if orchestration sends the wrong context to an otherwise capable model? The answer will often look fluent while answering the wrong question. That is why context selection belongs in normal application code, where you can test which records are included, prove the user may access them, and avoid relying on the model to discover missing business boundaries after the fact.

The model call is the probabilistic part, and it includes model choice, prompt content, sampling behavior, token budget, structured output configuration, and the exact runtime inputs. This part matters, but it should not become a dumping ground for access control, billing logic, database integrity, or policy enforcement. The model helps with uncertainty; the software owns authority.

The guardrail layer is what keeps the feature usable when the model output is incomplete, unsupported, malformed, or simply not good enough. Guardrails can validate required fields, constrain labels, limit length, block forbidden claims, require human review, provide fallback text, and record enough evidence to debug failures without casually logging sensitive content. Guardrails do not make the model perfect; they reduce predictable damage and create feedback for improvement.

Which approach would you choose here and why: should a model decide whether a customer qualifies for a refund, or should deterministic code decide eligibility and let the model draft a plain-language explanation? The safer beginner design keeps the refund rule in software and uses the model only after the decision is made. That division lets the system benefit from language generation without turning an uncertain component into the source of financial authority.

## A Fully Worked Example: Email Summarizer

Before you design your own feature, study one complete breakdown. The feature idea is intentionally plain: a support agent opens a long customer email thread and clicks "Summarize." The system returns a short draft summary that the agent can edit before saving. This is a good first AI feature because the user goal is clear, the model task is language-heavy, the human can review the result, and the feature can fail gracefully.

| Part | Email Summarizer Design | Why It Belongs There |
|---|---|---|
| Interface | A "Draft Summary" button, editable summary panel, and "Save to ticket" action | The user needs a focused workflow, not an open-ended chat |
| Orchestration | Load the email thread, check permissions, remove irrelevant headers, build the task prompt, request structured output, parse the response | The app must control context, task framing, and workflow state |
| Model Call | Ask the model to produce summary, customer intent, urgency label, and unresolved questions | The model is useful for compressing messy language into a helpful draft |
| Guardrails | Validate fields, limit length, block unsupported action claims, require human save, log edits and failures | The system must prevent weak output from silently becoming record data |

Walk through the flow as if you were debugging it. A support agent opens ticket T-1182, the app checks that the agent belongs to the assigned support group, and the agent clicks "Draft Summary." The app loads the latest customer-visible messages, excludes private internal notes, frames the output as a draft for a support agent, requests structured fields, and sets a timeout so the normal ticket workflow is not blocked indefinitely.

The model returns a summary, an intent, an urgency label, and unresolved questions. The app validates that every field exists, confirms that urgency is one of a small allowed set, checks that the summary fits the display limit, blocks claims such as "we refunded the customer," and shows the result in an editable panel. The agent edits one sentence, saves the summary, and the app records the final text plus metadata about whether the generated draft was changed.

Notice what the model did not do. It did not decide who may access the ticket, choose which records to load, decide whether a refund is allowed, write directly to the CRM, or send a customer email. It performed a bounded language task inside a controlled workflow. That boundary is what turns a useful demo into a beginner-safe v1 rather than a feature that silently gives the model operational authority.

A strong design review also asks what can go wrong when the model output is syntactically valid but semantically weak. Suppose the model summarizes a customer complaint as "asking about pricing" when the email actually says "cancel my account." The JSON might parse correctly, the urgency label might be valid, and the output might still mislead the agent. A good v1 cannot eliminate every semantic error, but it can reduce the impact by keeping the result editable, labeling it as a draft, logging review behavior, and preserving the original email nearby.

That feedback loop is how real AI systems improve. If many cancellation emails are mislabeled, the team can sample edited drafts, add evaluation examples, adjust the task framing, change the allowed labels, or add a specific validation rule that flags cancellation language for review. The system does not depend on one perfect prompt. It creates a workflow where failures can be observed, corrected, and measured over time.

Now change one design choice: pretend the app saves the summary automatically without human review. The feature has moved from suggestion to action, and the risks change immediately. The system might store inaccurate summaries as official record data, future agents might stop reading the original email, and the team might lose the signal that humans would have edited the result. Autonomy is not a mood; it is a concrete change in who commits the output.

## A Better Mental Model

Do not think, "I am building an AI app," as if the model were a special replacement for system design. Think, "I am building a software system that uses a model at specific decision points." That framing keeps deterministic parts deterministic, places uncertainty where it belongs, and makes the feature easier to debug when something goes wrong.

Authentication, authorization, billing, permissions, irreversible writes, policy enforcement, and audit logging should remain deterministic. A model can explain a policy, summarize facts relevant to a policy, draft a message about a deterministic decision, or help a human understand an exception. It should not be the only component deciding who has access, whether money moves, whether data is deleted, or whether a production change is deployed.

Models are valuable because many real inputs are messy. Customer emails, incident reports, meeting transcripts, code review discussions, support logs, requirements documents, and pull request descriptions contain ambiguity that rigid rules handle poorly. A model can summarize, classify, draft, extract, or explain those inputs so a human or deterministic workflow can move faster. The value comes from placing the model where uncertainty is useful and keeping authority where predictability is required.

The safest early design pattern is simple: model suggests, software checks, human decides, system records. This pattern is not a compromise for weak teams; it is a practical way to earn trust. As your evaluation data improves, you can decide whether some review steps can become lighter or more automated. You earn autonomy by measuring reliability and reducing risk, not by assuming the demo will behave the same way across real users and messy inputs.

Beginner thinking often starts with model capability: can the model summarize, extract fields, or answer questions? Intermediate thinking adds workflow: who uses the feature, what data does it need, what output does the app need, and what happens when the model fails? Senior thinking adds operational responsibility: how will quality be evaluated, how will drift be noticed, how will sensitive data be protected, and how will the team decide when more autonomy is justified?

If a stakeholder asks whether the model can "just do it," answer with a system boundary instead of a slogan. You can say the model can draft the response but the user should send it, the model can classify the request but the refund rule must stay in code, or the model can extract invoice fields but the accountant should verify before posting. That answer is practical because it names both the useful model job and the control that keeps the workflow safe.

## Choosing A Good First Use Case

A beginner-friendly AI feature usually has a narrow task, reviewable output, limited damage from mistakes, and a clear reason to use a model. Summarizing documents, extracting structured fields from messy text, generating a first draft for human editing, explaining logs, or answering questions over a bounded knowledge source can all be good first projects. They are not risk-free, but they give the team enough control to learn without turning uncertain output into hidden authority.

The same comparison helps you reject tempting but unsafe first projects. Fully autonomous business actions, legal wording with no review, hidden decision systems with no audit path, open-ended agent workflows with unclear boundaries, and systems that write to important records without validation all demand controls a beginner has not yet built. A demo shows possibility; production reveals responsibility. The difference between the two is not confidence, but authority.

A good first use case also has a clear done state. "Help support agents summarize emails" is clearer than "make support smarter." "Extract invoice number, vendor, due date, and total into a review queue" is clearer than "understand invoices." "Draft release notes from merged pull requests" is clearer than "manage releases." Specificity reduces cognitive load, reduces risk, and gives you something concrete to test.

Compare these three ideas as first projects. A meeting transcript summarizer for the meeting owner to edit is bounded and reviewable. An invoice extractor that places fields into an accountant review queue is also bounded and reviewable, though it touches financial records and needs stronger validation. An assistant that automatically approves or denies refunds from email sentiment combines uncertain interpretation with authoritative money movement, so it is the riskiest and should not be the first build.

The important skill is explaining the ranking, not memorizing it. A safe first project keeps the model job narrow, makes the user goal visible, leaves deterministic rules in code, includes validation, and gives humans an appropriate review point. If you cannot name those pieces, the idea may still be a useful demo, but it is not ready to be described as a real v1 system.

## Toy Demo vs Real v1

A toy demo is not bad. It is often the right way to learn whether a model can produce a useful-looking answer for one clean example. The mistake is pretending that the demo is a production system. A real v1 does not need a giant platform, but it does need explicit workflow, context control, validation, failure handling, and a way to learn from user review.

| Toy Demo | Real v1 |
|---|---|
| works for the author's example prompt | works across varied real inputs |
| has one happy path | handles failure paths |
| no output validation | parses or checks outputs |
| no logging | captures useful traces |
| no review gate | keeps human review where needed |

The difference is system design, not simply a bigger model. A toy demo can live in a notebook, rely on the author's judgment, fail silently, ignore observability, and use whatever context the author pasted. A real v1 needs a user workflow, explicit permissions, controlled context assembly, predictable fallback behavior, and traces that help the team understand failures without exposing private content unnecessarily.

You do not need to build every mature control on day one. You do need to label the stage honestly so stakeholders do not overcommit. You can say, "This is a demo that proves the model can respond," or "This is a v1 draft helper with human review," or "This is not ready for autonomous action." Those labels protect the team because they connect product claims to the actual controls in the system.

## Debugging An AI Feature Design

Before writing code, debug the feature design with a structured review. Start with the user goal, because a vague user goal produces vague model behavior. Then identify the model job, deterministic controls, context selection, output checks, human role, fallback, and observability. This is not paperwork; it is cheaper than discovering in production that the model was given authority the application never meant to delegate.

| Review Question | Weak Answer | Stronger Answer |
|---|---|---|
| What is the user trying to accomplish? | "Use AI in support" | "Summarize long support emails before an agent replies" |
| What is the model's bounded job? | "Handle the ticket" | "Draft a summary, intent, urgency, and open questions" |
| What stays deterministic? | "The model can decide" | "Permissions, record writes, policy checks, and save actions stay in code" |
| How is context selected? | "Send the ticket" | "Send only customer-visible messages the agent may access" |
| How is output checked? | "The answer should look good" | "Validate fields, labels, length, and forbidden claims" |
| What can the human change? | "They can ignore it" | "They can edit, reject, retry, or save explicitly" |
| What happens on failure? | "Try again later" | "Show a fallback, log a trace, and preserve the normal workflow" |

Use the table as a diagnostic tool, not as a ceremony. One weak answer can be acceptable in a prototype if everyone understands the limitation. Several weak answers mean the system is not ready to be treated as a product. Senior-level judgment is often the ability to say exactly which risks are acceptable for this stage and which ones would require a different design.

Observability deserves special attention because you cannot improve an AI system you cannot observe. For a first v1, measurement can be simple: generation success, validation pass rate, edits, rejections, common failure reasons, latency, fallback frequency, and a small sample of reviewed examples. You do not need to log raw sensitive content casually. Metadata, trace identifiers, output length, label values, and review outcomes often answer the most urgent engineering questions with less privacy risk.

These measurements turn AI work back into engineering. They help you ask whether the feature is being used, whether it saves time, where it fails, which inputs produce weak output, whether users edit everything, and whether a prompt or model change improved quality. Without those signals, every prompt change is a guess and every stakeholder discussion becomes a debate over anecdotes instead of evidence.

## Designing The First Version

A real first version should be boring in the right places. The user flow should be clear, the model task should be bounded, the output should be shaped, the checks should be explicit, the human role should be visible, and the fallback should be acceptable. A useful v1 does not require a complex agent, every possible tool, or a custom evaluation platform on day one. It does require honesty about what the system can and cannot do.

Start by writing the user goal in one sentence, then write the model job in one sentence. After that, name what stays deterministic, what data the model receives, what output shape the app expects, what the app checks, what the human can do, and how failure is handled. This sequence is intentionally plain. If you cannot fill it out, the design is not ready for implementation, because the missing sentence points to a missing responsibility.

Consider a release-note draft generator as a second worked example. The user goal is that a maintainer wants a first draft of release notes for a version. The model job is to summarize merged pull request titles and descriptions into user-facing sections for features, fixes, breaking changes, and known issues. The deterministic software decides which pull requests belong to the release, which repository the user may access, where the draft is stored, and who can publish it.

The context for that feature might include pull request titles, descriptions, labels, merged timestamps, and linked issue titles from the selected release range. The expected output shape is a draft with sections and references back to source pull requests. The checks verify that every mentioned pull request ID exists in the selected range, that breaking-change claims are supported by labels or source text, and that the draft does not claim a release was published. The maintainer edits the result and publishes manually.

That example has a different domain from the email summarizer, but the same system shape. Interface gives the maintainer a draft surface, orchestration gathers the allowed release context, the model performs language-heavy summarization, and guardrails check references before the draft becomes official release communication. This reuse is the point of the four-part model. Once you can see the parts, you can move across domains without treating every AI idea as mysterious.

When the v1 feels too small, resist the urge to add autonomy before adding measurement. A narrow tool that saves ten careful minutes each day may be more valuable than a broad assistant that users do not trust. Small scope also gives you better evaluation examples because the expected behavior is easier to inspect. The right first version should create confidence that the workflow can be controlled, not merely prove that the model can produce impressive text.

## What To Keep Deterministic

Deterministic means the same input reliably produces the same result. Normal software is excellent at deterministic work, and models are not a replacement for that strength. Keep identity deterministic, because a model should not decide who the user is. Keep authorization deterministic, because a model should not decide what records a user may access. Keep money movement deterministic, because transactions need predictable checks, logs, and approval paths.

Irreversible writes also deserve deterministic ownership. A model should not directly delete data, publish official content, issue refunds, grant access, or deploy production changes in a beginner's first system. The model may draft the message, explain the policy, extract facts for review, or propose next diagnostic steps, but the commit point should belong to software and humans with explicit authority. That separation keeps the system useful without making it ungovernable.

Policy enforcement belongs in code or governed human process, not in prompt text alone. Prompt instructions can guide behavior, but they are not a substitute for enforceable checks. If a support summary must not claim that a refund was issued, validate the output for that claim and keep actual refund state in the billing system. If a policy answer must come from approved documents, make retrieval and source selection deterministic before asking the model to explain the result.

Audit trails should also be deterministic. If the only record of a decision lives inside a model response, the system will be hard to investigate later. Record who requested the action, what source records were used, which validation checks passed, whether the human edited or accepted the output, and what final text was saved. You do not need to store every raw prompt forever, and privacy may forbid that, but you do need enough structured evidence to debug and govern the feature.

This boundary does not make the model unimportant. It makes the model useful in the right places. A model can turn messy language into a draft, explain an error in terms a human can understand, or extract candidate fields from inconsistent documents. The surrounding software then decides what is allowed, what is checked, what is saved, and what happens when the model cannot help.

## What Models Are Good For

Models are useful when language is messy and the desired output can be reviewed or checked. Customer emails contain indirect requests, emotional wording, missing context, and long digressions. Incident reports mix symptoms, hypotheses, and partial timelines. Pull request discussions include technical shorthand and social negotiation. In those situations, a model can compress, reorganize, classify, or explain material in ways that save humans time.

Models are also useful when the user needs a starting point rather than a final authority. A draft response can be edited, a summary can be compared with the source, extracted invoice fields can be verified, and a suggested diagnostic path can be accepted or rejected. That reviewability matters because it turns uncertainty into a manageable part of the workflow rather than a hidden decision.

The best first systems make people faster while keeping them responsible. A support agent still owns the customer response, a maintainer still owns the release notes, an accountant still owns invoice approval, and an engineer still owns the production change. The model provides leverage by reducing blank-page work and surfacing structure in messy inputs. The user remains accountable for the final action when the risk requires judgment.

Models are weaker when the problem is already exact. If a database query can answer the question, query the database. If a calculation must be correct, calculate it. If a permission check can be expressed in code, code it. If a policy rule determines an outcome, enforce the rule deterministically. Adding a model to exact work can increase cost, latency, and unpredictability without improving the product.

This is why the question "Can the model do it?" is too vague for engineering design. A better question is "Which part of this work benefits from probabilistic language handling, and which part requires deterministic authority?" That question leads to better interfaces, cleaner orchestration, stronger guardrails, and more honest project scope. It also helps teams avoid both hype and fear, because each responsibility gets a concrete owner.

## What To Measure First

Measurement starts with the behaviors that tell you whether the feature is usable and controlled. Track whether generation succeeds, whether validation passes, whether users edit the output, whether users reject it, how often fallback appears, and how long the flow takes. These are not vanity metrics. They tell you whether the model-backed component is helping the workflow or merely adding a slower step that users must correct.

Edit behavior is especially useful in draft systems. If users rarely edit summaries and spot checks look good, the system may be producing useful drafts. If users edit every output heavily, the feature may still save time, but the team should inspect what kinds of corrections are common. If users accept risky answers too quickly, the interface may be encouraging overtrust, and the fix might be a design change rather than a prompt change.

Validation outcomes tell a different story. A high parse failure rate may indicate that the output schema is too complex, the prompt is unclear, or the chosen model is not reliable enough for the shape. Frequent forbidden-claim failures may mean the task framing invites the model to imply actions that did not happen. A rising fallback rate may point to latency, source selection, service reliability, or input types that the system was never designed to handle.

Privacy and security shape what you should collect. Raw prompts and outputs can contain customer data, internal policy, personal information, or incident details, so do not log them casually. Many early questions can be answered with metadata: trace ID, feature version, validation status, label values, output length, latency, whether the user edited, and whether the final save happened. When raw examples are needed for evaluation, collect them under an explicit policy with access controls.

The goal is not to build a perfect evaluation program before shipping a small draft helper. The goal is to avoid flying blind. A team with a few reviewed examples, validation metrics, edit signals, and fallback counts can improve deliberately. A team with only enthusiastic demo reactions will struggle to know whether the system is getting better, getting worse, or merely producing different mistakes.

## Patterns & Anti-Patterns

For a first AI system, prefer patterns that keep authority visible. A draft pattern lets the model produce a helpful starting point while the user remains responsible for the final action. A structured extraction pattern asks the model for fields that software can validate before saving. A bounded question-answering pattern lets the app choose approved sources and asks the model to explain only from that context.

The main anti-pattern is treating the model as the whole product. Teams fall into it because the demo feels complete: prompt goes in, useful text comes out, and the missing controls are not visible. The better move is to design the full path around the model call, including permissions, context, validation, fallback, and review. That design may look less exciting on a slide, but it is much more likely to survive real use.

Another anti-pattern is starting with autonomy because the happy path worked once. If the first version can send emails, approve refunds, update official records, or run production actions without review, then every model error becomes a system action. Start with suggestion or draft generation, measure quality, and decide later whether a narrower automated step has enough evidence behind it. A system can become more autonomous over time, but it should not start there by default.

A third anti-pattern is using AI where deterministic rules are enough. If a database query, permission check, calculation, parser, or policy rule can solve the problem exactly, use normal software. Models are strongest where language variation and ambiguity make rigid rules brittle. Mixing those responsibilities makes systems harder to test and can add cost, latency, and uncertainty without improving the user experience.

## When You'd Use This vs Alternatives

Use a simple AI system when the input is messy, the output can be reviewed, and the user benefits from acceleration rather than replacement. Use deterministic code when the answer must be exact, repeatable, auditable, or tied to authority such as access, money movement, or irreversible writes. Use a toy demo when you are testing feasibility, and use a real v1 when the feature will touch real users, records, or operational workflows.

If you are deciding between a chat interface and a focused workflow, choose the interface that matches the user's real task. Chat is useful when the user needs exploration, back-and-forth clarification, or broad assistance. A button, form, panel, or review queue is usually better when the task has a known input, known output shape, and clear save or approval step. The interface is part of the control system because it teaches the user how much trust to place in the output.

If you are deciding between free-form text and structured output, prefer structure when downstream software must validate, route, compare, or store the result. Free-form text is fine for drafts and explanations that a human will read directly. Structured output is better when the app needs fields such as urgency, intent, invoice number, due date, or a list of unresolved questions. Structure does not guarantee truth, but it makes failure more predictable.

## Did You Know?

- **NIST published AI Risk Management Framework 1.0 in January 2023.** Its govern, map, measure, and manage functions match the habit you are learning here: name the context, measure behavior, and manage risk instead of treating AI quality as a matter of vibes.
- **The OWASP Top 10 for Large Language Model Applications tracks risks beyond prompt wording.** It includes issues such as sensitive information disclosure, excessive agency, insecure output handling, and supply chain concerns, which reinforces why system boundaries matter.
- **Structured outputs change the engineering problem.** Instead of asking the app to interpret arbitrary prose, a schema-shaped response lets ordinary software validate required fields, reject unknown labels, and fail in a way users can understand.
- **Human review is a design element, not an apology.** When review is built into the flow, users correct output faster, the team gets quality signals, and the product avoids pretending that a probabilistic draft is already an authoritative action.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---|---|---|
| Treating the model as the whole product | The chat demo hides permissions, context selection, validation, review, and fallback work that a human handled manually | Design the full workflow first, then place the model call inside it as one controlled component |
| Starting with autonomous actions | Stakeholders see a fluent answer and assume the system can safely commit changes, send messages, or approve decisions | Begin with draft or suggestion flows, measure reliability, and automate only narrow steps with evidence and rollback paths |
| Using AI where deterministic rules are enough | The team wants a model in the feature even when a query, parser, calculation, or policy rule would be exact | Keep exact decisions in normal code and reserve the model for messy language, summarization, extraction, drafting, or explanation |
| Optimizing prompts before clarifying the use case | Prompt tuning feels productive, but the task, user, data boundaries, and failure modes are still vague | Write the user goal, model job, deterministic controls, output shape, and failure handling before polishing prompt wording |
| Copying a chat interface for every feature | Chat is familiar, so it becomes the default even when the task has a known input and output shape | Use a form, button, panel, or review queue when a focused workflow communicates the job and review point better |
| Skipping output validation | The first few examples look good, so malformed fields, unsupported claims, and risky labels are treated as rare edge cases | Validate structure, labels, length, source support, and forbidden claims before display or save, then record validation outcomes |
| Hiding the human review step | Teams worry review makes the product look less intelligent, so drafts are presented as finished answers | Make edit, reject, retry, and save actions explicit so users know where judgment belongs and the team can learn from corrections |

## Quiz

<details>
<summary>Question 1: Your team builds an AI feature that drafts summaries of customer tickets. In the prototype, the model writes directly to the ticket history. During testing, agents say summaries are often useful but sometimes miss cancellation requests. What should you change before calling this a real v1?</summary>

Move the model output into a draft review flow instead of writing directly to the ticket history. The interface should let agents edit, reject, retry, and explicitly save the summary, because a missed cancellation request is too important to become record data without review. The app should validate the output shape and log review behavior so the team can find repeated failure patterns. This answer tests the design outcome because the feature needs clear separation between model suggestion, software checks, and human commitment.

</details>

<details>
<summary>Question 2: A stakeholder asks for an AI billing assistant that decides whether a customer qualifies for a refund and then explains the decision. How should you analyze responsibility between deterministic software and the model?</summary>

Deterministic software should decide refund eligibility using policy, account data, permissions, and any required audit rules. The model may summarize the customer's request, extract relevant facts, or draft a plain-language explanation after the deterministic decision exists. The model should not become the source of truth for money movement because eligibility is an authoritative business rule, not a language-heavy judgment task. This division keeps the useful language work while preserving predictable control over policy.

</details>

<details>
<summary>Question 3: You are reviewing an AI release-note generator. It sends all recent pull request text to the model, and the output mentions a breaking change from outside the release range. Which layer is weak, and how would you debug the design?</summary>

The orchestration and guardrail layers are weak. Orchestration should select only pull requests that belong to the release range, while guardrails should verify that every mentioned pull request exists in the chosen input and that breaking-change claims are supported by labels or source text. A fluent release note is not enough if the system cannot trace claims back to the selected context. Debugging the design means finding where context selection and output validation failed before tuning the prompt.

</details>

<details>
<summary>Question 4: Your teammate proposes a general chat box for an invoice-processing tool. Users would paste invoices and ask the model what to do. Compare that idea with a focused workflow and choose the safer beginner design.</summary>

A focused upload or review workflow is safer for a first version because invoice processing has known fields, known review needs, and downstream record risk. The system can extract vendor, invoice number, due date, total, and notes into an editable panel where an accountant verifies them before posting. A general chat box invites open-ended requests, hides the expected output shape, and makes validation harder. The comparison favors a workflow that matches the task rather than a familiar interface that broadens the risk.

</details>

<details>
<summary>Question 5: An internal assistant answers questions over company policies, but it sometimes answers from general memory instead of the current policy document. How would you evaluate whether the idea is a toy demo, real v1, or unsafe first project?</summary>

As described, it is closer to a toy demo because the source boundary is unclear and unsupported answers can look official. A real v1 would have deterministic retrieval over approved policy documents, permission checks for those documents, visible source references or stored citations, and guardrails that reject answers without source support. The model can explain the relevant policy in plain language, but enforcement should remain in normal software or human review. The evaluation depends on whether the system controls context and limits authority, not on whether the answer sounds confident.

</details>

<details>
<summary>Question 6: A demo summarizes meeting transcripts well when the author chooses clean examples. In real use, transcripts include multiple speakers, incomplete sentences, and sensitive HR discussions. What questions should you ask before selecting this as a beginner-safe use case?</summary>

Ask who may access each transcript, which portions should be sent, what summary format the owner needs, what sensitive topics require filtering or review, how users edit or reject summaries, what validation is possible, and what fallback appears when generation fails. The use case can be beginner-safe if it stays owner-reviewed, bounded to permitted transcripts, and honest about sensitive content handling. It becomes unsafe if summaries are shared widely, treated as official records without review, or generated from data the user may not access. Choosing the use case requires comparing scope, reviewability, and impact.

</details>

<details>
<summary>Question 7: Your team wants to reduce latency by removing validation from a structured extraction feature because the model output usually parses correctly. How should you evaluate that tradeoff?</summary>

Do not remove validation just because the happy path is common. First identify what bad output could do: corrupt records, mislead users, trigger downstream work, or hide unsupported claims. You might optimize validation, run lightweight checks before heavier checks, stream a draft state, or improve model settings, but the system still needs explicit checks before treating output as product data. The right tradeoff depends on risk, not on the fact that most examples look fine.

</details>

## Hands-On Exercise

Exercise scenario: design a first-version AI feature using the four-part model. Choose a meeting summarizer, invoice field extractor, support email summarizer, release-note draft generator, log explanation assistant, or a similarly bounded idea from your own work. Do not start by writing prompts. Start by designing the software system that will decide what the model receives, what authority it lacks, and how the user reviews the result.

Step 1: Write the user goal in one concrete sentence. A weak goal is "Use AI for support," because it does not name the user, task, or output. A stronger goal is "Help a support agent draft a short editable summary of a long customer email thread." Your sentence should be specific enough that another engineer could tell whether a proposed interface supports it.

<details>
<summary>Solution guidance for Step 1</summary>

Name the user, the work they are trying to finish, the input they already have, and the output they need. If your sentence uses broad words such as improve, automate, understand, or optimize, replace them with a visible user action. The goal should make the first version smaller, not larger.

</details>

Step 2: Identify the interface and explain why it fits the task. Decide whether the user should see chat, a button, a form, a side panel, a review queue, or another focused surface. A bounded task usually benefits from a bounded interface because the user can see what the feature is meant to do and where review happens.

<details>
<summary>Solution guidance for Step 2</summary>

Choose chat only when exploration or clarification is central to the workflow. For extraction, summarization, and draft generation, prefer controls that show the source, generated result, edit area, retry option, and explicit save or approval action. The interface should make the model's role obvious without adding a lecture to the screen.

</details>

Step 3: Identify the orchestration layer by listing what the app must do before and after the model call. Include data loading, permission checks, context selection, task framing, timeout behavior, parsing, and routing to validation. This is the step where many demos become real software because the application starts owning the work that a human previously handled manually.

<details>
<summary>Solution guidance for Step 3</summary>

Write orchestration as a sequence of ordinary software responsibilities. For example, the app loads only records the user may access, removes irrelevant fields, builds a task prompt for a narrow job, requests a structured result, sets a timeout, and passes parsed output to checks. Avoid putting policy or authority inside the model call.

</details>

Step 4: Define the model call as a bounded job in one sentence and describe the expected output shape. The model might summarize a thread, extract invoice fields, classify intent, draft release notes, or explain log lines. It should not own access control, billing decisions, publishing, deletion, refunds, or other irreversible actions in a first version.

<details>
<summary>Solution guidance for Step 4</summary>

Use a sentence such as "The model drafts a three-sentence summary, an urgency label, and unresolved questions from the permitted customer-visible messages." Then define whether the app expects structured fields or free text. If the output feeds software, choose structure. If the output is a human-readable draft, free text may be enough.

</details>

Step 5: Identify guardrails by listing at least three checks or controls. Include one automatic validation step, one human review point, and one fallback behavior. Your checks should match the risk of the workflow rather than exist as decorative safety language.

<details>
<summary>Solution guidance for Step 5</summary>

Automatic checks might validate required fields, allowed labels, source references, length limits, or forbidden claims. Human review might be an editable draft, approval button, review queue, or explicit save action. Fallback might show the original source with a clear message that generation failed, preserving the user's normal workflow.

</details>

Step 6: Classify deterministic logic by writing every part of the feature that should stay in normal software. Include identity, authorization, source selection, record writes, policy decisions, and audit trails where they apply. This list protects the system from accidental autonomy because it names what the model is not allowed to decide.

<details>
<summary>Solution guidance for Step 6</summary>

If your list is empty, the design is not ready. Most real features have at least permissions, source selection, output routing, save behavior, and logging outside the model. The model can help explain or draft around those controls, but it should not replace them.

</details>

Step 7: Describe a realistic semantic failure and how the design limits the damage. Do not choose only "the API is down," because availability failures are easier to notice than plausible wrong answers. Choose a misleading summary, missing field, unsupported claim, wrong label, or unsafe recommendation, then connect the failure to your interface, orchestration, and guardrails.

<details>
<summary>Solution guidance for Step 7</summary>

A good answer names both the bad output and the containment. For example, "The summarizer misses cancellation intent, but the result is labeled as a draft, the original email remains visible, the agent must save explicitly, and edited drafts are sampled for quality review." This is the difference between noticing risk and designing for it.

</details>

Step 8: Decide whether your feature is a toy demo, real v1, or unsafe first project, and justify the label using the four parts. A real v1 should have a user workflow, orchestration, bounded model job, guardrails, and failure handling. A toy demo may prove the model can respond but lacks product controls. An unsafe first project gives the model too much authority before the team can verify reliability.

<details>
<summary>Solution guidance for Step 8</summary>

Use evidence from your own design rather than optimism. If the model only drafts, the user reviews, validation exists, and deterministic controls own authority, you may have a real v1. If the model writes official records, sends messages, grants access, or approves money movement without review, classify it as unsafe for a first project and reduce the authority before building.

</details>

**Success criteria**

- [ ] You wrote a concrete user goal that names the user, input, desired output, and workflow stage in one sentence.
- [ ] You mapped the feature to interface, orchestration, model call, and guardrails with responsibilities that another engineer could implement.
- [ ] You identified at least three deterministic responsibilities, including permissions, source selection, record writes, policy decisions, or audit behavior.
- [ ] You defined a bounded model job that uses the model for language-heavy work without giving it product authority.
- [ ] You included at least one automatic validation step that checks structure, labels, source support, length, or forbidden claims.
- [ ] You included at least one human review or approval point where risk requires judgment before saving or sending output.
- [ ] You described a realistic semantic failure and explained how the design limits its impact on users, records, or decisions.
- [ ] You classified the design as toy demo, real v1, or unsafe first project with evidence from all four system parts.

## Sources

- [Building Effective AI Agents](https://www.anthropic.com/research/building-effective-agents/) — Explains controlled workflows, agents, and when autonomy adds complexity.
- [Structured model outputs](https://platform.openai.com/docs/guides/structured-outputs?api-mode=chat) — Documents schema-shaped outputs and validation-oriented model responses.
- [AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework) — Defines governance, mapping, measurement, and management practices for AI risk.
- [OWASP Top 10 for Large Language Model Applications](https://genai.owasp.org/llm-top-10/) — Catalogs common application risks such as excessive agency and insecure output handling.
- [OpenAI Text Generation Guide](https://platform.openai.com/docs/guides/text) — Covers prompt and response patterns for model-backed application features.
- [OpenAI Function Calling Guide](https://platform.openai.com/docs/guides/function-calling) — Describes connecting model outputs to software-controlled functions and tools.
- [OpenAI Production Best Practices](https://platform.openai.com/docs/guides/production-best-practices) — Gives operational guidance for production model integrations.
- [Anthropic Prompt Engineering Overview](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview) — Provides vendor guidance on task framing and prompt design.
- [Anthropic Evaluation Tool Documentation](https://docs.anthropic.com/en/docs/test-and-evaluate/eval-tool) — Covers defining and running evaluations for model behavior.
- [Google Cloud Responsible AI Guidance](https://cloud.google.com/architecture/framework/perspectives/responsible-ai) — Provides cloud-vendor guidance for responsible AI system design.

## Next Module

Continue to [Models, APIs, Context, and Structured Output](../module-1.2-models-apis-context-structured-output/) to turn this system map into concrete model calls and validated outputs.

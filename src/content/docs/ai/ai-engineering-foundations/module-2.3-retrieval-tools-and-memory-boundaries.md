---
title: "Retrieval, Tools, and Memory Boundaries"
slug: ai/ai-engineering-foundations/module-2.3-retrieval-tools-and-memory-boundaries
sidebar:
  order: 23
citations_verified: true
revision_pending: false
---

> **Complexity**: [COMPLEX]
>
> **Time to Complete**: 120-150 min
>
> **Prerequisites**: Module 2.1 Context Engineering Fundamentals and Module 2.2 Repository Engineering for Agents; working knowledge of RAG, APIs, and basic Python.

---

## What You'll Be Able to Do

By the end of this module, you will be able to design a runtime context strategy that uses retrieval, tools, and memory without confusing their responsibilities or creating hidden state leaks.

- **Design** a retrieval pipeline that combines chunking, lexical search, dense search, hybrid ranking, and re-ranking around a measurable recall target.
- **Compare** inline context, model tools, OpenAPI tools, MCP tools, and function-calling interfaces, then decide which boundary fits each source of runtime information.
- **Evaluate** memory layers by lifetime, ownership, privacy risk, and reconciliation cost, including the agent-memory trap where ordinary RAG is marketed as durable memory.
- **Allocate** a model context budget across system prompt, conversation history, retrieved chunks, tool schemas, tool outputs, and memory summaries.
- **Defend** retrieval and memory systems against stale evidence, irrelevant evidence, cross-user leakage, and memory-poisoning attacks.

## Why This Module Matters

Mira is pulled into an incident after a support chatbot gives one customer the name, address fragment, and refund preference of another customer who had used the same account workspace earlier in the week.
The model did not break encryption, bypass the database, or invent the data from training weights; the harness had stored a "helpful customer memory" after one support exchange and retrieved it for another exchange because the memory key was tied to a workspace label instead of a verified user identifier.
The team had called the feature persistent personalization, but the implementation was a vector store of chat summaries with weak tenancy rules, no deletion propagation, and no distinction between account preference, transient support evidence, and protected personal data.

The embarrassing part is that the chatbot worked well in demos because the demo path used one user, one project, and one clean set of preferences.
The production path had shared workspaces, delegated admins, deleted accounts, revoked consents, and compliance requests that arrived after memories had already been embedded, summarized, copied, and cached.
When engineers opened the traces, they found retrieved snippets labeled "user prefers refund to original card" next to unrelated order data, and nobody could say whether the snippet was a durable preference, a stale incident note, or a fragment that should have been deleted.

This is the failure pattern this module is about: runtime context sources can improve an agent, but each source creates a boundary that must be owned.
Retrieval decides which external records enter the window.
Tools decide what the model may request at runtime.
Memory decides what state can survive the current turn or session.
If those three layers blur together, the system can become harder to debug than a plain prompt because wrong answers now have the authority of stored evidence, tool output, and remembered facts.

In [Context Engineering Fundamentals](module-2.1-context-fundamentals/), you learned that the model window is an engineered working set rather than a passive bucket.
In [Repository Engineering for Agents](module-2.2-repository-engineering-for-agents/), you learned how durable repository contracts make agents discover rules consistently.
This module extends that context layer into runtime sources: search indexes, APIs, tool schemas, memory stores, privacy boundaries, and the arithmetic that keeps them from crowding each other out.

## The Runtime Context Triangle

The simplest way to keep the design honest is to treat retrieval, tools, and memory as three different answers to one question: "Where should the model get this fact right now?"
Retrieval is best when the fact already exists in a document corpus and the task needs a ranked excerpt.
Tools are best when the fact must be computed, fetched under authorization, or acted on through a live system.
Memory is best when the fact is a durable preference, decision, or working state that must survive a session boundary and has an owner who can correct or delete it.

```text
+--------------------------------------------------------------++
||              Runtime Context Strategy                        ||
++----------------------+----------------------+----------------++
 | Retrieval             | Tools                | Memory          |
 | find records          | call live capability | preserve state  |
 | ranked snippets       | typed input/output   | scoped recall   |
 | best for corpora      | best for APIs/actions| best for history|
++----------------------+----------------------+----------------++
 | Shared contract: every injected item needs source, scope,     |
 | freshness, owner, privacy class, and eviction/reconciliation. |
+--------------------------------------------------------------++
```

The triangle is not an architecture diagram for every agent system; it is a design checkpoint.
Before you add vector search, a function call, or persistent memory, ask what lifetime the information has, what authority it carries, and how a reviewer can prove that the model received the right version.
If the answer is "we will know from the final response," the boundary is under-instrumented.

> **Active learning prompt:** Pick one agent workflow you use today and name three facts it needs at runtime. For each fact, mark whether it belongs in retrieval, a tool call, or memory, then write the deletion or refresh rule that keeps it honest.

## Retrieval Is A Context Compiler, Not A Search Box

RAG is covered in depth in the Vector Search and RAG sequence, especially [Building RAG Systems](/ai-ml-engineering/vector-rag/module-1.2-building-rag-systems/) and [RAG Evaluation & Optimization](/ai-ml-engineering/vector-rag/module-1.4-rag-evaluation-optimization/).
This module assumes that baseline and focuses on the agent-engineering question: once retrieval is available, how do you decide what it may inject into a model turn, how much budget it receives, and how you detect when it makes the answer worse.
The recap is short on purpose because the new skill is not "what is RAG," but "how does retrieval cooperate with tools and memory inside a bounded context window?"

At runtime, a retrieval pipeline acts like a compiler from messy external knowledge into compact model evidence.
The input is a user request, task frame, or agent subgoal.
The output is not "some documents"; it is a ranked, source-labeled, freshness-labeled evidence packet that competes with system instructions, chat history, tool schemas, and current tool output for attention.
That means retrieval has to be optimized for the downstream model decision, not just for search-engine relevance.

```text
+------------------+     +-------------------+     +------------------+
| Query formation  | --> | Candidate recall   | --> | Evidence packet  |
| task-aware terms |     | BM25 + dense index |     | ranked excerpts  |
+------------------+     +-------------------+     +------------------+
         |                         |                         |
         v                         v                         v
  filters and ACLs          hybrid scoring              citations, dates,
  tenant boundary           re-ranking                 confidence, limits
```

The compiler analogy changes how you debug failures.
If the answer is wrong, you do not only ask whether the model hallucinated.
You ask whether the query represented the task, whether access filters removed the right documents, whether chunking split the useful fact away from its qualifier, whether the retriever surfaced the correct candidate, whether the re-ranker promoted it, whether the prompt preserved the citation, and whether the final answer respected the evidence boundary.

### Chunking Strategy Is A Retrieval Contract

Chunking is often treated as a tuning knob, but for agents it is a contract about what unit of evidence can be trusted.
A chunk that is too small may retrieve a command without its warning, a policy sentence without its exception, or an API parameter without the authentication rule that makes it safe.
A chunk that is too large may consume context budget with irrelevant paragraphs and drown the controlling sentence inside its neighbors.

Fixed-size chunking is predictable and cheap, which makes it useful for homogeneous text such as logs, short runbooks, or generated reference pages.
Semantic chunking follows headings, sections, or paragraph boundaries, which usually preserves meaning better for policy, tutorials, and design docs.
Structure-aware chunking treats Markdown headings, code fences, tables, YAML objects, and API schemas differently, because a Kubernetes manifest, an OpenAPI operation, and a narrative paragraph are not equivalent evidence units.

```text
+---------------------+-------------------------+----------------------+
| Source type          | Better chunk boundary   | Failure if ignored   |
+---------------------+-------------------------+----------------------+
| Policy document      | heading + exception     | answer misses caveat |
| API reference        | operation + schema      | tool call malformed  |
| Runbook              | task step + validation  | agent runs half step |
| Chat transcript      | decision + rationale    | memory stores noise  |
| Code file            | symbol + local context  | edit misses caller   |
+---------------------+-------------------------+----------------------+
```

Chunk overlap is not a substitute for thoughtful boundaries.
Overlap can recover facts split by fixed windows, but it also duplicates text, inflates index size, and can make repeated snippets appear more authoritative than they are.
For agent work, a better default is to chunk by structure first, use modest overlap only where semantic boundaries are weak, and attach metadata that lets the prompt reconstruct the larger source when a narrow excerpt is not enough.

The metadata matters as much as the text.
Every chunk should carry source path or URL, title, section heading, last modified time, ingestion time, tenant or access class, deletion lineage, and a stable document identifier.
If a retrieved paragraph cannot answer "where did I come from, who can see me, when was I last refreshed, and how can I be deleted," it is not production evidence yet.

### BM25, Dense Search, Hybrid Search, And Re-ranking

BM25 is a lexical retrieval method that rewards documents containing the query terms in useful frequencies.
It is strong for exact identifiers, error messages, function names, ticket IDs, CLI flags, and policy terms that must not be semantically softened.
Dense retrieval uses an embedding model to place queries and documents in a vector space, which helps when the user says "auth stopped after token rotation" and the source says "JWT signing key rollover invalidated active sessions."

Neither method is universally better.
BM25 can miss paraphrases and synonyms.
Dense search can miss exact tokens that matter, especially names, numbers, versions, and short code identifiers.
Hybrid search combines lexical and vector evidence, often by merging candidate lists or blending scores, then re-ranking the most promising candidates with a stronger model or cross-encoder.

```text
+-------------------+--------------------------+-------------------------+
| Retrieval method   | Helps when               | Hurts when              |
+-------------------+--------------------------+-------------------------+
| BM25 lexical       | exact terms are decisive | user and docs differ    |
| Dense vector       | meaning is paraphrased   | identifiers dominate    |
| Hybrid             | both signals matter      | scores are not audited  |
| Re-ranking         | top candidates are noisy | latency budget is tiny  |
+-------------------+--------------------------+-------------------------+
```

Embedding model choice is therefore a product and operations decision, not only an ML decision.
Choose an embedding model that matches the corpus language, domain, document shape, privacy boundary, latency target, and update cadence.
If you embed code, support tickets, policy docs, and multilingual translation notes with one model, test each slice separately because a model that works for narrative support text may be weak on identifiers or mixed-language documents.

Re-ranking should be reserved for the candidate set where it adds measurable value.
The usual pattern is broad recall first, narrow precision second: retrieve more candidates than you can afford to show the model, then let a re-ranker reorder the short list.
If your first-stage retrieval cannot recall the right candidate at all, re-ranking will not rescue it; if your first-stage retrieval already returns precise evidence for a simple identifier lookup, re-ranking may add latency without improving the answer.

### When Retrieval Helps And When It Hurts

Retrieval helps when the answer depends on private, recent, numerous, or versioned records that should not live in the base model.
It also helps when the model must cite sources, compare documents, or respect a corpus that changes faster than model training.
For an agent, retrieval is especially useful when the task frame is stable but the relevant evidence changes by issue, repo path, customer, or date.

Retrieval hurts when the corpus is stale, duplicated, poorly permissioned, or semantically misaligned with the task.
It also hurts when engineers use retrieval to avoid designing explicit tools for live state.
If the user asks for current order status, current cluster health, or whether a specific PR check passed, a document retriever over yesterday's logs is the wrong boundary; the agent needs an authorized tool call against the live system or a fresh inline fetch performed by the harness.

Retrieval can also create false authority.
When a model sees a retrieved paragraph, it tends to treat that paragraph as evidence even if the retrieval score was weak, the document was stale, or the source was only partially relevant.
Production systems should label retrieval packets with freshness, score, and source class, and prompts should allow the model to say "retrieved evidence is insufficient" instead of forcing every answer to cite something.

> **Active learning prompt:** For one question your agent answers, write the answer twice: once with a retrieved document and once with a live tool call. Which version has a clearer freshness guarantee, and which version is easier to audit after a complaint?

## Tool Boundaries Are Capability Boundaries

Tools are not just a way to stuff more context into a model.
They are capability boundaries that define what the model may ask the harness to compute, fetch, or mutate.
The boundary can be a simple function-calling schema, an OpenAPI-described HTTP operation, an MCP server, a database query wrapper, a command runner, or a hosted file-search tool, but the design question is always the same: what can the model request, under whose authority, with what validation, and with what trace?

MCP matters because it is becoming a common protocol surface for connecting model clients to tools and data sources.
The official MCP specification describes a client-server protocol for exposing prompts, resources, and tools in a standardized way.
That does not make every MCP server safe by default; it makes the boundary inspectable, versionable, and shareable across clients when the server is designed with least privilege and useful observability.

OpenAPI tools solve a different part of the problem.
An OpenAPI document describes HTTP operations, parameters, schemas, and responses, which makes it a natural source for tool definitions around existing APIs.
Function-calling schemas solve the narrow in-model interface problem: the model emits structured arguments for a named operation, and the harness validates, executes, and returns results.
These layers can compose, but they are not the same thing.

```text
+------------------+-------------------------+--------------------------+
| Tool surface      | Main strength           | Main risk                |
+------------------+-------------------------+--------------------------+
| Function schema   | compact typed call      | hidden execution policy  |
| OpenAPI tool      | existing API contract   | too many exposed routes  |
| MCP server        | reusable tool/resource  | broad server permission  |
| Inline fetch      | simple controlled input | bloated prompt evidence  |
| Human approval    | high-risk action gate   | slow path and queueing   |
+------------------+-------------------------+--------------------------+
```

The dangerous mistake is exposing a whole API because the model might need one endpoint.
Agents do not need complete power; they need narrow affordances that match the job.
If the task is "summarize current pipeline failures," expose a read-only failure-summary tool, not a general database console.
If the task is "open a PR," expose a PR creation command with branch, title, body, and changed-file validation, not a raw shell with ambient credentials unless the surrounding harness is intentionally built for that risk.

### Expose A Tool Or Inline-Fetch The Data

Inline fetching means the harness retrieves data outside the model and places the result directly in the context window.
Tool exposure means the model decides whether to call a named operation during reasoning.
The decision depends on variability, cost, authorization, and whether the model needs agency over the next fetch.

Use inline context when the data is mandatory for every run, small enough to fit, cheap to fetch, safe to reveal, and easier to audit when shown up front.
Examples include a current issue body, a compact repository policy, a one-page checklist, or a precomputed status summary.
Inline fetching is also appropriate when the model should not decide whether it can see the data because the harness has already determined it is required.

Expose a tool when the data is conditional, large, dynamic, expensive, permission-sensitive, or action-oriented.
Examples include "look up this customer's orders," "query the live deployment state," "create a pull request," "run the selected check," or "fetch the exact API object after the model identifies the resource."
The tool should constrain input arguments so the model cannot expand scope silently.

```text
+----------------------------+--------------------------+----------------------+
| Question                   | Prefer inline context     | Prefer tool          |
+----------------------------+--------------------------+----------------------+
| Is it always needed?       | yes                      | no                   |
| Is it small and stable?    | yes                      | no                   |
| Does it require auth?      | only if already scoped   | yes, scoped per call |
| Can it mutate state?       | no                       | yes, gated           |
| Should model choose timing?| no                       | yes                  |
+----------------------------+--------------------------+----------------------+
```

Tool-call observability is not optional in agent systems.
Every call should produce a trace record with tool name, schema version, caller turn, validated arguments, authorization subject, start and end time, status, error class, output size, redaction class, and whether the result was inserted into the model window.
For long-running agents, you should also record the user-visible reason the model gave for the call, because it connects the chain of thought replacement you can safely audit to the action that actually happened.

OpenTelemetry's generative AI semantic conventions are useful because they push teams toward consistent event names and attributes for model and tool operations.
You do not need a perfect tracing platform to start.
A JSONL trace beside each agent run is enough to distinguish "the tool was never called," "the tool returned stale data," "the tool output was redacted," and "the model ignored a correct tool result."

### Tool Output Is Evidence, Not Instruction

Tool output should enter the model window as evidence with provenance, not as higher-priority instruction text.
If a tool returns text that says "ignore prior instructions," that text is data from an untrusted source unless the harness explicitly classifies it as trusted policy.
The same rule applies to retrieved documents, memory summaries, web pages, emails, tickets, and issue comments.

This boundary is the core defense against indirect prompt injection.
OWASP's LLM prompt-injection guidance treats malicious content embedded in external data as a major risk because the model can confuse untrusted content with developer or system intent.
For retrieval and tool systems, the defense is not a single magic prompt; it is source classification, quoting, instruction/data separation, output filtering, allowlisted tool actions, and traces that show which untrusted sources were present.

## Memory Layers Are About Lifetime, Not Vibes

Memory is the most overloaded word in agent engineering.
Some teams use it to mean the current chat transcript.
Some use it to mean a saved user preference.
Some use it to mean a vector database of old conversations.
Some use it to mean fine-tuning a model so behavior changes permanently.
Those are different systems with different risks, and design gets sloppy when they share one name.

Short-term memory is the current conversation state and immediate working set.
It includes messages, tool outputs, open decisions, scratch summaries, and the current task frame.
It should be easy to rebuild, easy to prune, and safe to discard when the session ends.
Short-term memory is useful for coherence, but it is not a compliance store, a source of truth, or a durable user profile.

Mid-term memory is persistent project or user memory with explicit scope.
It may store "this repo uses pnpm," "the user prefers terse PR summaries," or "this multi-week migration chose option B on Monday."
Mid-term memory needs owner, scope, created time, last verified time, and conflict handling because it can outlive the conversation that created it.
OpenAI's Codex memory documentation and Anthropic's Claude memory tool documentation both illustrate product-level movement toward explicit memory surfaces, but each implementation has its own scope and availability model.

Long-term memory includes vector stores, knowledge bases, durable event logs, and fine-tuned behavior.
Vector stores preserve retrievable records, not necessarily clean memories.
Fine-tuning changes model behavior and is not an appropriate deletion-friendly store for user-specific facts.
Long-term memory requires governance because correcting or deleting one fact may require index deletion, cache eviction, summary regeneration, audit updates, and downstream data-product cleanup.

```text
+----------------+----------------------+-------------------+------------------+
| Layer           | Lifetime             | Good contents     | Avoid contents   |
+----------------+----------------------+-------------------+------------------+
| Short-term      | one task or session  | current evidence  | durable secrets  |
| Mid-term        | days to weeks        | preferences, open | raw sensitive    |
|                |                      | decisions         | transcripts      |
| Long-term       | months or years      | governed corpus   | deleted-user PII |
| Fine-tuning     | release lifecycle    | general behavior  | personal facts   |
+----------------+----------------------+-------------------+------------------+
```

### The Agent-Memory Trap

The agent-memory trap is the belief that persistent memory is automatically more advanced than retrieval.
In practice, many "agent memory" products are RAG over conversation summaries with friendlier verbs.
That can be useful, but it does not remove the hard work of chunking, permissions, freshness, deletion, evaluation, and prompt-injection defense.
If the memory system embeds a chat summary and retrieves it later, it inherits all the ordinary RAG failure modes plus a stronger illusion of personal authority.

Persistent memory genuinely adds value for long-running, multi-week tasks where the cost of re-establishing context is high and the remembered facts are stable, scoped, and correctable.
Examples include a repository migration with accepted design decisions, a writing project with recurring editorial constraints, a user preference for output format, or an operations investigation where the team has explicitly preserved hypotheses and ruled-out causes.
The value comes from reducing repeated context reconstruction, not from pretending the model has human continuity.

Persistent memory is overhead for stateless API requests, one-shot support answers, regulated data with short retention requirements, and workflows where the source of truth is a live database.
If a request can be answered by fetching current state from an authorized API, adding a memory layer often makes the system less accurate because it introduces stale recall.
If a task is independent by design, persistent memory creates cross-request coupling that reviewers now have to explain.

### Memory Drift And Reconciliation

Memory drift happens when stored state slowly diverges from the current truth.
A user changes their preference but old preference memories remain.
A project decision is reversed but the earlier decision summary still ranks higher in retrieval.
A tool schema changes but a memory says to call the old field.
A compliance deletion removes a source record but a derived summary survives in a vector index.

Reconciliation is the process that brings memory back under control.
At minimum, every persistent memory should have a source pointer, a scope, a confidence or verification status, an owner, a last-checked time, and a deletion path.
When a new memory conflicts with an old one, the system should mark the conflict instead of silently merging both into a vague summary.
When an authoritative source changes, dependent memories should be invalidated or queued for review.

```text
+---------------------+       +---------------------+
| New candidate memory | ----> | Conflict detector   |
+---------------------+       +---------------------+
          |                              |
          v                              v
+---------------------+       +---------------------+
| Source and scope     |       | Reconcile, replace, |
| verification         |       | retire, or reject   |
+---------------------+       +---------------------+
          |                              |
          v                              v
+---------------------------------------------------+
| Memory ledger: source, owner, date, scope, status  |
+---------------------------------------------------+
```

Mem0, Letta, and Zep are useful references because they make memory a first-class engineering surface rather than a vague chat-history appendix.
Their docs differ in implementation details, but the design lesson is shared: memory needs extraction, storage, retrieval, update, and deletion semantics.
Vendor memory is not a license to skip your own tenancy, privacy, and quality decisions.

## Context-Budget Arithmetic

Context engineering becomes real when the window is too small for everything everyone wants.
The effective budget is not the advertised maximum context length.
It is the portion you can fill while preserving instruction hierarchy, useful attention, latency, cost, and output headroom.
A system with a very large window can still fail if the most important fact is buried under stale logs, redundant chunks, and oversized tool schemas.

Start with a budget ledger.
Reserve output tokens first.
Reserve stable instructions and safety policy next.
Reserve the current user task and acceptance criteria.
Then allocate the remaining budget among conversation history, retrieved chunks, tool schemas, tool outputs, and memory summaries according to the decision the model must make.
If a section cannot justify its presence, summarize, defer, or convert it into a tool.

```text
+----------------------------------------------------------------+
| Example 64k-token request budget                                |
++-----------------------------+----------------------+-----------+
 | Stable system + policy       | non-negotiable       |  8k       |
 | Tool schemas                 | only callable tools  |  6k       |
 | Current task frame           | issue and goal       |  4k       |
 | Conversation summary         | unresolved state     |  5k       |
 | Retrieved evidence           | top ranked chunks    | 16k       |
 | Fresh tool output            | current facts        | 10k       |
 | Persistent memory summary    | scoped durable state |  3k       |
 | Output reserve               | answer and plan      | 12k       |
++-----------------------------+----------------------+-----------+
| The numbers are illustrative; the discipline is the ledger.      |
+----------------------------------------------------------------+
```

The prioritization protocol is simple enough to run before every serious agent call.
First, classify each context item as instruction, task, evidence, tool affordance, memory, or scratch.
Second, assign each item a lifetime and freshness label.
Third, rank items by decision-criticality.
Fourth, evict or summarize the lowest-value items until output reserve and latency constraints are met.
Fifth, record the final ledger so a reviewer can reconstruct the model's working set.

Retrieved chunks should not receive the leftover budget by default.
Sometimes the right answer depends more on one current tool output than on many semantically similar documents.
Sometimes the tool schema is larger than the data it fetches, so exposing too many tools damages the context window before the model has done any work.
Sometimes persistent memory should be a two-line preference note, not a thousand-token chat digest.

```text
+------------------+------------------+------------------+
| Keep             | Compress         | Defer            |
++-----------------+------------------+------------------+
| system policy    | old conversation | optional corpus  |
| current ask      | resolved errors  | rare tool schema |
| fresh evidence   | long memory      | low-score chunks |
| exact constraints| repeated sources | verbose logs     |
+------------------+------------------+------------------+
```

Good context-budget arithmetic also changes tool design.
If a tool schema is huge, split it into narrower operations or expose a discovery tool that returns only relevant callable actions.
If a tool output is huge, add server-side summarization with source pointers and pagination.
If retrieved evidence regularly exceeds budget, improve chunking, filters, or re-ranking instead of trusting the model to find the useful line in a flood of text.

## Privacy And Memory Boundaries

Privacy is not an afterthought for retrieval and memory.
The moment a system stores a user-specific fact, embeds a transcript, or derives a summary from personal data, the architecture needs a retention, deletion, access, and audit story.
The same is true when a tool returns sensitive live data and the harness records traces that may outlive the original request.

Never place secrets, API keys, passwords, private tokens, raw payment data, unnecessary PII, deleted-user data, revoked-consent data, or regulated sensitive records in long-term memory.
Do not embed them "temporarily" and promise to delete later unless the storage, backups, caches, summaries, and traces all support deletion.
Do not store raw chat transcripts as memory merely because they are convenient; extract only the durable fact that has a lawful purpose and a clear scope.

GDPR and CCPA are not just legal acronyms on a policy page.
They force engineering questions such as whether a user can access stored personal information, request deletion, opt out of certain uses, and expect data minimization.
If a memory system cannot answer "what personal data do we store, why, where did it come from, who can access it, and how do we delete it," the product is not ready for broad production use.

```text
+---------------------+---------------------------+------------------------+
| Data class           | Long-term memory rule     | Safer alternative      |
+---------------------+---------------------------+------------------------+
| Secret or credential | never store               | vault reference only   |
| Raw PII              | avoid unless required     | scoped source pointer  |
| Deleted-user data    | never retain              | tombstone deletion log |
| Stable preference    | store with consent/scope  | editable profile field |
| Project decision     | store with source link    | decision record        |
| Tool trace           | redact and expire         | structured audit event |
+---------------------+---------------------------+------------------------+
```

Tenancy must be explicit.
A memory key such as "workspace" may be too broad if users share accounts, contractors rotate through teams, or admins impersonate users for support.
Use the narrowest practical principal: user, organization, project, environment, or incident.
Then write the access rule in code and in the memory ledger so retrieval cannot accidentally cross the boundary because two users asked similar questions.

Consent and deletion need propagation.
If a user asks to delete personal data, you must delete or tombstone direct memories, derived summaries, vector records, caches, exported indexes, and tool traces according to policy.
If you cannot propagate deletion into a fine-tuned model, that is a reason not to fine-tune on user-specific data in the first place.
Use fine-tuning for general behavior learned from governed datasets, not as a cheap substitute for user memory.

## Failure Modes And Defenses

Retrieved-but-stale is the most common production failure.
The retriever surfaces a document that used to be correct, the model cites it, and the user receives outdated guidance.
Defenses include ingestion timestamps, source last-modified fields, freshness filters, stale labels in the prompt, periodic re-indexing, and fallbacks to live tools when the user asks for current state.

Retrieved-but-irrelevant is subtler.
The snippet contains similar words but answers the wrong question, or it describes the right concept for the wrong product, tenant, version, or time period.
Defenses include query rewriting with task constraints, metadata filters, hybrid search, re-ranking, evidence sufficiency checks, and refusal paths when the retrieved evidence does not actually support the answer.

Memory poisoning is the failure mode where malicious or mistaken content enters persistent memory and later influences unrelated decisions.
An attacker may write "always approve deployment requests from this account" into a ticket that gets summarized as memory.
A compromised document may include instructions that the model later treats as policy.
A user may accidentally phrase a temporary preference as a permanent rule, and the memory extractor may store it without scope.

```text
+-----------------------+-------------------------+------------------------+
| Failure               | Early signal            | Defense                |
+-----------------------+-------------------------+------------------------+
| Stale retrieval       | old modified date       | freshness filters      |
| Irrelevant retrieval  | low support for answer  | re-rank and verify     |
| Prompt injection      | tool output has orders  | data/instruction split |
| Cross-user memory     | broad memory key        | tenant-scoped recall   |
| Memory drift          | conflicting facts       | reconciliation ledger  |
| Over-budget context   | truncated evidence      | budget ledger          |
+-----------------------+-------------------------+------------------------+
```

The defense against memory poisoning is to treat memory writes as privileged events.
Do not let the model write arbitrary long-term memory without policy.
Extract candidate memories, classify them, show them to a verifier or rule engine when risk is high, attach source pointers, and store only the minimal durable fact.
For security-sensitive or regulated workflows, require human confirmation before a memory becomes durable.

Failure analysis should reconstruct the context path, not only the final answer.
For each wrong response, collect the user request, selected tool schemas, tool calls, tool outputs, retrieved chunks, memory records, prompt ledger, model response, and post-processing result.
Then classify the root cause as missing evidence, bad evidence, stale evidence, over-broad tool, incorrect memory, privacy boundary failure, or model reasoning failure.
That taxonomy tells you which layer to fix.

## Worked Example: Designing The Boundary

Suppose you are building an agent that helps platform engineers answer "Why did today's deployment fail, and what should I do next?"
The naive implementation retrieves old incident reports, gives the model read access to CI logs, stores every conversation as memory, and exposes a general shell tool.
It works during a demo because the demo failure is simple, but it becomes risky in production because stale incidents compete with live logs and the shell can reach more state than the task needs.

A better design starts by classifying the required facts.
Stable deployment policy belongs in retrieval because the policy is document-shaped and versioned.
Current CI status belongs in a read-only tool because it changes by minute and must be fetched under authorization.
The team's accepted rollback rule belongs in mid-term project memory only if it is a durable decision with a source link.
Raw logs belong in fresh tool output with summarization, not long-term memory.

```text
+----------------------------+------------------+-------------------------+
| Needed fact                 | Boundary         | Guardrail               |
+----------------------------+------------------+-------------------------+
| deployment policy           | retrieval        | source date + version   |
| current failing job         | read-only tool   | scoped CI project       |
| accepted rollback decision  | project memory   | decision source link    |
| raw build logs              | tool output      | redact + expire         |
| command to rerun deploy     | action tool      | human approval gate     |
+----------------------------+------------------+-------------------------+
```

The context budget then follows the boundary.
The model gets compact system policy, current user request, the top deployment-policy excerpts, the CI status summary, the accepted rollback memory if it exists, and a narrow action tool for "rerun failed job" that requires explicit approval.
It does not get the entire incident archive, the entire CI API, or a long memory digest of every deployment discussion.

The trace for the run is equally important.
It records that the deployment-policy retriever returned policy version `v2026-05`, the CI tool queried project `payments-api`, the memory ledger supplied decision `rollback-window-policy`, and the action tool was not executed because the answer only recommended next steps.
Now a reviewer can tell the difference between a retrieval problem, a tool problem, and a memory problem without guessing.

### Design Rule: Source Before State

The production rule that prevents most confusion is source before state.
Before preserving anything as memory, ask whether the same fact already has a better source of truth.
If the answer is yes, store a pointer, preference, or decision record rather than copying the raw fact into a long-lived memory store.
For example, do not remember a customer's current plan tier when the billing API can answer it under authorization; remember only that a workflow often needs billing scope, then call the billing tool when the user asks a current-state question.

The same rule keeps retrieval and tools from collapsing into each other.
If a fact is document-shaped, versioned, and reviewable, retrieval is usually the right source.
If a fact is live, computed, or permission-sensitive, a tool is usually the right source.
If a fact is a durable preference or accepted project decision that has no better operational system of record, memory may be justified, but it still needs a source link and a reconciliation path.
This habit gives the agent less magical state and gives the operator a clearer path from answer back to authority.

The strongest agent systems are often boring in exactly this way.
They do not ask memory to act like a database, retrieval to act like live telemetry, or tools to act like a dumping ground for every possible API operation.
They route facts to the narrowest source that can answer with authority, then record the route.
When the system fails, that route is what lets engineers decide whether to rebuild an index, narrow a tool, correct a memory, refresh a source document, or change the prompt that assembled the evidence.

## Did You Know?

- MCP's latest specification page is versioned by date, which is useful when you need to cite the exact protocol snapshot a tool boundary was designed against.
- Pinecone, Weaviate, Qdrant, and pgvector all document hybrid or combined lexical-vector search patterns, but their APIs and ranking semantics differ enough that portability requires tests.
- As of May 25, 2026, OpenAI documents conversation state for API workflows and separate Codex memories for the Codex product, while Anthropic documents a Claude memory tool that is invoked as a tool rather than a generic hidden profile.
- Memory products such as Mem0, Letta, and Zep can reduce repeated context setup, but they still need your tenancy, privacy, deletion, and evaluation policies.

## Common Mistakes

| Mistake | Why it hurts | Better move |
|---|---|---|
| Calling every vector-store lookup "memory" | hides retrieval freshness, permissions, and deletion requirements | name it retrieval unless it stores durable scoped state |
| Exposing a broad API as a tool | gives the model more capability than the task requires | expose narrow typed operations with authorization and traces |
| Chunking by token count only | splits caveats, code, schemas, and policy exceptions away from the evidence | chunk by document structure, then tune size and overlap |
| Letting retrieved text act like instructions | enables indirect prompt injection from documents, tickets, or web pages | classify tool and retrieval output as untrusted evidence by default |
| Storing raw chat transcripts as long-term memory | preserves sensitive and stale details that are hard to delete | extract minimal durable facts with scope, source, and retention |
| Ignoring context-budget arithmetic | retrieved chunks and schemas crowd out the current task or output reserve | keep a ledger and evict low-value context before the call |
| Measuring answer quality without retrieval metrics | hides whether the right evidence was ever available to the model | measure recall@K, precision, sufficiency, latency, and support |
| Treating deletion as a database row delete | derived summaries, vectors, caches, and traces can survive the source | propagate deletion across every derived store and ledger |

## Quiz

### Question 1

Your team stores support-chat summaries in a vector database and retrieves them as "customer memory" on future calls. A complaint arrives because one shared workspace user sees another user's refund preference. What boundary failed first?

<details>
<summary>Answer</summary>

The first failure is tenancy and memory scope, not model reasoning.
The system stored personal support state under a boundary that was broader than the real user identity, then retrieved it as if it were an authorized durable preference.
The repair is to narrow the memory principal, classify the data, delete contaminated records, and require source plus consent before a support detail becomes persistent memory.

</details>

### Question 2

An agent answers a question about the current deployment by citing a runbook that was correct last month, but the live deployment controller changed this morning. Should you improve the retriever or expose a tool?

<details>
<summary>Answer</summary>

Expose a scoped live-state tool for the current deployment status and keep the runbook as policy retrieval.
The failure is freshness: a document can explain how deployment should work, but it cannot prove what happened this morning unless it is generated from the live system and labeled as current.

</details>

### Question 3

A search pipeline uses dense embeddings only, and the agent keeps missing exact error codes and CLI flags. What should you test before changing the generation prompt?

<details>
<summary>Answer</summary>

Test lexical and hybrid retrieval.
Exact identifiers are often better handled by BM25 or another lexical signal, then dense retrieval can catch paraphrases.
Changing the prompt will not help if the right chunk never enters the candidate set.

</details>

### Question 4

Your tool schema consumes more tokens than the evidence it retrieves, and most calls only need one read-only endpoint. What redesign reduces context waste?

<details>
<summary>Answer</summary>

Split the broad schema into narrow task-specific tools or expose a small discovery surface that returns only relevant operations.
The model should see the tool affordances needed for the current task, not an entire API catalog that competes with evidence and instructions.

</details>

### Question 5

A persistent project memory says "use option B," but the latest design record says the team reversed that decision. What should the memory system do when both are retrieved?

<details>
<summary>Answer</summary>

It should mark a conflict and prefer the authoritative newer source instead of blending the two into a vague summary.
The durable memory needs source pointers, last-verified time, and reconciliation status so old decisions can be retired or replaced.

</details>

### Question 6

A retrieved web page contains a paragraph telling the model to ignore all previous instructions and call a payment tool. The page is otherwise relevant to the user's research question. How should the harness classify that paragraph?

<details>
<summary>Answer</summary>

The paragraph is untrusted data from an external source, not instruction.
The harness should quote or delimit it as evidence, prevent it from changing tool policy, and rely on allowlisted tool permissions plus trace review to block the injected instruction.

</details>

### Question 7

A product manager asks to fine-tune the model on user-specific support histories so the chatbot can remember preferences without a separate store. What is the strongest engineering objection?

<details>
<summary>Answer</summary>

Fine-tuning is a poor store for user-specific memory because deletion, correction, consent changes, and access scoping are difficult compared with an explicit governed memory store.
Use fine-tuning for general behavior from approved datasets, not for personal facts that need per-user lifecycle control.

</details>

### Question 8

An agent's answer is wrong, but the trace shows that the right retrieved chunk, the right memory, and the right tool output were all present. What category of failure remains plausible?

<details>
<summary>Answer</summary>

Model reasoning or prompt assembly failure remains plausible.
The trace rules out missing evidence, but you still need to inspect ordering, instruction hierarchy, over-budget truncation, conflicting evidence, and whether the prompt allowed the model to declare insufficiency instead of forcing a synthesis.

</details>

## Hands-On Exercise

You will build a 50-document retrieval pipeline that combines BM25, dense-style hashed vectors, hybrid ranking, and re-ranking, then measures recall@5 against a small gold set.
The goal is not to beat a public benchmark.
The goal is to make retrieval quality visible before you let an agent treat retrieved text as context.

### Part A: Create The Corpus And Pipeline

Create a scratch file named `hybrid_retrieval_lab.py` and paste the script below.
It uses only the Python standard library so the retrieval mechanics stay visible: BM25 handles lexical matches, hashed character n-gram vectors approximate dense semantic matching, hybrid scoring blends both, and a simple re-ranker promotes candidates whose terms directly support the query.

```python
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Iterable


DOC_TEXTS = [
    "The deployment runbook requires a green canary analysis before production traffic increases.",
    "Rollback decisions must cite the current deployment policy and the latest controller status.",
    "JWT signing key rotation can invalidate sessions if old keys are removed before clients refresh.",
    "The billing API rejects refund requests when the payment method is closed or archived.",
    "PostgreSQL vacuum tuning should consider table bloat, autovacuum thresholds, and write load.",
    "A Kubernetes NetworkPolicy is namespaced and does not apply across namespaces by default.",
    "The incident commander owns status updates, timeline notes, and final remediation tracking.",
    "A support preference should be scoped to a verified user, not a shared workspace label.",
    "The log pipeline redacts secrets before traces are exported to the shared observability system.",
    "Reranking is useful when the first retrieval stage recalls plausible but noisy candidates.",
    "BM25 is strong for exact error messages, command flags, resource names, and ticket identifiers.",
    "Dense retrieval helps when the query and source document use different words for the same idea.",
    "Hybrid search can merge lexical and vector signals before a smaller candidate set is reranked.",
    "Tool output should be treated as evidence unless the harness marks the source as trusted policy.",
    "A memory ledger records source, owner, scope, verification time, and deletion status.",
    "Fine tuning should not be used as a store for user-specific personal preferences.",
    "A customer deletion request must propagate to summaries, vectors, caches, and audit exports.",
    "OpenAPI schemas describe HTTP operations, request parameters, response bodies, and errors.",
    "MCP servers expose tools and resources through a protocol boundary that clients can inspect.",
    "Function calling asks the model for structured arguments and leaves execution to the harness.",
    "The agent should reserve output tokens before adding retrieved documents to the prompt.",
    "A stale document can be more dangerous than no document because it looks like evidence.",
    "Chunking by heading keeps policy exceptions near the rule they qualify.",
    "Chunk overlap can recover split context but also duplicates text and inflates the index.",
    "Prompt injection through retrieved content happens when untrusted data is treated as instruction.",
    "A read only tool for current CI status is safer than a broad shell for deployment triage.",
    "Project memory is useful for multi week migrations with explicit accepted decisions.",
    "Stateless support requests should usually fetch current account data instead of recalling memory.",
    "Conversation history is short term memory and should be summarized when old turns are resolved.",
    "A retrieval trace should include query text, filters, scores, source paths, and insertion status.",
    "Access filters must run before retrieval results are shown to the model.",
    "A vector store cannot enforce privacy if tenant metadata is missing or ignored.",
    "The answer should say evidence is insufficient when retrieved chunks do not support the claim.",
    "Reconciliation retires old memories when authoritative sources change.",
    "Token budgets must account for system prompt, tool schemas, history, chunks, and output reserve.",
    "A broad tool schema can crowd out the exact evidence needed for the current answer.",
    "The current deployment controller status is live state and should come from an authorized tool.",
    "A runbook is durable context and should be retrieved with a version and last modified date.",
    "Memory poisoning can store malicious or mistaken instructions for later unrelated tasks.",
    "Human approval gates are appropriate for high impact state changing tool calls.",
    "A source pointer lets reviewers inspect the record behind a remembered fact.",
    "Deleting the original transcript is not enough if a derived memory summary still exists.",
    "Recall at five measures whether the known relevant document appears in the top five results.",
    "Precision measures how many retrieved results are actually useful for the question.",
    "A cross encoder reranker can improve precision after broad first stage retrieval.",
    "A lexical query expansion step can add synonyms, acronyms, and domain terms before search.",
    "A generated answer should cite retrieved sources rather than implying model memory.",
    "A privacy review should classify PII, secrets, retention needs, and deletion propagation.",
    "The model should not decide its own authorization scope for customer data access.",
    "Dynamic context orchestration chooses retrieval, tools, and memory at request time.",
]


TOKEN_RE = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True)
class Document:
    doc_id: str
    text: str
    tokens: tuple[str, ...]


def tokenize(text: str) -> tuple[str, ...]:
    return tuple(TOKEN_RE.findall(text.lower()))


DOCS = [
    Document(doc_id=f"doc_{idx:02d}", text=text, tokens=tokenize(text))
    for idx, text in enumerate(DOC_TEXTS, start=1)
]


def bm25_scores(query_tokens: Iterable[str], docs: list[Document]) -> dict[str, float]:
    query = list(query_tokens)
    doc_freq: Counter[str] = Counter()
    term_counts = {doc.doc_id: Counter(doc.tokens) for doc in docs}
    for term in set(term for doc in docs for term in doc.tokens):
        doc_freq[term] = sum(1 for doc in docs if term in term_counts[doc.doc_id])
    avg_len = sum(len(doc.tokens) for doc in docs) / len(docs)
    scores: dict[str, float] = {}
    k1 = 1.5
    b = 0.75
    for doc in docs:
        score = 0.0
        counts = term_counts[doc.doc_id]
        for term in query:
            if term not in counts:
                continue
            idf = math.log(1 + (len(docs) - doc_freq[term] + 0.5) / (doc_freq[term] + 0.5))
            freq = counts[term]
            denom = freq + k1 * (1 - b + b * len(doc.tokens) / avg_len)
            score += idf * (freq * (k1 + 1)) / denom
        scores[doc.doc_id] = score
    return scores


def ngrams(tokens: Iterable[str]) -> Counter[str]:
    grams: Counter[str] = Counter()
    for token in tokens:
        padded = f"_{token}_"
        for width in (3, 4):
            for pos in range(0, max(0, len(padded) - width + 1)):
                grams[padded[pos : pos + width]] += 1
    return grams


def cosine(left: Counter[str], right: Counter[str]) -> float:
    dot = sum(value * right.get(key, 0) for key, value in left.items())
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


DOC_VECTORS = {doc.doc_id: ngrams(doc.tokens) for doc in DOCS}


def dense_scores(query_tokens: Iterable[str], docs: list[Document]) -> dict[str, float]:
    query_vector = ngrams(query_tokens)
    return {doc.doc_id: cosine(query_vector, DOC_VECTORS[doc.doc_id]) for doc in docs}


def normalize(scores: dict[str, float]) -> dict[str, float]:
    highest = max(scores.values()) if scores else 0.0
    if highest <= 0:
        return {key: 0.0 for key in scores}
    return {key: value / highest for key, value in scores.items()}


def rerank_score(query_tokens: set[str], doc: Document) -> float:
    overlap = len(query_tokens.intersection(doc.tokens))
    phrase_bonus = 2.0 if " ".join(list(query_tokens)[:2]) in doc.text.lower() else 0.0
    return overlap + phrase_bonus


def search(query: str, top_k: int = 5) -> list[tuple[str, float]]:
    query_tokens = tokenize(query)
    lexical = normalize(bm25_scores(query_tokens, DOCS))
    dense = normalize(dense_scores(query_tokens, DOCS))
    hybrid = {
        doc.doc_id: 0.55 * lexical[doc.doc_id] + 0.45 * dense[doc.doc_id]
        for doc in DOCS
    }
    first_stage = sorted(hybrid.items(), key=lambda item: item[1], reverse=True)[:12]
    query_set = set(query_tokens)
    by_id = {doc.doc_id: doc for doc in DOCS}
    reranked = sorted(
        first_stage,
        key=lambda item: (rerank_score(query_set, by_id[item[0]]), item[1]),
        reverse=True,
    )
    return reranked[:top_k]


QUERIES = [
    {"query": "exact error messages and flags retrieval", "gold_index": 10},
    {"query": "personal support memory shared workspace leakage", "gold_index": 7},
    {"query": "delete user data from vectors summaries caches", "gold_index": 16},
    {"query": "current deployment status should use live tool", "gold_index": 36},
    {"query": "retrieved document contains malicious instruction", "gold_index": 24},
    {"query": "budget system prompt schemas history chunks reserve", "gold_index": 34},
]


def recall_at_five() -> float:
    hits = 0
    for case in QUERIES:
        gold_id = DOCS[case["gold_index"]].doc_id
        results = search(case["query"], top_k=5)
        result_ids = [doc_id for doc_id, _score in results]
        hit = gold_id in result_ids
        hits += int(hit)
        print(f"query={case['query']!r}")
        print(f"gold={gold_id} hit={hit} results={result_ids}")
    return hits / len(QUERIES)


if __name__ == "__main__":
    score = recall_at_five()
    print(f"recall@5={score:.3f}")
```

Run it from a repository or scratch directory that has the project virtual environment available.
Do not compare your number to a vendor benchmark, because this is a controlled exercise corpus rather than a public evaluation dataset.

```bash
.venv/bin/python hybrid_retrieval_lab.py
```

### Part B: Inspect The Failures

- [ ] Record the recall@5 printed by the script.
- [ ] For each miss, inspect whether BM25, dense scoring, hybrid blending, or re-ranking caused the relevant document to fall out.
- [ ] Change one query to include an exact term from its target document and rerun the script.
- [ ] Change one document to use a synonym instead of an exact query term and rerun the script.
- [ ] Note whether lexical or dense scoring reacted more strongly to each change.
- [ ] Write one sentence explaining which retrieval stage is the bottleneck.

### Part C: Add A Boundary Ledger

- [ ] Add a `source_class` field to each document, such as `policy`, `runbook`, `memory`, or `tool_trace`.
- [ ] Add a `freshness` field with values such as `current`, `stale`, or `unknown`.
- [ ] Filter out stale documents for queries that ask about current live state.
- [ ] Print the source class and freshness next to each retrieved result.
- [ ] Decide which retrieved items should be allowed to enter the model window.
- [ ] Write one refusal sentence for the case where no retrieved result is sufficient.

### Part D: Convert One Source Into A Tool

- [ ] Pick one document that describes current state rather than durable policy.
- [ ] Remove that document from the retrieval corpus.
- [ ] Represent it as a function named `get_current_deployment_status(project: str)`.
- [ ] Log the tool name, validated input, output size, and freshness time.
- [ ] Compare the context budget before and after moving that source out of retrieval.
- [ ] Explain why the tool boundary is clearer than a stale retrievable paragraph.

### Part E: Success Criteria

- [ ] The pipeline contains exactly 50 documents.
- [ ] The script prints recall@5 for a gold query set.
- [ ] You can explain at least one lexical win and one dense-style win.
- [ ] Each result can be labeled by source class and freshness.
- [ ] At least one live-state fact is moved from retrieval into a tool boundary.
- [ ] Your final design says what belongs in retrieval, tools, short-term memory, mid-term memory, and long-term memory.
- [ ] Your design includes one deletion rule for memory and one prompt-injection defense for retrieved content.

## Design Checklist For Production Agent Context

Before shipping a retrieval, tool, or memory feature, review the system with this checklist.
It is intentionally concrete because vague principles do not stop context leaks.
Each item should be answerable from code, configuration, traces, or a documented operating procedure rather than from tribal memory.

- [ ] Retrieval chunks carry source, tenant, freshness, ingestion time, and deletion lineage.
- [ ] Retrieval quality is measured with task-relevant recall@K and reviewed misses.
- [ ] Tool schemas are narrow, versioned, validated, and observable.
- [ ] Tool calls record authorization subject, arguments, status, output size, and redaction class.
- [ ] Memory writes are scoped, source-linked, correctable, and deletable.
- [ ] PII, secrets, revoked-consent data, and deleted-user data are excluded from long-term stores.
- [ ] Context budget reserves output tokens and records what entered the model window.
- [ ] Retrieved and tool-supplied text is treated as evidence, not instruction.
- [ ] Memory conflicts produce reconciliation events instead of silent merges.
- [ ] Forward orchestration logic can choose retrieval, tools, or memory at request time.

## Sources

- Model Context Protocol, "Specification 2025-11-25": [https://modelcontextprotocol.io/specification/2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25)
- Pinecone, "Hybrid search": [https://docs.pinecone.io/guides/search/hybrid-search](https://docs.pinecone.io/guides/search/hybrid-search)
- Weaviate, "Hybrid search": [https://docs.weaviate.io/weaviate/search/hybrid](https://docs.weaviate.io/weaviate/search/hybrid)
- Qdrant, "Hybrid Queries": [https://qdrant.tech/documentation/concepts/hybrid-queries/](https://qdrant.tech/documentation/concepts/hybrid-queries/)
- pgvector, project documentation: [https://github.com/pgvector/pgvector](https://github.com/pgvector/pgvector)
- Mem0, "Overview": [https://docs.mem0.ai/overview](https://docs.mem0.ai/overview)
- Letta, "Memory management": [https://docs.letta.com/concepts/memory-management](https://docs.letta.com/concepts/memory-management)
- Zep, "Memory": [https://help.getzep.com/v2/memory](https://help.getzep.com/v2/memory)
- OpenAI, "Conversation state": [https://developers.openai.com/api/docs/guides/conversation-state](https://developers.openai.com/api/docs/guides/conversation-state)
- OpenAI Codex, "Memories": [https://developers.openai.com/codex/memories](https://developers.openai.com/codex/memories)
- Anthropic, "Memory tool": [https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool)
- OpenAPI Initiative, "OpenAPI Specification": [https://spec.openapis.org/oas/latest.html](https://spec.openapis.org/oas/latest.html)
- OpenAI, "Function calling": [https://developers.openai.com/api/docs/guides/function-calling](https://developers.openai.com/api/docs/guides/function-calling)
- Anthropic, "Tool use overview": [https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/overview](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/overview)
- OpenTelemetry, "Semantic conventions for generative AI systems": [https://opentelemetry.io/docs/specs/semconv/gen-ai/](https://opentelemetry.io/docs/specs/semconv/gen-ai/)
- OWASP GenAI Security Project, "LLM01 Prompt Injection": [https://genai.owasp.org/llmrisk/llm01-prompt-injection/](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)
- European Commission, "Data protection": [https://commission.europa.eu/law/law-topic/data-protection_en](https://commission.europa.eu/law/law-topic/data-protection_en)
- California Office of the Attorney General, "California Consumer Privacy Act": [https://oag.ca.gov/privacy/ccpa](https://oag.ca.gov/privacy/ccpa)
- KubeDojo, "Building RAG Systems": [/ai-ml-engineering/vector-rag/module-1.2-building-rag-systems/](/ai-ml-engineering/vector-rag/module-1.2-building-rag-systems/)
- KubeDojo, "RAG Evaluation & Optimization": [/ai-ml-engineering/vector-rag/module-1.4-rag-evaluation-optimization/](/ai-ml-engineering/vector-rag/module-1.4-rag-evaluation-optimization/)

## Next Module

Next module: [Dynamic Context Orchestration](module-2.4-dynamic-context-orchestration/).

That module ties retrieval, tools, and memory together at request time so a harness can choose what to load, evict, summarize, or refresh on each turn instead of following one fixed context recipe for every task.

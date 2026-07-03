---
title: "Context Engineering Fundamentals"
slug: ai/ai-engineering-foundations/module-2.1-context-fundamentals
sidebar:
  order: 21
revision_pending: false
---

> **Complexity**: `[COMPLEX]`
>
> **Time to Complete**: 75-90 min
>
> **Prerequisites**: Module 1.1 Prompt Fundamentals or equivalent; comfort with LLM context windows; basic CLI + git.

---

## Learning Outcomes

By the end of this module, you will be able to reason about context as an engineered working set rather than as a longer prompt. The outcomes below focus on the choices that make an agent run repeatable across sessions, reviewers, and repositories:

- **Distinguish** context engineering from prompt engineering and from RAG by naming the unit of optimization for each discipline.
- **Diagnose** why an agent that worked in one session fails in a fresh session by identifying the missing context inputs.
- **Design** a context layout that improves cached-token share while staying under the effective attention budget.
- **Evaluate** the trade-offs of high-context and low-context agent runs across cost, latency, risk, and reviewability.
- **Compare** session-level context with repo-level context and route information to the surface that will remain authoritative.

## Why This Module Matters

**Hypothetical scenario:** Mira is the senior engineer everyone asks when the AI coding workflow becomes unstable. She shipped the first useful internal agent playbook for a large platform repository. In her hands, the agent reads the right runbook, opens the right files, avoids the generated state directory, runs the correct tests, and produces a small pull request. The model has a large context window, and Mira uses it well.

For several weeks, the workflow looks repeatable. Then a teammate joins the same workstream. The teammate receives Mira's prompt, the same model name, and the same issue. The result is not the same. The new session misses a hidden branch rule, reopens a solved design question, forgets a reviewer constraint, and edits a generated file that Mira's runs never touched.

Nobody changed the model. Nobody changed the task. The missing piece is that Mira had been carrying useful state inside the session: prior tool outputs, remembered decisions, cached files, the order in which she loaded instructions, and a mental map of which repository documents mattered. Her "prompting skill" was not just prompt writing. It was context engineering that she had never named.

Context engineering is the discipline of managing what an LLM agent sees on each turn. It is not a synonym for prompt engineering. It is not the same thing as RAG. It is the RAM-management layer of LLM-backed work: deciding what belongs in the window, where it should sit, how it should change, how it should be cached, and when stale state should be refreshed.

This module gives that layer a practical shape. You will learn how to reason about the model window as a scarce operating surface, how to place persistent repository knowledge differently from transient session knowledge, how prefix caching changes prompt layout, and how to detect context rot before a useful session turns into a loop. The point is not to make every prompt enormous; the point is to make each turn carry the smallest complete working set for the decision in front of the agent.

That distinction matters in production teams because context failures are expensive to review. A bad instruction usually leaves a visible trace in the prompt. A bad context assembly can look like model weakness, operator error, flaky tooling, or missing documentation depending on who investigates it. When the working set is explicit, the team can ask concrete questions: was the rule present, was the evidence current, was the acceptance criterion near the current ask, and could a fresh session reconstruct the same state without relying on Mira's memory?

## Start With The Unit Of Optimization

Prompt engineering, context engineering, and RAG often get collapsed into one phrase because all three influence model input. That collapse is expensive. When teams do not name the layer, they debug the wrong thing. They rewrite instructions when the repository map is missing. They add vector search when the real issue is tool-output bloat. They increase context size when the actual problem is poor ordering. The first senior habit is to name the unit of optimization.

| Discipline | Unit of optimization | Typical artifact | Failure symptom |
|---|---|---|---|
| Prompt engineering | The instruction interface for a task | system prompt, user prompt, examples, output contract | the model misunderstands what to do |
| Context engineering | The assembled input state for a turn | file excerpts, chat history, tool results, repo docs, retrieved snippets | the model lacks or misweights the information needed to act |
| RAG | One retrieval pattern inside context assembly | retriever, corpus, chunks, ranking, citations | the model receives the wrong external knowledge or cannot ground a claim |

Prompt engineering asks: "What instruction should the model follow?" Context engineering asks: "What should the model be able to see right now?" RAG asks: "Which external records should be retrieved and inserted?" Those questions overlap, but they are not interchangeable. A strong prompt cannot compensate for a missing acceptance criterion. A large retrieval result cannot fix contradictory session state.

A perfect repository guide will not help if it is loaded after several screens of noisy logs that dominate attention. The context engineer owns selection, compression, order, freshness, and observability. That ownership matters most in agentic work because the input is not one static prompt. The input is repeatedly rebuilt from instructions, conversation history, tool outputs, file reads, previous decisions, and sometimes retrieved documents. Each turn is a new operating surface.

This is also why the unit-of-optimization table is a debugging tool, not just terminology. If the agent misunderstands the output contract, you probably need prompt work. If it lacks a path map, stale evidence is still salient, or the rule is present but buried, you need context work. If the agent needs an external fact that is not in the repo or session, retrieval may be appropriate, but retrieval should enter as one intentionally placed evidence source rather than as a magic memory layer.

### Worked Example: The Fresh-Session Failure

Mira's successful run had a layered working set, even though nobody had written it down as a formal artifact. The task prompt sat on top of stable repository policy, live session evidence, and tool outputs that had accumulated during the run:

```text
+------------------------------------------------------------+
| Stable repo context                                        |
| AGENTS.md, branch policy, generated-file exclusions        |
+------------------------------------------------------------+
| Session context                                            |
| Prior command failures, selected test command, issue scope |
+------------------------------------------------------------+
| Task prompt                                                |
| "Fix the module and open a PR"                             |
+------------------------------------------------------------+
| Tool outputs                                               |
| Changed file list, build output, reviewer notes            |
+------------------------------------------------------------+
```

Her teammate received only the visible task request, so the model could not distinguish durable rules from unstated assumptions. The new run looked like the same prompt, but it was a different operating surface:

```text
+------------------------------------------------------------+
| Task prompt                                                |
| "Fix the module and open a PR"                             |
+------------------------------------------------------------+
```

The prompt was not the problem by itself. The missing state was the problem. The teammate did not know which files were generated, which checks were mandatory, which issue scope was active, or which previous design choice had already been rejected. A prompt engineer might try to make the task prompt longer. A context engineer asks where each missing input should live.

| Missing input | Best home | Why |
|---|---|---|
| generated-file exclusions | repo context | stable rule, should apply to every session |
| selected test command | repo context if universal, session context if task-specific | some checks are global, some are local to a change |
| previous rejected design | repo context if durable, session context if only for this task | avoid polluting stable docs with one-off debate |
| last failing build output | session context | transient evidence, useful until fixed |
| reviewer requirement | repo context if policy, session context if PR-specific | route based on expected reuse |

The core diagnostic question is therefore not "how do we phrase the prompt more forcefully?" but "which state did the successful run have that a fresh run lacks, and where should that state live?"

> **Active learning prompt:** Think of an AI agent run that worked only after a long back-and-forth. Which three pieces of state did the final successful turn contain that a fresh session would not have?

If the answer includes policy, path maps, or team conventions, those belong in repo context. If the answer includes command output, partial reasoning, or current failure traces, those belong in session context. If the answer includes external knowledge, retrieval may help, but only after you know what the retrieval result must support.

Notice the routing decision behind each row. The generated-file exclusion should survive every future session, so hiding it in a conversation transcript is a design bug. The last build failure should not become permanent policy, so copying it into an agent guide would be a different design bug. Context engineering is the habit of making those placement choices deliberately, then checking that the next agent run actually receives the chosen inputs at the right time.

## The LLM-as-OS Mental Model

The LLM-as-OS framing is a community-of-practice shorthand, not a formal architecture standard. The useful part is not claiming that a model is literally a kernel; the useful part is seeing that agent reliability comes from the model plus tools, durable files, session history, harness rules, and observability around the call. Vendor guidance on agents, context windows, and caching repeatedly points in this direction: better systems assemble and manage the working set around the model rather than relying on one clever instruction string.

In the analogy, the context window acts like RAM, tools behave like system calls, repository files are durable storage, and the harness is the process supervisor, policy layer, and observability surface. The prompt is closer to a process entrypoint than to the whole program, because the real behavior comes from the entrypoint plus the available working set plus the rules enforced around execution.

| Operating concern | LLM agent analogue | Context question |
|---|---|---|
| RAM | context window | what fits now? |
| cache locality | prefix cache | what repeats first? |
| disk | repository docs and code | what persists? |
| process log | session history | what just happened? |
| system call | tool invocation | what can be fetched? |
| supervisor | harness rules and checks | what is enforced? |

This model prevents two common mistakes. The first mistake is treating the context window as a passive bucket. It is not a bucket. It is the active working set that shapes the next model computation. The second mistake is treating a larger window as a cure for weak context design. More address space does not eliminate the need for memory management. It often makes memory management more important because the agent can now carry a larger amount of stale or low-value state.

### Nominal Limit Versus Effective Attention Budget

Vendors advertise nominal token limits. Engineers operate within effective attention budgets. The nominal limit answers: "How much input can the request accept before truncation or failure?" The effective attention budget answers: "How much of this input can the model use reliably for this task?" Those are different numbers. A model may accept a huge input while still over-weighting the beginning, the end, recent tool outputs, repeated phrasing, or highly salient instructions.

Long-context research shows that fitting tokens and using them reliably are different problems (for example, Liu et al., arXiv:2307.03172). Architectures such as Google DeepMind's Infini-attention, "Leave No Context Behind: Efficient Infinite Context Transformers with Infini-attention" (arXiv:2404.07143), address scaling attention itself. The practical lesson is not "never use long context." The lesson is "test where performance degrades for your task shape." Long windows are extremely useful for codebase reading, multi-document review, and migration planning. They are less useful when the agent must notice one small acceptance criterion hidden in a noisy transcript.

The effective budget is especially important when the prompt mixes different kinds of information. Provider documentation can tell you the nominal window size, but your workflow has its own attention profile: a code review with one critical security constraint behaves differently from a broad architecture survey, even if both fit inside the same token limit. A useful benchmark asks the agent to perform the exact decision you care about, places the controlling fact in different prompt regions, and records whether the model still acts on that fact when logs, file excerpts, and old discussion are present.

Position effects matter. Many model behaviors are strongest around the start and end of the prompt. That is why teams often place durable instructions and maps early, keep the current task and acceptance criteria near the end, and aggressively compress tool output that no longer matters.

| Prompt region | Good candidates | Risk | Design move |
|---|---|---|---|
| Very early | stable rules | stale if mixed with run-specific facts | keep static and reviewable |
| Early-middle | repo map | too much prose | use indexes and targeted links |
| Middle | evidence chunks | lost-in-middle effects | summarize and label freshness |
| Late-middle | recent findings | tool-output bloat | prune resolved evidence |
| Very late | task and ask | unstable if huge | keep the current action crisp |

The effective budget is also shaped by task difficulty. A simple summarization task can often tolerate more background. A multi-file code edit with strict acceptance criteria needs a cleaner window because the model must preserve constraints while planning, editing, and explaining. Do not ask "Can the file fit?" Ask "Will the model attend to the part that controls the decision?"

### A Practical RAM Budget

For senior engineering work, start with a budget that classifies context by expected reuse, not by the order in which the information happened to arrive during exploration.

```yaml
context_budget:
  stable_prefix:
    purpose: durable rules and maps
    examples:
      - agent instructions
      - repository layout
      - acceptance rubric
  task_frame:
    purpose: the current problem and success criteria
    examples:
      - issue summary
      - non-goals
      - required checks
  evidence:
    purpose: facts gathered during this run
    examples:
      - file excerpts
      - failing command output
      - API responses
  scratch:
    purpose: short-lived notes used to choose next action
    examples:
      - temporary hypotheses
      - alternative plans
      - resolved errors
```

Only the first block should be stable across many requests. The task frame should change per issue, but not per tool call. Evidence should be kept only while it affects the next decision. Scratch should be summarized or discarded quickly. The RAM analogy becomes useful when the session starts to degrade. If the agent is looping, the scratch area may have grown into a misleading state machine.

If the agent forgets acceptance criteria, the task frame may be buried. If the agent violates stable policy, the stable prefix may be missing, contradicted, or loaded too late.

The budget also gives reviewers a vocabulary for feedback. Instead of saying "the model missed the rule," a reviewer can say "the rule was stable policy but appeared only in scratch after three logs," or "the failing command output was useful evidence, but it stayed in the window after a later run superseded it." Those statements are actionable because they point to a change in assembly, not a vague hope that the next model call will reason better.

## Context Is Scarce Even In Large Windows

Large context windows change what is possible. They do not remove scarcity. Scarcity moves from "will this input fit?" to "which tokens deserve attention, cost, latency, and review?" Every added token competes with other tokens. Every added file increases the chance that the model will overfit to irrelevant detail. Every added tool output can become stale evidence after the problem is fixed.

The most useful discipline is to treat context like an SRE treats dashboards during an incident. More panels are not always better. The right panel, at the right moment, with a clear freshness signal, is better.

Scarcity also has a review cost. If an agent produces a patch after reading forty files, a reviewer has to decide whether those files mattered, whether the agent ignored something important, and whether stale evidence shaped the final edit. A narrower run can be easier to audit, but it can also be falsely confident if the hidden constraint was outside the window. The engineering problem is to choose a context size that is large enough to cover the decision and small enough that both model and reviewer can still see the controlling facts.

### High-Context Versus Low-Context Runs

Neither high-context nor low-context is inherently correct, because each one buys a different failure mode. The right choice depends on blast radius, ambiguity, and recovery cost: a platform migration needs broad continuity, while a typo fix should not drag an entire architecture archive into the prompt.

| Approach | Strength | Cost | Failure mode | Use when |
|---|---|---|---|---|
| High-context | broad awareness, fewer missing files, better architectural continuity | slower, more expensive, harder to review | model attends to stale or irrelevant detail | architecture review, migration planning, incident reconstruction |
| Low-context | fast, cheap, narrow, easier to audit | misses hidden constraints, may rediscover known facts | agent invents defaults for absent context | small edits, single-file fixes, known command loops |
| Staged-context | starts narrow, expands on evidence | requires orchestration discipline | expansion rules are vague | most production agent workflows |

Staged-context is often the best default. Begin with the stable rules, the task frame, and the smallest relevant file set. Expand only when evidence shows a missing dependency. Summarize or drop resolved evidence before the next expansion. That loop keeps the session from turning into an accidental archive, and it leaves a trail of why each added source was worth its token budget.

```mermaid
flowchart TD
    A[Start with stable prefix] --> B[Load task frame]
    B --> C[Read narrow evidence]
    C --> D{Enough to act?}
    D -- yes --> E[Edit or answer]
    D -- no --> F[Expand context by one reason]
    F --> G[Record why it was needed]
    G --> C
    E --> H[Summarize resolved evidence]
    H --> I[Keep next turn small]
```

The phrase "by one reason" is important because uncertainty alone is too vague to govern context growth. Do not expand context because the agent feels uncertain. Expand because a specific decision needs a specific missing input, such as the implementation of a referenced helper, the policy that controls generated artifacts, or the current output of the failing check.

### Position Bias In Practice

The "lost in the middle" problem (Liu et al., arXiv:2307.03172) is not only an academic curiosity. In agent sessions, it shows up as practical forgetting. An acceptance criterion placed in the middle of a long transcript may be ignored while the model follows the newest command output. A repository rule loaded after several long logs may be treated as less central than the logs.

A security note buried in a retrieved document may lose to a confident but generic prior. The repair is not to shout the rule louder in every sentence. The repair is to design a context layout. Put durable rules early. Put the current task and success criteria late. Keep the middle for compressed evidence that directly supports the next decision. When a middle item becomes decision-critical, promote it into the task frame or stable prefix before the next turn.

```text
Bad layout:

+------------+------------+------------+------------+------------+
| variable   | huge logs  | key rule   | old debate | current ask |
+------------+------------+------------+------------+------------+

Better layout:

+------------+------------+------------+------------+------------+
| stable     | repo map   | evidence   | open risks | current ask |
+------------+------------+------------+------------+------------+
```

### Worked Example: Shrinking Without Losing Signal

Suppose an agent is fixing a failing build after a long debugging session. The raw transcript contains several categories of information, but only some of them still affect the next action:

- full repository instructions
- issue body
- three failed build logs
- two file reads
- one reviewer comment
- one stale hypothesis about package versions
- the final compiler error

A weak low-context approach drops too much, leaving the agent without the rules and evidence that distinguish this failure from any generic compiler error:

```text
Fix the build. The compiler failed.
```

A weak high-context approach includes everything, which preserves evidence but also makes stale hypotheses compete with the current causal error:

```text
Here is every instruction, every log, every command, every old hypothesis,
every file, and every comment from the last two hours. Continue.
```

A context-engineered version keeps the decision state by naming the stable rules, current scope, fresh evidence, and exact next action:

```text
Stable rules:
- Do not edit generated state.
- Run the site build before opening the PR.

Task:
- Fix the build failure caused by the new module.
- Keep the change limited to the new content files.

Fresh evidence:
- The current compiler error says the Mermaid block is malformed.
- The affected file is module-2.1-context-fundamentals.md.
- Earlier package-version hypotheses were disproven by a clean dependency install.

Next action:
- Inspect the Mermaid block, correct syntax, rerun build, and report only current errors.
```

The engineered version is smaller than the raw session but richer than the vague prompt. It removes resolved noise while preserving the causal path. In practice, this is the difference between "summarize the chat so far" and "rebuild the working set for the next decision." The first may carry every emotional contour of the debugging session; the second carries the facts that still matter.

> **Active learning prompt:** Take a recent AI session transcript and mark each paragraph as stable rule, task frame, evidence, or scratch. Which paragraphs would you delete before the next model turn?

## The Economics Of Prefix Caching

Context layout is not only about quality. It is also about cost and latency. Prompt caching rewards stable prefixes. If the beginning of a request repeats exactly across calls, providers can reuse cached work instead of processing the whole prefix from scratch. Both Anthropic and OpenAI document the same core design rule: put stable or repeated content first, and variable user-specific content later.

The exact implementation differs by provider. Anthropic exposes automatic caching and explicit cache breakpoints such as `cache_control`. OpenAI describes automatic prompt caching for eligible long prompts, with usage fields such as `cached_tokens` and options such as `prompt_cache_key` and retention policy. The engineering principle is provider-neutral: maximize the stable prefix without hiding current task data.

Gim et al. (arXiv:2311.04934) are also cited for framing the economics of stable-prefix reuse in repeated inference runs.

This is where quality and economics point in the same direction. The stable prefix is usually where durable policy, output contracts, tool schemas, and compact repository maps belong, so placing it first helps both attention and cache reuse. The suffix is where current evidence belongs, so keeping it late protects recency without destroying the cached prefix. A context layout that starts with a timestamp, issue title, or raw command output pays more and often teaches the model to focus on the noisiest part of the run.

### Cache-Friendly Context Layout

```text
+--------------------------------------------------------------------------+
| Stable prefix                                                            |
| Provider instructions, agent role, repo policy, output contract          |
+--------------------------------------------------------------------------+
| Semi-stable middle                                                       |
| Tool schemas, repository map, rubric, examples                           |
+--------------------------------------------------------------------------+
| Variable suffix                                                          |
| Issue body, current file excerpts, command output, user question         |
+--------------------------------------------------------------------------+
```

If you put variable content at the top, the cache breaks early. If you put a timestamp, random run id, or current error log before the stable policy, every request looks new. That forces the provider to process the expensive shared material again.

### Caching Flow
```mermaid
sequenceDiagram
    participant App as Agent harness
    participant Cache as Provider cache
    participant Model as Model runtime
    App->>App: Build stable prefix first
    App->>App: Append variable task suffix
    App->>Cache: Check exact prefix match
    alt cache hit
        Cache-->>Model: Reuse cached prefix state
        App->>Model: Send variable suffix
    else cache miss
        App->>Model: Send full request
        Model-->>Cache: Store eligible prefix
    end
    Model-->>App: Return answer and usage metrics
    App->>App: Log cached tokens and latency
```

The important metric is not "did caching exist?" The important metric is cached-token share for the expensive part of the prompt. You can observe that with provider usage fields and local timing, then compare those metrics with output quality so a cache improvement does not hide a worse review result.

### Worked Example: Reordering For Cache

Assume an agent harness sends this request shape on every file review, and the team wonders why repeated reviews still feel slow and expensive:

```text
BAD ORDER

1. Current timestamp and run id
2. User issue text
3. Failing command output
4. Stable repository policy
5. Stable review rubric
6. Tool schema
7. Required output shape
```

The top changes every request. Even if the policy and rubric are identical, they arrive after variable content. The stable prefix is tiny. A cache-friendly layout is:

```text
BETTER ORDER

1. Stable repository policy
2. Stable review rubric
3. Tool schema
4. Required output shape
5. Current issue text
6. Failing command output
7. Timestamp and run id, only if needed
```

Now the expensive stable portion is the prefix. The variable details still reach the model, but they do not poison the cache key at the top. For an agent doing repeated reviews, that can reduce both latency and input cost while making the review rubric more salient. If quality drops after the reorder, the problem is not caching itself; it is that a current-task constraint was moved too far from the ask or compressed too aggressively.

### Instrumentation Example

Do not guess whether the layout improved caching. Log usage and calculate the share of input tokens served from cache. The following script reads JSON lines from a local agent log. Each line must include `prompt_tokens`, `cached_tokens`, and `latency_ms`.

```python
import json
from pathlib import Path

def load_runs(path: Path) -> list[dict]:
    runs = []
    for line in path.read_text().splitlines():
        if line.strip():
            runs.append(json.loads(line))
    return runs

def summarize(runs: list[dict]) -> dict:
    prompt_tokens = sum(run["prompt_tokens"] for run in runs)
    cached_tokens = sum(run["cached_tokens"] for run in runs)
    latency_ms = sum(run["latency_ms"] for run in runs)
    count = len(runs)
    cached_token_share = cached_tokens / prompt_tokens if prompt_tokens else 0
    return {
        "runs": count,
        "prompt_tokens": prompt_tokens,
        "cached_tokens": cached_tokens,
        "cached_token_share": round(cached_token_share, 3),
        "avg_latency_ms": round(latency_ms / count, 1) if count else 0,
    }

if __name__ == "__main__":
    log_path = Path("agent-cache-runs.jsonl")
    print(json.dumps(summarize(load_runs(log_path)), indent=2))
```

Create a small test log so the measurement has enough repeated structure to show a cache hit after the first uncached request:

```bash
cat > agent-cache-runs.jsonl <<'EOF'
{"prompt_tokens": 18000, "cached_tokens": 0, "latency_ms": 9200}
{"prompt_tokens": 18100, "cached_tokens": 15600, "latency_ms": 4100}
{"prompt_tokens": 17950, "cached_tokens": 15480, "latency_ms": 3980}
EOF
```

Save the preceding Python block as `cache_summary.py`, then run:

```bash
.venv/bin/python cache_summary.py
```

The expected output shape should show both the total prompt volume and the cached share, because a lower average latency without cached-token visibility is too ambiguous to trust:

```json
{
  "runs": 3,
  "prompt_tokens": 54050,
  "cached_tokens": 31080,
  "cached_token_share": 0.575,
  "avg_latency_ms": 5760.0
}
```

This is a toy measurement, but the operating habit is real. A context layout is not done until you can see whether it improves repeated work. For production harnesses, add outcome labels as well, such as "accepted patch," "missed rule," or "needed human correction." Cost and latency are useful only when paired with task success.

### Cache Trade-Offs

Caching does not mean every request should start with a giant static prefix. Static content has to earn its place. A stable prefix that includes outdated rules will faithfully cache outdated rules. A stable prefix that includes every possible policy may improve cache rate while degrading attention. Cache optimization must stay subordinate to task quality.

| Design choice | Cache effect | Attention effect | Decision |
|---|---|---|---|
| stable policy first | improves prefix reuse | makes rules salient | usually good |
| variable issue first | breaks reuse | makes current task salient | only use when request is one-off |
| all repo docs in prefix | may improve reuse | overloads attention | usually bad |
| compact repo map in prefix | improves reuse | preserves routing signal | usually good |
| current log at top | breaks reuse | may over-focus on transient evidence | avoid unless emergency |
| task ask at end | does not help prefix cache | improves recency | usually good |

The best layout often has a stable prefix and a crisp suffix. The prefix gives the model the operating contract. The suffix tells it what to do now.

## Session Context Versus Repo Context

All context eventually enters the same model window. That does not mean all context should be managed the same way. Session context is ephemeral. Repo context is persistent. Session context answers: "What has happened in this run?" Repo context answers: "What should every run know?"

Both are necessary. Confusing them creates rot. If a durable policy lives only in chat history, the next session forgets it. If a one-off failure log is copied into a permanent agent guide, future sessions inherit stale noise.

The boundary is not about file format; it is about lifetime and ownership. A Markdown guide, an issue comment, a local scratch note, and a JSON trace can all become context, but they carry different review paths and expiry expectations. Repo context should be durable enough that maintainers are willing to review it, and session context should be disposable enough that future agents are not forced to inherit yesterday's transient confusion.

### Comparison Matrix

| Context surface | Examples | Lifetime | Owner | Good for | Bad for |
|---|---|---|---|---|---|
| Chat history | decisions, clarifications, recent failures | one session | current operator | continuity inside a task | durable policy |
| Tool outputs | command results, file reads, API responses | minutes to hours | harness or agent | fresh evidence | long-term memory |
| AGENTS.md | workflow rules, branch policy, maps | weeks to months | repository maintainers | stable agent instructions | long debates |
| Structured docs | architecture, runbooks, rubrics | weeks to quarters | domain owners | explainable policy and design | transient logs |
| Code as context | tests, types, scripts, config | version history | code owners | executable truth | unexpressed intent |
| Retrieval corpus | tickets, docs, knowledge base | variable | platform team | external grounding | hidden enforcement |

The routing rule is simple: put information where its expected lifetime and ownership match. If it should survive a fresh session, put it in repo context. If it should disappear after the current task, keep it in session context. If it should be recomputed from code, do not duplicate it in prose unless the prose explains intent.

This rule also protects the repository from becoming a memory dump. Teams often respond to agent failures by adding another paragraph to the top-level instruction file, but every addition raises the cost of future context assembly. A better fix is often a small route in the top-level file plus a focused document elsewhere, so the agent learns where to go without carrying every detail on every turn.

### Repo Context Design

A repository should give agents a map, not a full manual at the top of every request. The map should point to stable sources. The stable sources should be small enough to load on purpose.

```text
repo-root/
  AGENTS.md
  docs/
    architecture/
      context-boundaries.md
    runbooks/
      build-and-test.md
    harness/
      checks.md
  scripts/
    check_context_layout.py
  src/
    ...
```

`AGENTS.md` should not become a dumping ground for every lesson learned. It should route the agent. For example:

```text
For build failures, read docs/runbooks/build-and-test.md.
For generated artifacts, read docs/harness/checks.md.
For architecture changes, read docs/architecture/context-boundaries.md.
```

That is repo-level context. It persists across sessions. It can be reviewed in pull requests. It can be tested with link checks. It can be shortened when it grows.

Good repo context is opinionated about routing and conservative about detail. It should name the files that are authoritative, explain the rules that cannot be inferred from code, and point agents toward runnable checks. It should not preserve every past debate, because old debate becomes ambiguous evidence when a future model is trying to infer current policy.

### Session Context Design

Session context needs a different discipline. The goal is not preservation; the goal is continuity without bloat. At each turn, the session should carry the few live facts that let the next action follow from the previous one:

- the current objective
- the latest accepted plan
- current open questions
- fresh evidence that changes the next action
- decisions that have not yet been written to the repo

It should not carry stale or resolved material merely because that material appeared earlier in the conversation:

- resolved command output
- disproven hypotheses
- entire files after a small excerpt was enough
- repeated policy already available in repo context
- long assistant explanations that no longer affect the task

Agent harnesses can implement this with rolling summaries. Humans can implement it manually by writing a short "current state" note before asking the next question. The note should be factual, not autobiographical, because the model needs operational state more than a narrative of how the session felt.

```text
Current state:
- Objective: make the new context module render cleanly.
- Files in scope: the new section index and module.
- Fixed: frontmatter parses.
- Open: Mermaid syntax and line-count gate.
- Next check: npm run build.
```

This is a compression boundary. It preserves decision state without preserving every token that produced it. The compression is only safe if it keeps open risks and superseded evidence separate; otherwise, a summary can silently turn an old hypothesis into an accepted fact.

### Routing Decisions

Use this decision table when deciding where context belongs, especially when a piece of information feels useful but does not obviously deserve a permanent home.

| Question | If yes | If no |
|---|---|---|
| Should a fresh agent know this next week? | repo context | session context |
| Is it executable truth? | code, tests, or scripts | docs or session note |
| Is it policy rather than evidence? | AGENTS.md or structured docs | tool output |
| Does it change per request? | suffix or session state | stable prefix |
| Is it sensitive or user-specific? | minimize and isolate | consider stable docs |
| Is it needed for one decision only? | session evidence | repo map |

The main risk is over-documenting transient facts. Repo context should remain clean enough that every new agent can afford to read it. Session context should remain fresh enough that every next turn can trust it.

When in doubt, choose the smaller durable surface and make expansion cheap. A top-level agent file can say "for release process, read the release runbook" instead of embedding the whole release process. A session note can say "current failure is the schema validator, older linter failures are resolved" instead of preserving three full logs. Those two moves keep the repo readable and the session current.

## Context-Rot Observability

Context rot is degradation caused by stale, bloated, contradictory, or misordered context. It often feels like the model "got worse." Sometimes the model is fine. The working set is bad. You can observe context rot before it wastes a whole session.

### Symptoms

Common signs include behavioral drift that would be hard to explain if the agent had a clean, current working set:

- the agent loops on a problem already resolved
- it contradicts an earlier accepted decision
- it forgets acceptance criteria after reading long logs
- it hallucinates filenames that do not exist
- it edits files outside the declared scope
- it repeats a tool call without using the result
- it treats old errors as current errors
- it asks for context that is already present but buried

Each symptom maps to a context failure class, so the repair should target the working set instead of blindly retrying the same prompt.

| Symptom | Likely context failure | First repair |
|---|---|---|
| loops on resolved problem | stale evidence remains salient | summarize resolved state and remove old logs |
| contradicts accepted decision | decision not promoted | move decision into task frame or repo doc |
| forgets acceptance criteria | criteria buried in middle | restate criteria near current ask |
| hallucinates filenames | repository map missing | load file tree or exact path list |
| edits outside scope | scope missing or contradicted | put scope in stable rule and current ask |
| repeats tool calls | tool outputs too noisy | extract the useful result and drop the rest |
| treats old error as current | freshness not labeled | label outputs with time and status |
| asks for present context | overload or poor ordering | shrink and reorder context |

### What To Instrument

Instrument context like you would instrument a service boundary. You need size, freshness, composition, and outcome. At minimum, log:

- total input tokens
- cached input tokens
- context sections included
- top files loaded
- tool-output token share
- age of last critical evidence
- number of unresolved open questions
- final outcome for the turn

The point is not to collect beautiful dashboards. The point is to make failure review factual. When an agent misses a rule, you should be able to answer: Was the rule present? Where was it located? Was it contradicted? Was it surrounded by noisy output? Did the session summary preserve it?

Those questions turn agent review into an operational practice. If the rule was absent, the fix is routing or retrieval. If it was present but buried, the fix is ordering or compression. If it was present and contradicted, the fix is source-of-truth cleanup. If it was present, salient, and still ignored, you may have a model capability issue, but that conclusion is much stronger after the context evidence is visible.

### Minimal Context Ledger

A context ledger is a small structured record of what the agent saw, what was current, and which outcome followed from that working set.

```yaml
turn_id: review-006
stable_prefix:
  - AGENTS.md
  - docs/harness/checks.md
task_frame:
  - issue summary
  - acceptance criteria
evidence:
  - src/content/docs/ai/ai-engineering-foundations/index.md
  - build error excerpt
tool_output:
  token_share_estimate: 0.18
freshness:
  build_error: current
  branch_policy: stable
outcome:
  status: needs_rerun
  reason: mermaid syntax corrected
```

This ledger can live in an agent trace, a local JSONL file, or a pull request note. It does not need to be long. It needs to tell reviewers whether the agent had the right working set.

The ledger is most useful when it is written before the next retry, not after everyone has already guessed at the cause. A short ledger can reveal that the agent never loaded the acceptance criteria, that the current failure was mixed with old failures, or that a permanent policy had become invisible behind a wall of tool output. That makes the next run a controlled experiment rather than another expensive reroll.

### Refresh Cycle

When rot appears, do not keep adding context. Refresh the working set by classifying the symptom, deciding whether to prune, promote, reorder, or retrieve, and then rebuilding the window from stable rules toward current evidence.

```text
+-------------------+     +-------------------+     +-------------------+
| detect symptom     | --> | classify context  | --> | prune or promote  |
| loop, miss, drift   |     | stale, absent,    |     | delete, summarize,|
| or contradiction    |     | buried, noisy     |     | or move to repo   |
+-------------------+     +-------------------+     +-------------------+
          ^                                                   |
          |                                                   v
+-------------------+     +-------------------+     +-------------------+
| observe next turn  | <-- | rerun with ledger | <-- | rebuild window    |
| outcome and cost    |     | size and outcome  |     | stable then fresh |
+-------------------+     +-------------------+     +-------------------+
```

This is the same operational loop as debugging a flaky service: observe, classify, repair one cause, rerun, and record the result. The discipline is to change one context variable at a time when you can, because a retry that changes model, prompt, files, retrieved documents, and ordering all at once teaches the team very little.

### Choosing The Repair

Use one of four repairs. Prune when the context is too large or stale. Promote when a decision should become durable. Reorder when important content is present but poorly placed. Retrieve when the missing fact exists outside the current session and repository context.

| Repair | Use when | Example |
|---|---|---|
| prune | resolved evidence dominates | replace full build log with current error |
| promote | a rule should survive sessions | move "never edit generated state" to AGENTS.md |
| reorder | content is present but ignored | put acceptance criteria near the current ask |
| retrieve | needed fact is external | fetch provider docs or issue history |

Do not use retrieval as a reflex. Retrieval is powerful when the missing fact is in a corpus. It does not fix overloaded session state or contradictory instructions. If the model is ignoring a rule already present in the prompt, adding ten more retrieved chunks usually makes the attention problem worse.

## Designing A Context Layout

A useful context layout is a repeatable assembly order. It should be explicit enough that another engineer or harness can rebuild it, and compact enough that the important pieces are still visible after real tool output arrives. Start with this baseline:

```text
+----------------------+
| 1. Stable prefix     |
| Rules, role, maps    |
+----------------------+
| 2. Semi-stable tools |
| Schemas, rubrics     |
+----------------------+
| 3. Task frame        |
| Issue, goals, limits |
+----------------------+
| 4. Fresh evidence    |
| Files, logs, outputs |
+----------------------+
| 5. Current ask       |
| Exact next action    |
+----------------------+
```

Then apply three checks. First, cache check: Does the repeated part appear before the variable part? Second, attention check: Are the highest-risk rules and success criteria at strong positions? Third, freshness check: Can the model tell which evidence is current?

Those checks should happen before the model call, not only during postmortem. If the stable prefix contains run-specific data, caching will be weak. If the acceptance criteria are buried in the middle, attention will be weak. If evidence is unlabeled, freshness will be weak. A layout that fails any of those checks may still fit inside the nominal window, but fitting is not the same as being usable.

### Example Layout For A Coding Agent

```yaml
stable_prefix:
  role: senior repository coding agent
  rules:
    - obey AGENTS.md
    - do not edit generated artifacts
    - keep scope limited to the issue
  output_contract:
    - summarize changed files
    - report tests run
semi_stable:
  repo_map:
    - src/content/docs
    - scripts
    - docs
  tool_contracts:
    - use ripgrep for search
    - use explicit virtualenv python path
task_frame:
  issue: write Context Engineering Fundamentals
  success:
    - module has required sections
    - line count gate passes
    - build passes
fresh_evidence:
  files_read:
    - module-quality.md
    - existing harness module
current_ask:
  action: draft, validate, commit, and open PR
```

This layout is not universal. It is a starting point. A security review would put threat model and trust boundaries into the task frame. An incident analysis would put current timeline and confirmed facts into fresh evidence. A migration plan would put compatibility constraints into the stable or semi-stable area.

### Evaluation Rubric

Before using a layout, evaluate it with these questions and make the answers visible enough that another engineer can challenge them.

| Dimension | Good answer | Weak answer |
|---|---|---|
| selection | each included item has a decision reason | included because it might help |
| ordering | stable prefix and current ask are deliberate | order follows discovery accident |
| freshness | stale and current evidence are labeled | all logs look equally current |
| cacheability | repeated prefix is stable | variable data appears first |
| reviewability | reviewer can see what was loaded | context is invisible in chat |
| portability | fresh session can reconstruct it | depends on one person's memory |

The layout should not optimize only for the model. It should also optimize for human review. If a reviewer cannot tell what context the agent used, they cannot tell whether the failure was model reasoning, missing input, or bad instructions.

## Did You Know?

1. OpenAI's prompt-caching guide says cache hits require exact prefix matches, so static instructions and examples should be placed before variable user-specific content. Source: [OpenAI Prompt Caching](https://developers.openai.com/api/docs/guides/prompt-caching).
2. Anthropic's prompt-caching docs describe automatic caching, explicit cache breakpoints, a default five-minute cache lifetime, and longer cache options for supported use cases. Source: [Anthropic Prompt Caching](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching).
3. DeepMind's "Leave No Context Behind: Efficient Infinite Context Transformers with Infini-attention" describes a bounded-memory architecture for scaling attention over long inputs without quadratic compute. Source: [arXiv:2404.07143](https://arxiv.org/abs/2404.07143).
4. Google Gemini's long-context documentation recommends using long inputs for tasks such as summarizing, querying, and reasoning across large documents, while context caching is documented separately for repeated content. Source: [Gemini Long Context](https://ai.google.dev/gemini-api/docs/long-context).

## Common Mistakes

| Mistake | Why it hurts | Better move |
|---|---|---|
| Putting timestamps or user-specific data at the top of every request | breaks stable prefix reuse and weakens cache benefits | place static policy and schemas first, variable details later |
| Loading the entire repository into context | increases cost, latency, and irrelevant attention competition | load a repo map first, then expand by reason |
| Calling context engineering "advanced prompt engineering" | hides the difference between instruction design and working-set design | name the layer and optimize the assembled turn state |
| Treating RAG as the whole context strategy | retrieval does not manage session history, repo policy, ordering, or cache layout | use RAG as one input source inside a broader context plan |
| Ignoring tool-output bloat | stale logs become more salient than current facts | summarize resolved outputs and keep only fresh evidence |
| Keeping durable policy only in chat | fresh sessions miss the rule | promote durable policy to AGENTS.md or structured docs |
| Copying transient failures into permanent docs | future sessions inherit stale incident state | store transient evidence in session logs or traces |
| Measuring token count but not outcome | a smaller window can still omit critical facts | measure cached-token share, latency, errors, and task success together |

## Quiz

### Question 1

Your team has a prompt that says, "Follow our repository rules," but a fresh agent still edits generated files. The previous successful session did not make that mistake. What context failure should you investigate first?

<details>
<summary>Answer</summary>

Investigate whether the generated-file rule exists in repo-level context and whether the fresh session loaded it early enough. This is not primarily a prompt phrasing issue. The missing or poorly placed input is likely a durable repository rule that lived in prior session memory. Promote the rule to AGENTS.md or a linked harness doc, then make the agent map load that source before editing.

</details>

### Question 2

An agent reads a huge failure log, then ignores a short acceptance criterion that appeared earlier in the conversation. The model's final answer is plausible but outside scope. How should you repair the next turn?

<details>
<summary>Answer</summary>

Do not paste more log output. Compress the log to the current causal error and restate the acceptance criterion near the current ask. This is a position and freshness problem: stale or bulky evidence has outcompeted the controlling requirement.

</details>

### Question 3

A platform team wants to improve cost and latency for repeated code reviews. Their current prompt starts with the issue body, current timestamp, and raw command output, then appends the stable review rubric. What layout change should they test?

<details>
<summary>Answer</summary>

Move stable policy, rubric, output contract, and tool schemas to the prefix. Place the issue body and command output after that stable prefix. Then log cached tokens, total input tokens, and latency across repeated requests to verify that the prefix cache improves the expensive shared portion.

</details>

### Question 4

An engineer proposes solving all context issues by adding vector search over every internal document. The agent's actual failure is that it keeps treating an old command error as current after the command has passed. Is RAG the right first fix?

<details>
<summary>Answer</summary>

No. The failure is stale session evidence, not missing external knowledge. The first fix is to label command output freshness, remove or summarize resolved errors, and rebuild the session state. Retrieval may help later if a needed document is absent, but it does not solve stale working-set state.

</details>

### Question 5

A security review agent performs better when given the full repository policy document, but the run becomes slow and expensive. The team wants to keep quality without paying that cost on every small review. What context strategy fits?

<details>
<summary>Answer</summary>

Use staged context. Start with a compact stable security map and the current task frame. Expand into the full policy only when a decision requires a specific rule. If repeated reviews need the same policy excerpt, place that stable excerpt in the prefix and measure cached-token share.

</details>

### Question 6

An agent forgets that the team already rejected a design option earlier in the task. The rejection matters only for this pull request, not future work. Where should that context live?

<details>
<summary>Answer</summary>

Keep it in session context, preferably in a short current-state summary or open-decisions note. Do not promote it to AGENTS.md unless it becomes durable policy. The right home follows lifetime and ownership.

</details>

### Question 7

A reviewer asks why an AI-generated patch missed a mandatory test. The agent claims the test instruction was present, but nobody can tell where it was loaded or whether it was buried in tool output. What should the team add?

<details>
<summary>Answer</summary>

Add a context ledger or trace that records which stable prefix, task frame, evidence, and tool outputs were included for the turn. The ledger should include enough size and freshness information to distinguish missing context from ignored context. That makes review factual instead of speculative.

</details>

## Hands-On Exercise

You will refactor an existing agent prompt and context bundle for cache use, attention quality, and fresh-session repeatability. Use a real workflow if you have one. If not, create a small mock workflow with an agent instruction file, a task prompt, a repository map, and two command outputs.

### Part A: Capture The Current Layout

- [ ] Choose one agent workflow that runs more than once per week.
- [ ] Save the current prompt or instruction bundle in a scratch file.
- [ ] List every context input the agent receives before its first tool call.
- [ ] Mark each input as stable prefix, semi-stable, task frame, fresh evidence, or scratch.
- [ ] Identify which inputs change on every request.
- [ ] Identify which inputs should survive a fresh session.

### Part B: Add Measurement

- [ ] Add logging for total input tokens if your provider exposes it.
- [ ] Add logging for cached input tokens or provider-specific cache-read fields.
- [ ] Add latency measurement around the model call.
- [ ] Add a list of included context sections to each trace record.
- [ ] Run the workflow at least three times with similar stable context.
- [ ] Record the baseline cached-token share and average latency.

### Part C: Refactor The Layout

- [ ] Move stable policy, role, output contract, and tool schemas before variable task data.
- [ ] Replace large stable documents with a compact map plus targeted excerpts.
- [ ] Move current acceptance criteria near the final ask.
- [ ] Delete or summarize resolved tool outputs.
- [ ] Label fresh evidence with current, stale, or superseded.
- [ ] Keep one explicit note for open questions and accepted decisions.

### Part D: Re-Measure

- [ ] Run the same workflow again with a similar task shape.
- [ ] Compare cached-token share before and after the refactor.
- [ ] Compare latency before and after the refactor.
- [ ] Inspect the output for missed rules or hallucinated files.
- [ ] Ask a teammate to reconstruct the agent's working set from your trace.
- [ ] Write one sentence explaining which context item moved to a better surface.

### Success Criteria

- [ ] The stable prefix no longer starts with variable user data.
- [ ] A fresh session can find durable policy without relying on chat history.
- [ ] The current task and acceptance criteria are easy to locate.
- [ ] Tool-output bloat is reduced or summarized.
- [ ] Cache metrics are visible for repeated runs.
- [ ] The measured result includes both quality and cost or latency observations.

## Sources

- OpenAI, "Prompt caching": [https://developers.openai.com/api/docs/guides/prompt-caching](https://developers.openai.com/api/docs/guides/prompt-caching)
- OpenAI Cookbook, "Prompt Caching 101": [https://cookbook.openai.com/examples/prompt_caching101](https://cookbook.openai.com/examples/prompt_caching101)
- Anthropic, "Prompt caching": [https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching)
- Anthropic, "Context windows": [https://docs.anthropic.com/en/docs/build-with-claude/context-windows](https://docs.anthropic.com/en/docs/build-with-claude/context-windows)
- Anthropic, "Effective context engineering for AI agents": [https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- Anthropic, "Building effective agents": [https://www.anthropic.com/engineering/building-effective-agents](https://www.anthropic.com/engineering/building-effective-agents)
- Google, "Gemini API long context": [https://ai.google.dev/gemini-api/docs/long-context](https://ai.google.dev/gemini-api/docs/long-context)
- Google, "Gemini API context caching": [https://ai.google.dev/gemini-api/docs/caching](https://ai.google.dev/gemini-api/docs/caching)
- Google DeepMind, "Leave No Context Behind: Efficient Infinite Context Transformers with Infini-attention": [https://arxiv.org/abs/2404.07143](https://arxiv.org/abs/2404.07143)
- Nelson F. Liu et al., "Lost in the Middle: How Language Models Use Long Contexts": [https://arxiv.org/abs/2307.03172](https://arxiv.org/abs/2307.03172)
- Chroma Research, "Context Rot": [https://www.trychroma.com/research/context-rot](https://www.trychroma.com/research/context-rot)
- Gim et al., "Prompt Cache: Modular Attention Reuse for Low-Latency Inference": [https://arxiv.org/abs/2311.04934](https://arxiv.org/abs/2311.04934)
- Lewis et al., "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks": [https://arxiv.org/abs/2005.11401](https://arxiv.org/abs/2005.11401)

## Next Module

Continue with [Module 2.2: Repository Engineering for Agents](../module-2.2-repository-engineering-for-agents/). That module focuses on making repository structure, indexes, docs, scripts, and tests act as durable context surfaces for AI coding agents.

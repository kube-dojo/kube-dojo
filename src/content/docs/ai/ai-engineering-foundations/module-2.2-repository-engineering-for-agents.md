---
title: "Repository Engineering for Agents"
slug: ai/ai-engineering-foundations/module-2.2-repository-engineering-for-agents
sidebar:
  order: 22
revision_pending: false
---

> **Complexity**: [COMPLEX]
>
> **Time to Complete**: 90-120 min
>
> **Prerequisites**: Module 2.1 Context Engineering Fundamentals or equivalent; familiarity with repository layout, Git workflows, and Markdown documentation.

## Learning Outcomes

By the end of this module, you will be able to: This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle..

- **Design** a repository-level agent legibility stack and justify where each layer lives.
- **Differentiate** system-of-record files from ephemeral task memory and ephemeral execution logs.
- **Engineer** progressive-disclosure instruction files that prevent context drift and stale rules.
- **Compose** structured `docs/` surfaces that transform policy, architecture, and operations into machine-readable guidance.
- **Map** how a repository can “talk back” to an agent through API endpoints, checks, and status surfaces.

## Why This Module Matters

Mira has seen one more task bounce back and forth.
She asked an agent to fix a bug, then ran a different check, then got a patch that violated an obvious repo rule.
The repo had good docs somewhere, but the agent never found the right page at the right moment.

This module treats repository design as the difference between “reasonable instructions” and “usable instructions.”
A poorly engineered repository can still have great people and great models, and still fail repeatedly.
A well-engineered repository gives agents a stable map, a clear load order, and explicit feedback loops.

Repository engineering for agents is not documentation theater.
You are not writing yet another long instruction file.
You are designing a load-bearing contract surface.

The contract has three constraints.
First, an agent must discover the right context quickly.
Second, context must stay trustworthy over time.
Third, the repository must continuously signal what changed since the last run.

In this module, you will learn how to satisfy all three while avoiding the classic failure modes of brittle, overgrown AGENTS-like files and one-size-fits-all instructions.

## The Problem We Keep Solving in Long AI-Work

Team-level AI workflows usually break in one of four recurring ways. This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle.

### 1) The one-file monolith

A single AGENTS-like file grows until it becomes a museum.
It includes policy, style, branch rules, secrets hygiene, PR etiquette, test order, deployment notes, and platform quirks all in one place.
The file eventually becomes noise.
Agents still load it, but the signal-to-noise ratio drops.

### 2) The missing map

Some repos have many files but no discoverable entry path.
The agent reads random rule files and misses the system-of-truth folder.
By the time it lands on the right page, the task context has shifted.

### 3) The stale loop

A stale rule says branch `main`, but the repo moved to `main` plus `release` and `stage`.
An obsolete review cadence says run one check, while the CI now requires three.
An old checklist tells the agent to skip an expensive but now required step.
This mismatch is not hypothetical.

### 4) The blindfolded repo

The repo returns no structured signals beyond a final success line.
It might compile but still violate governance.
An agent cannot “learn” repo expectations if the repo does not expose what was expected or what failed.

If you can prevent these four modes, you dramatically improve correctness, review quality, and merge predictability. This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle.

## What AGENTS.md and CLAUDE.md actually become in agent engineering

AGENTS.md and CLAUDE.md are not the system itself.
They are the repository front-door summary and route map. This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle.

In practical terms: This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle..

- They establish *what to read first*.
- They establish *where the stable norms live*.
- They establish *how deeper documents are organized*.

AGENTS.md generally serves an ecosystem where many agent families may run.
CLAUDE.md gives a Claude-specific memory surface for Anthropic tooling.
The two can overlap.
The overlap should be intentional.

The goal is not duplicate text.
The goal is a clearly layered contract where each file has authority in a specific slice of the problem.

```text
+----------------------+------------------------------+------------------------------+
| Concern              | First load (stable)           | Deferred deeper load          |
+----------------------+------------------------------+------------------------------+
| Governance           | CLAUDE.md, AGENTS.md         | .claude/rules/*.md            |
| Repository shape      | AGENTS.md TOC section        | docs/ + module maps           |
| Safety expectations   | AGENTS.md + CLAUDE.md        | review checklists and reviews  |
| Runtime behavior      | .claude/rules + scripts      | local API + state endpoints    |
| Task-specific hints   | Prompt or task-specific prompt | docs/operational/ playbooks     |
+----------------------+------------------------------+------------------------------+
```

The table is a template, not a law.
It helps force a design decision.
If the line is “task-specific hints” then the repo should not hardcode those into AGENTS.md.

## Progressive Disclosure as a design principle

Progressive disclosure is the discipline of ordering context by stability, reuse, and expected drift.
It is not a UI concept copied into docs.
It is a memory-safety principle for AI work.

Imagine context as a memory hierarchy.
The first layer must always be safe to keep.
The second layer must support repeatable operations.
The third layer should stay narrow and time-bound.

```text
+--------------------------------------------------------------+
| Layer  | Stability            | Change cadence | Agent read-time policy |
+--------+---------------------+----------------+-----------------------+
| L0     | High                 | Slow           | Always load            |
| L1     | Medium               | Moderate       | Load when in subtree    |
| L2     | Low                  | Frequent       | Load on demand only     |
| L3     | Ephemeral            | Real-time      | Load from current task   |
+--------+---------------------+----------------+-----------------------+
```

### L0: Always-loaded map files

L0 includes your highest-level bootstrap files.
If every agent starts with your repository, this layer should include: This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle..

- one path to the main workflow contract,
- one path to safety and branch policy,
- one path to docs index,
- and one path to execution checks.

AGENTS.md and root CLAUDE.md are common L0 occupants.
But they should remain compact.
A compact L0 means 100-250 high-leverage lines, not a 3,000-line instruction book.

### L1: Repository-locally discoverable slices

L1 should include scoped rules and recurring playbooks.
In this layer: This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle..

- rules apply to common workflows,
- changes are infrequent,
- text should be stable across many tasks,
- examples should be durable and explicit.

This is where `.claude/rules`, architecture notes, and recurring task-runbooks usually live. This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle.

### L2: Role-specific and workflow-specific documents

L2 holds targeted instructions tied to roles, features, or recurring domains.
A few examples: This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle..

- docs for onboarding,
- docs for PR review,
- docs for module publishing,
- docs for issue triage,
- docs for release hygiene.

These are not ignored.
They are loaded when needed and often become the differentiator between a decent agent workflow and a high-precision one.

### L3: Dynamic run surfaces

L3 is what the repo tells the agent about the *current* run.
Think of it as per-task telemetry.
Examples include:

- current pipeline state,
- open issue constraints,
- required checks for the task,
- open warnings from local APIs,
- and review history for this module.

For L3, the repository becomes operational, not only descriptive. This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle.

## The bootstrap stack for this repository

KubeDojo’s own stack is intentionally explicit.
The root `CLAUDE.md` gives agent entry rules and workflow requirements.
The `scripts/cold-start.sh` script enforces issue-first onboarding and surfaces current project state.
`.claude/rules/` adds scoped conventions for review, module quality, module migration decisions, and translation constraints.

That means the root instructions are not just helpful prose.
They are a real first-run contract.
Agents are expected to consume this as the base layer.

A useful design rule for any repo is this: This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle..

- if a policy is required before any tool call, it belongs in bootstrap or always-on layer,
- if policy is only needed for one domain, keep it in scoped docs,
- if a requirement is temporary, keep it in the task layer.

## The “docs/` as system of record” model

A well-engineered repository treats `docs/` as the durable interface between humans and agents.
Humans maintain structure.
Agents consume structure.
When both sides align, the repo becomes easier to operate.

For this model to work, documentation has to meet three criteria: This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle..

1. **Stable authority**: statements should be true for the module until intentionally revised.
2. **Machine readability**: enough section headings, anchors, and predictable names for tooling and retrieval.
3. **Review pressure**: every change to docs should be reflected in checklists, PR templates, or state surfaces.

A practical pattern is to separate docs by intent. This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle.

```text
+----------------------+----------------------------------------------+
| Folder intent        | Primary consumer                               |
+----------------------+----------------------------------------------+
| src/content/docs     | Long-term learning, policy, and design records  |
| .claude/rules        | Scoped agent operating constraints            |
| scripts/*            | Operational contracts and automation surfaces  |
| docs/research        | Strategic research and brief summaries         |
+----------------------+----------------------------------------------+
```

This repository already uses that structure by design.
`docs/` is not the only source of truth.
But it is the highest-value source for persistent repository knowledge.

## Designing the AGENTS chain

You do not need one giant AGENTS strategy document.
You need a predictable chain.
Here is a reliable sequence:

### Step 1: root bootstrap card

Create or verify a short root file that answers: This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle..

- where checks live,
- what command order governs each run,
- what forbidden outputs are banned,
- and where deeper instructions are linked.

### Step 2: scope folders

If repository sections have unique logic, add scoped files.
The scope can be by tab, domain, or operational area.
A file in a subfolder should override root instructions when conflicts are explicit.

### Step 3: stable-to-dynamic linking

Use short links and explicit anchors.
Every scoped file should point to deeper documents rather than duplicate them.

### Step 4: periodic audits

Every quarter, read and prune: This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle..

- stale process calls,
- outdated tools,
- moved folders,
- changed ownership names.

If an instruction file has not changed in a year but still describes current work, test it.
If it no longer matches real behavior, remove or move it down the stack.

### Step 5: feedback hooks

The chain must include where violations surface.
If a rule exists and is not checked, it is not an instruction, only lore.

## CLAUDE.md as layered memory in this model

In Anthropic tooling, CLAUDE.md gives project-context memory that is hierarchy-aware.
Agents use the file system to inherit higher-level and lower-level instructions automatically.
That makes CLAUDE.md a strong candidate for one part of L0 or L1.

It must not absorb every policy.
For robust stacks: This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle..

- root CLAUDE.md: startup posture and cross-project conventions,
- nested CLAUDE.md: domain-specific context,
- references to `docs/` pages for durable design and policy,
- links to local endpoints for current state.

The important distinction: This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle..

- CLAUDE.md is memory bootstrap.
- AGENTS.md is often ecosystem-level bootstrap and agent-facing index.
- docs pages are durable records and behavior contracts.

You can use both without contradiction.
When they overlap, choose the closest applicable layer as source of truth for that concern.

## How a repository should “talk back”

A repository that teaches passively only lowers confidence.
A repository that teaches interactively improves agent behavior.
“Talking back” means the repo emits structured signals during and after each run.

For KubeDojo, three signal classes are especially useful. This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle.

### Structural signals

The API exposes module and lease state.
Before touching a module, check live state and active constraints.
This reduces duplicate work, conflicting edits, and stale assumptions.

Examples: This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle..

- `GET /api/pipeline/leases`
- `GET /api/module/{key}/state`
- `GET /api/reviews?module={key}`
- `GET /api/tracks/readiness`
- `GET /api/activity`

### Quality signals

Quality surfaces include static checks and scoring surfaces.
An agent should run a quality-aware workflow because these checks shape what “done” means.
In this repo, the required checks are already documented in local instruction rules.
Not every learner should memorize every command.
They should know where that inventory lives and which check corresponds to which phase.

### Health signals

`scripts/check_site_health.py` and module verify scripts provide objective health checks.
If those checks pass, behavior is usually safe to merge.
If they fail, the repo is trying to tell you that instruction and implementation are diverging.

## From instruction to executable contracts

The goal is not only readable text.
An instruction surface must become executable checks.
The most common failure is static prose with no mechanical hook.

A minimal contract pattern: This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle..

1. Statement in instruction file.
2. Corresponding command in `scripts/*`.
3. Automated check with stable command name.
4. CI or local check gate.
5. Review path when check fails.

## Repository interface for agents: a design framework

Use this architecture lens when auditing a repository. This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle.

```text
+----------------------+---------------------------+-------------------------------+
| Surface              | Question asked            | Quality test                   |
+----------------------+---------------------------+-------------------------------+
| Bootstrap files      | Can agent start safely?    | Loads without contradiction    |
| Rules & norms        | Are restrictions explicit? | Covered by checks/review        |
| Structured docs      | Where does truth live?     | Searchability + freshness       |
| Scripted feedback     | Can it report current state?| API + command stability         |
| Observability surfaces | Can it explain failures?  | Logs + summary output           |
+----------------------+---------------------------+-------------------------------+
```

Your design objective is to maximize positive findings in all five columns. This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle.

## Four mandatory design questions

Before writing any instruction file, ask and answer: This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle..

1. What is always true for this repository?
2. What is usually true but subject to change?
3. What is temporary for this specific work?
4. What does the repo report after each run?

If you cannot answer these quickly, your instructions are too broad. This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle.

## The repository as a contract with multiple readers

Different readers extract different meaning from the same files.
Agents and humans need aligned grammar. This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle.

- **Humans** want rationale and narrative.
- **Agents** want stable extraction points.
- **CI** wants commandable invariants.
- **Reviewers** want auditability and deterministic checklists.

A single section can serve all if authored with this principle: This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle..

- first line states policy,
- second line states why,
- third line points to the command,
- fourth line points to a review artifact.

## Layered instruction pattern for real modules

A practical scaffold for module authoring: This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle..

```text
ModuleRoot/
  module-name/
    module.md          # compact module-level learning contract
    tasks/
      hands-on.md      # optional, if task flow is large
    checklists/
      preflight.md     # optional runtime checklist
```

Do not require every module to include all folders.
Do require each module to state at least one stable path to:

- how to start,
- how to verify,
- how to report completion.

## What should not go into AGENTS.md

A strong anti-pattern is loading AGENTS.md with one-time or rapidly changing instructions.
Use targeted docs instead. This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle.

- PR-specific reviewer names,
- one-off issue details,
- temporary local branch naming experiments,
- unresolved design drafts.

If this content becomes frequent, move it into: This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle..

- task prompt,
- issue comments,
- per-module notes,
- temporary run logs.

## When CLAUDE.md should be split

A single CLAUDE.md becomes fragile when: This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle..

- it contains unrelated instructions for distinct domains,
- multiple teams modify it without ownership boundaries,
- nested directories conflict silently,
- and readers can no longer identify active scope.

In that case, split by subtree where edits are independent.
That split may mirror source structure, team boundaries, or subsystem ownership.

## Repository anti-fragility: stale-aware design

Every repository instruction system ages.
A strong pattern is a simple stale policy. This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle.

### Staleness policy sample

For every instruction file: This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle..

- define an owner,
- define expected review cadence,
- define a deprecation note,
- define migration target.

If a file fails cadence twice in a row, move it into task-local scope or delete it. This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle.

A stale-file score can be calculated manually. This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle.

```text
+-------------------+----------------+------------------+--------------------------+
| File              | Last modified  | Last effective   | Action                     |
+-------------------+----------------+------------------+--------------------------+
| AGENTS.md         | older than 60d  | unchanged 30d     | review required            |
| CLAUDE.md         | older than 45d  | changed twice/mth  | refresh mapping sections    |
| docs/ modules     | older than 120d | unchanged 60d     | verify against scripts      |
| .claude/rules     | older than 30d  | changed 10d         | force owners review         |
+-------------------+----------------+------------------+--------------------------+
```

## Repository surfaces in practice: a blueprint

A repository that can be used by agents should expose four primary documents: This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle..

1. Orientation document.
2. Standards and review document.
3. State and health document.
4. Escalation and override document.

### Orientation document

This is the first file an agent should always be able to resolve.
In KubeDojo, root `CLAUDE.md` and scripts entrypoints serve this role.

### Standards and review document

This is where long-lived behavior rules live.
For example: This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle..

- issue-first workflow,
- branch expectations,
- PR conventions.

### State and health document

This is where current conditions are exposed.
For example: This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle..

- module-level pipeline state,
- quality state,
- active blockers,
- local API warnings.

### Escalation and override document

This is where conflict resolution is described: This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle..

- which guidance wins at conflict,
- what manual checks are mandatory,
- where to report and close contradictions.

## Example architecture: how to teach an agent what to ignore

Agents do poorly when asked to reason over generated files, vendor directories, and throwaway outputs without explicit exclusions.
Include explicit exclusions in bootstrap and in task checklists.

Examples of exclusions: This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle..

- build directories,
- dist artifacts,
- cache directories,
- database and message store files,
- generated lockfiles that are environment-specific,
- ephemeral PID files.

In this repository, generated run artifacts are already called out in AGENTS-like constraints.
The same idea should appear in your own project.

## Designing repo legibility with file-level contracts

File-level contracts are specific statements attached to known files.
A few patterns: This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle..

```text
# Contract pattern A — Immutable baseline
File: src/content/docs/<path>/index.md
Contract: this page defines module navigation and purpose.
Owner: module lead.
Refresh: when curriculum spine changes.

# Contract pattern B — Execution invariant
File: scripts/*
Contract: command output and failure mode should remain machine predictable.
Owner: script author.
Refresh: before every release.

# Contract pattern C — Cognitive map
File: CLAUDE.md
Contract: bootstrap contract and first-order instructions.
Owner: maintainers.
Refresh: weekly for active repos.
```

For each file, state both “what it does” and “why it does it,” then link to a check command.

## Hands-on checklist design for repository authors

Your module should teach action, not only theory.
A practical authoring cycle: This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle..

1. Start from the issue.
2. Draft the contract surfaces.
3. Add links and exclusions.
4. Add verification commands.
5. Add feedback surfaces.
6. Run checks.
7. Update index.

Each step should include owner and next state. This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle.

## The minimal contract set for a healthy repo

An effective minimum set in this model has seven files/components. This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle.

- `AGENTS.md` or equivalent.
- `CLAUDE.md` or equivalent.
- `scripts/cold-start` equivalent.
- one `local` API or script to query current run context.
- one module checklist for review.
- one quality entrypoint check.
- one health check.

If a repository lacks at least one component, the repo is not currently “agent-friendly.” This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle..

## Worked example: repository design walkthrough

Below is a worked walkthrough for a hypothetical repository. This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle.

### Step A: Start from breakage

The repo often fails because agents miss branch constraints and run commands in the wrong order. This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle.

### Step B: Choose L0 files

The team adds a compact root AGENTS-like file listing required preflight checks and links. This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle.

### Step C: Add memory links

A root CLAUDE.md entry points to scoped rule files for API, docs, and deployments. This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle.

### Step D: Build docs map

`docs/` contains a “for AGENTS and agents” subsection with: This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle..

- system map,
- review invariants,
- check ordering,
- and common operational gotchas.

### Step E: Add talkback endpoints

A local API endpoint now exposes: This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle..

- active module,
- required checks,
- quality score,
- and blocker status.

### Step F: Introduce stale checks

A periodic checklist now asks owners to trim outdated instructions every 30 days. This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle.

### Step G: Validate

Now each agent run follows the same route.
Context quality improves, and the same task is less sensitive to chat window age.

## Layer-by-layer design rubric

You can evaluate your repository design with this matrix. This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle.

```text
+--------------------+-------------------------+--------------------------+-------------------+
| Layer              | Design indicator         | Evidence check            | Failure signal     |
+--------------------+-------------------------+--------------------------+-------------------+
| Orientation         | One file gets you started| bootstrap check passes    | repeated clarifications |
| Memory              | Instructions are layered  | nested memory load         | conflicting rules |
| Content             | docs map stays current   | versioned docs links       | stale copy/paste |
| Feedback            | run-time state is exposed | API/state endpoint query   | silent failures |
| Governance          | exceptions are explicit   | review notes + logs        | silent rule drift |
+--------------------+-------------------------+--------------------------+-------------------+
```

## Designing for scale across many issue types

Small repos can get away with one file.
Large repos need more shape. This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle.

### Multi-team pattern

Each team gets scoped docs.
Global rules stay small.
Scoped rules override global where local scope is explicit.

### Multi-model pattern

Different AI models and tools parse instructions differently.
Keep stable commands and names consistent.
This reduces model-specific variance.

### Multi-runtime pattern

One run happens locally.
One run happens in CI.
One run happens in reviews.
The repository should emit the same expected state to each runtime.

## Practical contract artifacts you should build

A mature repository has at least these artifacts: This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle..

1. **Navigation card**: where to start.
2. **Execution card**: what to run and when.
3. **Risk card**: what not to do.
4. **Recovery card**: where to check failures and how to restart.
5. **Closure card**: what constitutes a successful run.

Each card can live in docs or in command output, but links should exist from bootstrap files. This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle.

## Avoiding instruction debt

Instruction debt accumulates in three ways. This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle.

- one-time task assumptions copied into baseline rules,
- outdated historical incident notes left in bootstrap,
- duplicate instruction copies in multiple files.

When debt is high, agents do not get confused because they cannot parse ambiguity.
They act on ambiguity.

To prevent debt, require ownership tags.
For example: This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle..

- Owner: module maintainer,
- Reviewer: quality reviewer,
- Expiry review date,
- Migration note.

## Repository engineering as a social contract

This is technical and social.
Agents are not replaced by this process.
Humans still decide architecture, ownership, and quality.
The engineering work is to let humans make those decisions once and let agents execute repeatedly.

A repo that talks back to an agent creates better collaboration because: This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle..

- humans spend less time repeating context,
- agents spend less time rediscovering policy,
- and failures are easier to diagnose.

## The design exercise: map this repo to four layers

Try this for your own repository.
For each layer, fill one sentence. This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle.

- **Layer 0**: what file always loads and why.
- **Layer 1**: what file scopes by folder and who owns it.
- **Layer 2**: where role-specific behavior and tool choices live.
- **Layer 3**: where current-run state and telemetry are published.

Then add at least one check command per layer. This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle.

## Did You Know

- Repositories that survive long AI-first programs keep boot instructions short and keep deep context in linked `docs/`.
- The most stable failure signals come from scripts and APIs, not from prose that is not tied to checks.
- Progressive disclosure is usually more reliable than comprehensiveness because it reduces context collisions between tools and teams.
- A reusable agent repository surface uses nested files, explicit links, and explicit state endpoints at every scale.

## Common repository mistakes and anti-patterns

The following table is diagnostic. Use it while auditing your own files. This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle.

## Common Mistakes

| Mistake | Why it harms agents | Typical symptom |
|---|---|---|
| One giant AGENTS file without sections | Overload and ambiguous priority | Agents skip critical constraints |
| No nested instruction overrides | Global rules override local needs silently | Team-specific tasks fail for local conventions |
| Instructions duplicated in many places | Conflicting stale copies | Different runs contradict each other |
| `docs/` used as dumping ground | No stable index of truth | Agents open wrong file repeatedly |
| No machine-readable state surface | Hidden failures remain silent | Repetition of same fix loop |
| Generated artifacts mixed with source docs | Noise in search results | Agents ingest garbage context |
| No periodic review for instruction files | Context drift becomes systemic | Outdated policy appears “current” |

## What a repo surface should contain in this module’s scope

This module focuses on a practical design bundle: This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle..

- a compact repository-level map,
- a scoped memory hierarchy,
- structured `docs/` records,
- and operational feedback endpoints.

For learning, this means the minimum implementation is: This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle..

- one root bootstrap file,
- one hierarchical memory file,
- one set of structured docs,
- one quality check,
- one health check,
- and one escalation route.

## Design patterns for AGENTS-like files

Use the following layout pattern. This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle.

```text
# Root map
- What this repo is,
- how agents should start,
- where deeper docs live,
- where checks are run.

# Stable invariants
- branch policies,
- required checks,
- code organization constraints.

# Runtime route
- relevant APIs,
- health endpoints,
- review path.
```

Do not include: This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle..

- ephemeral one-off issue details,
- deep technical history,
- and long unowned troubleshooting transcripts.

## Checklist design for maintainers

A concise maintainability checklist for repository engineering: This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle..

1. Is the entrypoint short enough to read quickly?
2. Are command paths explicit and deterministic?
3. Are temporary notes scoped to tasks?
4. Are generated directories explicitly excluded?
5. Is there a “next step after failure” route?
6. Is the docs index discoverable from bootstrap files?
7. Are layered files mutually consistent?

If any answer is no, file triage is required. This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle.

## How to design this for a real team in one week

Week 1: This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle..

- Day 1: inventory existing rules and duplicates.
- Day 2: define map-only root AGENTS/CLAUDE.
- Day 3: move stable facts into docs structure.
- Day 4: split nested scoped instructions.
- Day 5: expose state and health commands.
- Day 6: add missing review surfaces.
- Day 7: run checks and collect first failure pattern.

Week 2 and beyond: This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle..

- add stale checks,
- add ownership metadata,
- add automated reminder to remove stale sections.

## Knowledge as reusable modules

A repository designed for agents should support both quick start and deep dives.
A quick start path gives short-term speed.
A deep-dive path gives long-term correctness.

Quick-start path: This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle..

- run cold-start,
- review state,
- open module index,
- run module checks.

Deep-dive path: This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle..

- inspect review history,
- inspect instruction deltas,
- inspect pipeline status,
- and trace failure sequences across runs.

## The “if not represented, enforce” rule

If an expectation affects behavior, and the repo cannot represent it in a file or command, the expectation is probably not enforceable.
Enforceability is what turns human preferences into machine trust.

A non-enforced expectation is still useful context but not operational truth. This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle.

## Designing for portability across model families

Different models and frameworks load context differently.
You can reduce variance by using: This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle..

- concise L0 instructions,
- stable file names,
- low churn for bootstrap,
- deterministic check commands,
- and explicit state surfaces.

This matters in mixed-model workflows and in multi-tool review loops. This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle.

## How to express model-agnostic contracts

Do not write instructions as one tool’s command syntax.
Write them as behavior expectations and expected states.
For tool specifics, provide per-tool examples as examples, not as only definitions.

For example: This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle..

- “Do not run commands that mutate hidden state without a rollback plan.”
- then optionally:
  - “For Git, use standard commands in review mode.”
  - “For local APIs, use explicit endpoints.”

The behavioral contract stays model-agnostic. This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle.

## Operationally safe defaults

The safest defaults for repository engineering are conservative.
If uncertain, prefer explicitness over coverage. This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle.

- explicit exclusions,
- explicit scopes,
- explicit update paths,
- and explicit failure messages.

## Practical lab: design a two-layer bootstrap for this module

1. Write one root map section that answers start state and run order.
2. Write one scoped section under a dedicated directory for this module.
3. Add one command that prints the current run contract.
4. Add one check that fails on stale or conflicting instructions.
5. Add one link from the module back to the parent contract.

## Design challenge: avoiding false safety in instructions

A false-safe instruction is one that looks strict but does not stop bad outcomes.
That happens when: This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle..

- constraints reference files that no longer exist,
- examples show only happy path,
- and checks are not wired.

Use this audit phrase while reviewing any instruction layer: This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle..

“Can this rule be violated without failing a check?” This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle..

If yes, it is informative but not enforceable. This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle.

## Knowledge Check

### 1) Which statement best describes progressive disclosure for repository legibility?
<details>
<summary>Which statement best describes progressive disclosure for repository legibility?</summary>

A) Place all instructions in one file so agents never need to jump around.  
B) Separate short-lived details from stable contracts so that agents can load the right layer first.  
C) Keep everything in generated logs because those are always up-to-date.  
D) Store everything in PR comments so it is always visible.  

**Correct answer: B** because stable contracts should be short and frequently reused, while temporary rules remain scoped and on-demand. **A is wrong** because it increases ambiguity and reduces signal strength. **C is wrong** because logs are often noisy and not stable. **D is wrong** because PR comments are not a contract surface for every run.
</details>

### 2) Which layer should host high-frequency operational policies?
<details>
<summary>Which layer should host high-frequency operational policies?</summary>

A) A single root AGENTS file with every possible constraint, regardless of longevity.
B) Layered scope files plus a stable root map that links to them.
C) Only ephemeral task prompts that reset every session.
D) A generated changelog only.

**Correct answer: B** because stable, repeatable policies need predictable location and links from root, while prompts handle task-specific details. **A is wrong** because it becomes stale and verbose. **C is wrong** because ephemeral prompts cannot represent durable governance. **D is wrong** because changelogs are historical and not operational bootstrap.
</details>

### 3) Why is a `docs/` structure considered a system of record in this module?
<details>
<summary>Why is a structured `docs/` considered a system of record?</summary>

A) Because it can store all agent instructions in raw binary format.
B) Because it is the first place every agent reads automatically.
C) Because it can hold durable, reviewable, and versioned instructions that can be linked and revised intentionally.
D) Because it is required by every model family and automatically replaces all rules.

**Correct answer: C** because `docs/` provides durable structure, traceable updates, and reviewability. **A is wrong** because the content model remains human-readable text, not binary instructions. **B is wrong** because bootstrap can include other files, and first load does not guarantee completeness. **D is wrong** because replacement is context-specific and unsafe.
</details>

### 4) What is the most accurate interpretation of “repo talks back” in this context?
<details>
<summary>What is the most accurate interpretation of "repo talks back"?</summary>

A) The repo should always print friendly messages.
B) The repo should expose status, checks, and constraints that can be observed by agents before and after action.
C) The repo should block all automated edits.
D) The repo should avoid runtime signals to reduce noise.

**Correct answer: B** because reproducible feedback channels are what allow agents to adapt actions in a safe loop. **A is wrong** because decorative output without operational signals is insufficient. **C is wrong** because blocking all automation is the opposite of efficient workflow. **D is wrong** because observability is needed for reliable operations.
</details>

### 5) Which item best fits a stale-rule anti-pattern?
<details>
<summary>Which item best fits a stale-rule anti-pattern?</summary>

A) A rule reviewed weekly with ownership and migration notes.
B) A command copied into one file years ago and never updated despite changed tooling.
C) A root file that links to scoped documents for deeper detail.
D) A task prompt that references a current issue branch.

**Correct answer: B** because stale copied rules mislead agents and undermine trust. **A is wrong** because it implies active maintenance. **C is wrong** because it supports discoverability and freshness. **D is wrong** because task prompts are temporary, not stale base policy.
</details>

### 6) In this module’s design model, what should avoid being in a permanently loaded file?
<details>
<summary>In this module’s design model, what should avoid being in a permanently loaded file?</summary>

A) Stable governance and branch constraints.
B) One-off issue notes.
C) Scope links to module-specific docs.
D) Core execution checks.

**Correct answer: B** because one-off issue notes become stale and should be task-local. **A is wrong** because stable constraints belong in always-loaded references. **C is wrong** because scope links are high-value discoverability paths. **D is wrong** because core checks are central to safe operation and should be discoverable.
</details>

### 7) Which statement reflects the best ownership pattern for instruction files?
<details>
<summary>Which statement reflects the best ownership pattern for instruction files?</summary>

A) Only one person owns every instruction file globally.
B) No ownership is needed as long as files are descriptive.
C) Each file has a scope, owner, and refresh path, with nested files overriding conflicts.
D) Root ownership is enough for all scoped folders.

**Correct answer: C** because scope plus ownership plus refresh policy reduces drift and clarifies update responsibility. **A is wrong** because that model becomes a bottleneck and misses domain ownership. **B is wrong** because ownership enables consistency and maintenance cadence. **D is wrong** because scope-level conflicts require delegated and explicit ownership.
</details>

## Hands-on Practical Exercises

- [ ] Audit your repo root bootstrap by listing the first five files loaded before any task work, then mark which are stable L0 and which are scoped L1.
- [ ] Build a `Repository Legibility Sheet` in one markdown file with four layers, links, and one health-check command for each layer.
- [ ] Add one `docs/` entry as a durable contract for agent execution and one explicit exclusion list for generated artifacts.
- [ ] Define a short failure feedback loop: identify one endpoint or command that should run after every task and explain how it changes next actions.
- [ ] Draft a stale-rotation rule that assigns an owner and cadence to each bootstrap and scoped instruction file.

## Next Module

Next module: [Semantic vs Lexical Context](module-2.3-semantic-vs-lexical-context/) This keeps the repository contract observable and lowers onboarding costs while preserving auditable behavior for each new agent cycle..

## Sources

- [Harness engineering (OpenAI)](https://openai.com/index/harness-engineering/)
- [Give Claude context with CLAUDE.md (Anthropic Support)](https://support.claude.com/en/articles/14553240-give-claude-context-claude-md-and-better-prompts)
- [Claude Code memory model (Anthropic docs)](https://docs.anthropic.com/en/docs/claude-code/memory)
- [AGENTS.md project format](https://agents.md/)
- [AGENTS.md repository (GitHub)](https://github.com/agentsmd/agents.md)
- [AGENTS.md example source file](https://raw.githubusercontent.com/agentsmd/agents.md/main/AGENTS.md)
- [KubeDojo CLAUDE.md](https://raw.githubusercontent.com/kube-dojo/kube-dojo.github.io/main/CLAUDE.md)
- [KubeDojo module-quality rules](https://raw.githubusercontent.com/kube-dojo/kube-dojo.github.io/main/.claude/rules/module-quality.md)
- [KubeDojo new-content checklist](https://raw.githubusercontent.com/kube-dojo/kube-dojo.github.io/main/.claude/rules/new-content-checklist.md)
- [Starlight sidebar architecture](https://starlight.astro.build/guides/sidebar/)
- [Starlight frontmatter reference](https://starlight.astro.build/reference/frontmatter/)
- [Astro routing guide](https://docs.astro.build/en/guides/routing/)
- [KubeDojo configuration file](https://raw.githubusercontent.com/kube-dojo/kube-dojo.github.io/main/astro.config.mjs)

## Repository Engineering Deepening Appendix

The previous sections gave you a practical map.
This appendix is the operational expansion.
We move from a descriptive understanding to an engineering implementation model you can apply to any repository that wants reliable agent behavior over time.

A strong repository contract always starts with a map, because map quality determines execution quality.
If you know where to go first, you can avoid random context reads and stop mixing temporary intent with durable policy.
Agents still need task memory, but the first step is always to distinguish what is permanently true from what is true only for this issue.
A repo that gets this distinction wrong does not fail because the model is wrong; it fails because the context system is wrong.

The same principle applies to every file.
One file should represent durable assumptions.
Another file should represent scoped practice.
A third file should represent temporary state.
When those files are mixed, the repo no longer has a contract surface and becomes a pile of reminders.

In enterprise settings, teams often call this “governance debt.”
In practical engineering, it is simply missing layered boundaries.
Boundaries are cheap to define and expensive to rebuild after repeated confusion.
Once a boundary is defined, each layer can be reviewed by a different team with different ownership, and that separation keeps both speed and control.

A disciplined pattern is to separate four planes: bootstrap, knowledge, feedback, and operations.
Bootstrap is where the agent knows the initial posture.
Knowledge is where design and conventions live.
Feedback is where state and outcomes are returned.
Operations is where tasks are executed and observed.
Those four planes are often documented in separate file families and linked in one compact route.
If you remove one plane, execution still happens but with more failures.
If you duplicate one plane, failures become harder to diagnose.

Bootstrap can be as short as 120 lines.
That is often enough to state startup commands, branch policy, and check order.
Longer bootstrap files might still work if they remain clean, but they usually drift quickly.
For this reason, bootstrap files should optimize for discoverability and determinism.
A good bootstrap file should answer two questions quickly: where do I start, and what must I verify.
If it does not answer those questions under 30 seconds, it is too long for repeated usage.

Knowledge surfaces should be modular, linked, and versioned.
A module should own one coherent topic, not one broad behavior.
If a topic grows into multiple responsibilities, split it early.
This is especially true when teams expand from manual to issue-driven agent workflows.
You need a place where architecture decisions, process decisions, and review expectations are each separate enough to evolve without breaking the others.
Cross-linking this structure matters.
If links break or become stale, your feedback quality drops because agents cannot trust navigation.

Feedback should be explicit and machine-consumable.
Human language is still useful, but machine checks let you detect divergence quickly.
A few concrete feedback signals are enough: active lease state, module pipeline state, review state, and health state.
Every signal should include severity.
If a warning indicates missing checks, it should not look like success.
If the repo enters a failing state, this state should be visible before the next write.
That principle is what separates robust agent systems from random automation.

Operations should record where tasks begin and where they finish.
A simple operational loop uses command traces, review logs, and outcome status files.
This loop does not require heavyweight tooling.
It requires consistency.
When every run outputs a short state block, maintainers can reason about failure patterns and agents can self-adjust.
The better the state signal, the less post-hoc triage is needed.

To make these planes practical, map each plane to owners and refresh policies.
Ownership should match team structure.
If a single person owns everything, latency rises and conflict increases.
If no one owns anything, drift is inevitable.
In both cases, the repo is effectively unmaintained.
A minimal policy is one owner, one review owner, and one escalation owner.
For small teams, these roles can be combined.
For larger teams, roles should be distinct.

A robust repository contract also needs explicit scope tags.
A scope tag is not just a folder.
It is a statement that says who edits what and why.
For example:
root instructions can define branch strategy.
Team folders can define review details.
Issue folders can define temporary constraints.
Runbooks can define operational defaults.
Scope tags keep teams from accidentally editing the wrong layer.

Another practical point is exception handling.
Instruction stacks break when exception policy is missing.
Without exception policy, every edge case becomes a permanent exception.
With exception policy, edge cases are bounded to explicit tasks and are eventually retired.
For every exception you add, define expected closure conditions.
If no one defines closure, the exception becomes permanent by default.
That is how stale rules appear in a few cycles.

The goal is not to eliminate all exceptions.
The goal is to ensure every exception has a life cycle.
A useful cycle has three stages:
intent, execution window, and retirement.
If retirement is never scheduled, the cycle is incomplete.
If execution windows remain open for too long, intent turns into noise.
A project with 10 clean cycles for every one broken cycle scales significantly better than one with no cycle model.

You can implement this directly in documentation style.
At each scoped file, add a short “lifecycle” block.
One block for when this file is authoritative.
One block for when it must be reviewed.
One block for when it will be retired or merged.
This is a low-cost addition with high operational payback.

A major failure mode is “task leakage.”
Task leakage happens when one-off issue details stay in bootstrap or rules.
The fix is simple and immediate.
Create a task-local section and keep it small.
Move issue context to the task issue or task log.
Do not let it replace stable contract.
When a task note is moved into permanent files, it usually returns as stale and harmful guidance.

Instruction drift is easier to control if you automate detection.
A few checks can catch drift before agents execute:

- missing links,
- expired references,
- moved files with stale anchors,
- and unknown required check names.

These checks do not solve human judgment.
They do solve mechanical rot.
Mechanical rot is the easier category to fix.
Human judgment should remain explicit and intentional.

When a repo starts acting like a learning system, teams should use feedback data to improve rules.
Do not wait for a major outage to rewrite instructions.
Use weekly or per-release review windows.
Collect one small signal at a time.
If a command is repeatedly bypassed, either the command is wrong or the contract is unclear.
If a signal is repeatedly ignored, add a concrete reason and fallback.
If a check cannot be interpreted quickly, shorten it and split it.

Now compare two approaches.
Approach A writes a single monolithic file with all rules, checklists, and examples.
Approach B uses bootstrap, scoped files, and machine checks.
Approach B almost always outperforms A for long-term agent operations.
Approach A requires the agent to parse more data than needed and cannot represent temporary state safely.
Approach B allows each layer to evolve without causing cross-layer ambiguity.
The difference is not just cleanliness.
The difference is operational resilience.

A compact example of this difference is the following progression.
A beginner might start with one instruction block.
At first this works.
As tasks multiply, contradictions appear.
At that point, the layer model adds explicit scopes.
If scoped layers are added without tests, the model still fails.
If scoped layers are added with checks, the model stabilizes.

For every new module, ask: does this rule belong in bootstrap, docs, or runtime state?
If uncertain, run a small decision test.
If a human must read the rule in every run, it is likely bootstrap.
If only one subdomain needs it, it is likely scoped docs.
If it only applies to one issue, it belongs to task context.
If it should trigger automatically, it belongs to runtime state.
When this decision test is followed consistently, instruction quality improves quickly.

Finally, think about onboarding.
A strong onboarding path is short, deterministic, and repetitive.
A weak onboarding path is broad and narrative heavy.
Agents work best with deterministic onboarding because it is easier to validate.
Humans also work better when they can point to one line and know what changed.
This is where this module’s practical goal meets real repo engineering: every decision should become discoverable, auditable, and executable.

You now have enough structure to inspect a repository and design a full contract.
If your audit reveals fewer than four high-signal files and no automated state signals, start there before adding more complexity.
If your audit reveals many rules but no ownership map, add owners before adding rules.
If your audit reveals stale rules, retire them before adding new ones.
If your contract remains confusing, split layers before expanding content.

By applying these practices, you move from “agent instructions are mostly prose” to “agent instructions are a layered operating system.”
That shift is the essence of repository engineering for agents.
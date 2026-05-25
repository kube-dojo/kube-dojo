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

By the end of this module, you will be able to:

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

Team-level AI workflows usually break in one of four recurring ways.

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

If you can prevent these four modes, you dramatically improve correctness, review quality, and merge predictability.

## What AGENTS.md and CLAUDE.md actually become in agent engineering

AGENTS.md and CLAUDE.md are not the system itself.
They are the repository front-door summary and route map.

In practical terms:

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
If every agent starts with your repository, this layer should include:

- one path to the main workflow contract,
- one path to safety and branch policy,
- one path to docs index,
- and one path to execution checks.

AGENTS.md and root CLAUDE.md are common L0 occupants.
But they should remain compact.
A compact L0 means 100-250 high-leverage lines, not a 3,000-line instruction book.

### L1: Repository-locally discoverable slices

L1 should include scoped rules and recurring playbooks.
In this layer:

- rules apply to common workflows,
- changes are infrequent,
- text should be stable across many tasks,
- examples should be durable and explicit.

This is where `.claude/rules`, architecture notes, and recurring task-runbooks usually live.

### L2: Role-specific and workflow-specific documents

L2 holds targeted instructions tied to roles, features, or recurring domains.
A few examples:

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

For L3, the repository becomes operational, not only descriptive.

## The bootstrap stack for this repository

KubeDojo’s own stack is intentionally explicit.
The root `CLAUDE.md` gives agent entry rules and workflow requirements.
The `scripts/cold-start.sh` script enforces issue-first onboarding and surfaces current project state.
`.claude/rules/` adds scoped conventions for review, module quality, module migration decisions, and translation constraints.

That means the root instructions are not just helpful prose.
They are a real first-run contract.
Agents are expected to consume this as the base layer.

A useful design rule for any repo is this:

- if a policy is required before any tool call, it belongs in bootstrap or always-on layer,
- if policy is only needed for one domain, keep it in scoped docs,
- if a requirement is temporary, keep it in the task layer.

## The docs-as-system-of-record model

A well-engineered repository treats `docs/` as the durable interface between humans and agents.
Humans maintain structure.
Agents consume structure.
When both sides align, the repo becomes easier to operate.

For this model to work, documentation has to meet three criteria:

1. **Stable authority**: statements should be true for the module until intentionally revised.
2. **Machine readability**: enough section headings, anchors, and predictable names for tooling and retrieval.
3. **Review pressure**: every change to docs should be reflected in checklists, PR templates, or state surfaces.

A practical pattern is to separate docs by intent.

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

Create or verify a short root file that answers:

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

Every quarter, read and prune:

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
For robust stacks:

- root CLAUDE.md: startup posture and cross-project conventions,
- nested CLAUDE.md: domain-specific context,
- references to `docs/` pages for durable design and policy,
- links to local endpoints for current state.

The important distinction:

- CLAUDE.md is memory bootstrap.
- AGENTS.md is often ecosystem-level bootstrap and agent-facing index.
- docs pages are durable records and behavior contracts.

You can use both without contradiction.
When they overlap, choose the closest applicable layer as source of truth for that concern.

## How a repository should “talk back”

A repository that teaches passively only lowers confidence.
A repository that teaches interactively improves agent behavior.
“Talking back” means the repo emits structured signals during and after each run.

For KubeDojo, three signal classes are especially useful.

### Structural signals

The API exposes module and lease state.
Before touching a module, check live state and active constraints.
This reduces duplicate work, conflicting edits, and stale assumptions.

Examples:

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

A minimal contract pattern:

1. Statement in instruction file.
2. Corresponding command in `scripts/*`.
3. Automated check with stable command name.
4. CI or local check gate.
5. Review path when check fails.

## Repository interface for agents: a design framework

Use this architecture lens when auditing a repository.

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

Your design objective is to maximize positive findings in all five columns.

## Four mandatory design questions

Before writing any instruction file, ask and answer:

1. What is always true for this repository?
2. What is usually true but subject to change?
3. What is temporary for this specific work?
4. What does the repo report after each run?

If you cannot answer these quickly, your instructions are too broad.

## The repository as a contract with multiple readers

Different readers extract different meaning from the same files.
Agents and humans need aligned grammar.

- **Humans** want rationale and narrative.
- **Agents** want stable extraction points.
- **CI** wants commandable invariants.
- **Reviewers** want auditability and deterministic checklists.

A single section can serve all if authored with this principle:

- first line states policy,
- second line states why,
- third line points to the command,
- fourth line points to a review artifact.

## Layered instruction pattern for real modules

A practical scaffold for module authoring:

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
Use targeted docs instead.

- PR-specific reviewer names,
- one-off issue details,
- temporary local branch naming experiments,
- unresolved design drafts.

If this content becomes frequent, move it into:

- task prompt,
- issue comments,
- per-module notes,
- temporary run logs.

## When CLAUDE.md should be split

A single CLAUDE.md becomes fragile when:

- it contains unrelated instructions for distinct domains,
- multiple teams modify it without ownership boundaries,
- nested directories conflict silently,
- and readers can no longer identify active scope.

In that case, split by subtree where edits are independent.
That split may mirror source structure, team boundaries, or subsystem ownership.

## Repository anti-fragility: stale-aware design

Every repository instruction system ages.
A strong pattern is a simple stale policy.

### Staleness policy sample

For every instruction file:

- define an owner,
- define expected review cadence,
- define a deprecation note,
- define migration target.

If a file fails cadence twice in a row, move it into task-local scope or delete it.

A stale-file score can be calculated manually.

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

A repository that can be used by agents should expose four primary documents:

1. Orientation document.
2. Standards and review document.
3. State and health document.
4. Escalation and override document.

### Orientation document

This is the first file an agent should always be able to resolve.
In KubeDojo, root `CLAUDE.md` and scripts entrypoints serve this role.

### Standards and review document

This is where long-lived behavior rules live.
For example:

- issue-first workflow,
- branch expectations,
- PR conventions.

### State and health document

This is where current conditions are exposed.
For example:

- module-level pipeline state,
- quality state,
- active blockers,
- local API warnings.

### Escalation and override document

This is where conflict resolution is described:

- which guidance wins at conflict,
- what manual checks are mandatory,
- where to report and close contradictions.

## Example architecture: how to teach an agent what to ignore

Agents do poorly when asked to reason over generated files, vendor directories, and throwaway outputs without explicit exclusions.
Include explicit exclusions in bootstrap and in task checklists.

Examples of exclusions:

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
A few patterns:

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
A practical authoring cycle:

1. Start from the issue.
2. Draft the contract surfaces.
3. Add links and exclusions.
4. Add verification commands.
5. Add feedback surfaces.
6. Run checks.
7. Update index.

Each step should include owner and next state.

## The minimal contract set for a healthy repo

An effective minimum set in this model has seven files/components.

- `AGENTS.md` or equivalent.
- `CLAUDE.md` or equivalent.
- `scripts/cold-start` equivalent.
- one `local` API or script to query current run context.
- one module checklist for review.
- one quality entrypoint check.
- one health check.

If a repository lacks at least one component, the repo is not currently “agent-friendly.”

## Worked example: repository design walkthrough

Below is a worked walkthrough for a hypothetical repository.

### Step A: Start from breakage

The repo often fails because agents miss branch constraints and run commands in the wrong order.

### Step B: Choose L0 files

The team adds a compact root AGENTS-like file listing required preflight checks and links.

### Step C: Add memory links

A root CLAUDE.md entry points to scoped rule files for API, docs, and deployments.

### Step D: Build docs map

`docs/` contains a “for AGENTS and agents” subsection with:

- system map,
- review invariants,
- check ordering,
- and common operational gotchas.

### Step E: Add talkback endpoints

A local API endpoint now exposes:

- active module,
- required checks,
- quality score,
- and blocker status.

### Step F: Introduce stale checks

A periodic checklist now asks owners to trim outdated instructions every 30 days.

### Step G: Validate

Now each agent run follows the same route.
Context quality improves, and the same task is less sensitive to chat window age.

## Layer-by-layer design rubric

You can evaluate your repository design with this matrix.

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
Large repos need more shape.

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

A mature repository has at least these artifacts:

1. **Navigation card**: where to start.
2. **Execution card**: what to run and when.
3. **Risk card**: what not to do.
4. **Recovery card**: where to check failures and how to restart.
5. **Closure card**: what constitutes a successful run.

Each card can live in docs or in command output, but links should exist from bootstrap files.

## Avoiding instruction debt

Instruction debt accumulates in three ways.

- one-time task assumptions copied into baseline rules,
- outdated historical incident notes left in bootstrap,
- duplicate instruction copies in multiple files.

When debt is high, agents do not get confused because they cannot parse ambiguity.
They act on ambiguity.

To prevent debt, require ownership tags.
For example:

- Owner: module maintainer,
- Reviewer: quality reviewer,
- Expiry review date,
- Migration note.

## Repository engineering as a social contract

This is technical and social.
Agents are not replaced by this process.
Humans still decide architecture, ownership, and quality.
The engineering work is to let humans make those decisions once and let agents execute repeatedly.

A repo that talks back to an agent creates better collaboration because:

- humans spend less time repeating context,
- agents spend less time rediscovering policy,
- and failures are easier to diagnose.

## The design exercise: map this repo to four layers

Try this for your own repository.
For each layer, fill one sentence.

- **Layer 0**: what file always loads and why.
- **Layer 1**: what file scopes by folder and who owns it.
- **Layer 2**: where role-specific behavior and tool choices live.
- **Layer 3**: where current-run state and telemetry are published.

Then add at least one check command per layer.

## Did You Know

- Repositories that survive long AI-first programs keep boot instructions short and keep deep context in linked `docs/`.
- The most stable failure signals come from scripts and APIs, not from prose that is not tied to checks.
- Progressive disclosure is usually more reliable than comprehensiveness because it reduces context collisions between tools and teams.
- A reusable agent repository surface uses nested files, explicit links, and explicit state endpoints at every scale.

## Common repository mistakes and anti-patterns

The following table is diagnostic. Use it while auditing your own files.

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

This module focuses on a practical design bundle:

- a compact repository-level map,
- a scoped memory hierarchy,
- structured `docs/` records,
- and operational feedback endpoints.

For learning, this means the minimum implementation is:

- one root bootstrap file,
- one hierarchical memory file,
- one set of structured docs,
- one quality check,
- one health check,
- and one escalation route.

## Design patterns for AGENTS-like files

Use the following layout pattern.

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

Do not include:

- ephemeral one-off issue details,
- deep technical history,
- and long unowned troubleshooting transcripts.

## Checklist design for maintainers

A concise maintainability checklist for repository engineering:

1. Is the entrypoint short enough to read quickly?
2. Are command paths explicit and deterministic?
3. Are temporary notes scoped to tasks?
4. Are generated directories explicitly excluded?
5. Is there a “next step after failure” route?
6. Is the docs index discoverable from bootstrap files?
7. Are layered files mutually consistent?

If any answer is no, file triage is required.

## How to design this for a real team in one week

Week 1:

- Day 1: inventory existing rules and duplicates.
- Day 2: define map-only root AGENTS/CLAUDE.
- Day 3: move stable facts into docs structure.
- Day 4: split nested scoped instructions.
- Day 5: expose state and health commands.
- Day 6: add missing review surfaces.
- Day 7: run checks and collect first failure pattern.

Week 2 and beyond:

- add stale checks,
- add ownership metadata,
- add automated reminder to remove stale sections.

## Knowledge as reusable modules

A repository designed for agents should support both quick start and deep dives.
A quick start path gives short-term speed.
A deep-dive path gives long-term correctness.

Quick-start path:

- run cold-start,
- review state,
- open module index,
- run module checks.

Deep-dive path:

- inspect review history,
- inspect instruction deltas,
- inspect pipeline status,
- and trace failure sequences across runs.

## The “if not represented, enforce” rule

If an expectation affects behavior, and the repo cannot represent it in a file or command, the expectation is probably not enforceable.
Enforceability is what turns human preferences into machine trust.

A non-enforced expectation is still useful context but not operational truth.

## Designing for portability across model families

Different models and frameworks load context differently.
You can reduce variance by using:

- concise L0 instructions,
- stable file names,
- low churn for bootstrap,
- deterministic check commands,
- and explicit state surfaces.

This matters in mixed-model workflows and in multi-tool review loops.

## How to express model-agnostic contracts

Do not write instructions as one tool’s command syntax.
Write them as behavior expectations and expected states.
For tool specifics, provide per-tool examples as examples, not as only definitions.

For example:

- “Do not run commands that mutate hidden state without a rollback plan.”
- then optionally:
  - “For Git, use standard commands in review mode.”
  - “For local APIs, use explicit endpoints.”

The behavioral contract stays model-agnostic.

## Operationally safe defaults

The safest defaults for repository engineering are conservative.
If uncertain, prefer explicitness over coverage.

- explicit exclusions,
- explicit scopes,
- explicit update paths,
- and explicit failure messages.

## Practical lab: design a two-layer bootstrap for this module

1. Create `repo-contract.md` in your repository root with an explicit L0/L1/L2/L3 map.

```md
# Repository Run Contract

- L0: `AGENTS.md`
- L1: `docs/` (navigation and long-form architecture notes)
- L2: `.claude/rules/` (scoped run constraints)
- L3: `module-2.2-repository-engineering-for-agents.md` (current task-local context)
```

2. Add `scripts/print-run-contract.sh` with the following script:

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_CONTRACT="${ROOT_DIR}/repo-contract.md"

CHECK_PATHS=(
  "AGENTS.md"
  "docs/"
  ".claude/rules/"
  "src/content/docs/ai/ai-engineering-foundations/module-2.2-repository-engineering-for-agents.md"
)

echo "L0 paths:"
grep -E '^-[[:space:]]*L0:' "${REPO_CONTRACT}" | sed 's/^- [Ll]0:/  -/'
echo

echo "L1 paths:"
grep -E '^-[[:space:]]*L1:' "${REPO_CONTRACT}" | sed 's/^- [Ll]1:/  -/'
echo

echo "L2 paths:"
grep -E '^-[[:space:]]*L2:' "${REPO_CONTRACT}" | sed 's/^- [Ll]2:/  -/'
echo

echo "L3 paths:"
grep -E '^-[[:space:]]*L3:' "${REPO_CONTRACT}" | sed 's/^- [Ll]3:/  -/'
echo

for candidate in "${CHECK_PATHS[@]}"; do
  if [[ -e "${ROOT_DIR}/${candidate}" ]]; then
    echo "OK EXISTS ${candidate}"
  else
    echo "MISSING ${candidate}" >&2
    exit 1
  fi
done
echo "All contract paths are present."
```

3. Define one stale-rule check:

- A path listed under L0/L1/L2/L3 is considered stale if it is missing from disk at the start of a new run.
- Add that rule to your root contract workflow:
  - `scripts/print-run-contract.sh` must run before any task-write step.
  - If it exits non-zero, stop the workflow and fix references before continuing.

4. Verify with these expected results:

- Success output: `L0 paths:`, `L1 paths:`, `L2 paths:`, `L3 paths:` plus all `OK EXISTS` lines and final `All contract paths are present.`
- Failure output: at least one `MISSING <path>` line, non-zero exit code, and task paused until contract files are corrected.

5. Add one back-link in the module:

- Add one sentence in `## Sources` saying this module’s contract lives in `repo-contract.md`, so the check script has a stable target and failure path.

## Design challenge: avoiding false safety in instructions

A false-safe instruction is one that looks strict but does not stop bad outcomes.
That happens when:

- constraints reference files that no longer exist,
- examples show only happy path,
- and checks are not wired.

Use this audit phrase while reviewing any instruction layer:

“Can this rule be violated without failing a check?”

If yes, it is informative but not enforceable.

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

Next module: [Semantic vs Lexical Context](module-2.3-semantic-vs-lexical-context/)

## Sources

- [Harness engineering (OpenAI)](https://openai.com/index/harness-engineering/)
- [Give Claude context with CLAUDE.md (Anthropic Support)](https://support.claude.com/en/articles/14553240-give-claude-context-claude-md-and-better-prompts)
- [Claude Code memory model (Anthropic docs)](https://docs.anthropic.com/en/docs/claude-code/memory)
- [Custom instructions with AGENTS.md — Codex (OpenAI Developers)](https://developers.openai.com/codex/guides/agents-md)
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
- The lab script in this module points to `repo-contract.md` as the root contract file.

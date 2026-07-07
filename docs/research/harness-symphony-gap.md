# Harness Engineering + Symphony — Curriculum gap + Self-application

Captured 2026-05-12. Source: user-pasted summary of OpenAI's Feb 2026 "Harness
Engineering" post (Ryan Lopopolo) and the Apr 2026 Symphony follow-up
(Kotliarskyi, Zhu, Brock + open-source SPEC.md). Goal: durable capture for
two distinct workstreams — a curriculum module to write, and a meta-initiative
to apply the principles to KubeDojo's own codebase.

---

## A. Source summary (verbatim, for module brief)

### Harness engineering (Feb 2026)

**Author**: Ryan Lopopolo (OpenAI). **Setting**: 5-month internal experiment —
real internal product shipped with zero manually-written lines of code. Codex
wrote everything: app logic, tests, CI, docs, internal tooling, AGENTS.md.

> "Humans steer. Agents execute."

**Definition**: When the team's job is no longer to write code, the new job is
"to design environments, specify intent, and build feedback loops that allow
Codex agents to do reliable work." The harness is the scaffolding — tools,
abstractions, in-repo knowledge, mechanical guardrails — that lets agents
succeed on tasks no single prompt could specify.

**Layered framing**:

| Term | Optimizes |
|---|---|
| Prompt engineering | A single interaction |
| Context engineering | What the agent sees on this turn |
| Harness engineering | The whole environment — code structure, mechanical lints, app legibility, doc layout, merge norms |

**Seven principles**:

1. **The map, not the manual.** One big AGENTS.md fails. "Context is a scarce
   resource… Too much guidance becomes non-guidance… It rots instantly… It's
   hard to verify." Fix: AGENTS.md ~100 lines as table of contents, with
   structured `docs/` directory as system of record (design-docs, exec-plans,
   references/, generated/, ARCHITECTURE.md, QUALITY_SCORE.md). Progressive
   disclosure: agents start with a small, stable entry point and are taught
   where to look next.
2. **Repository as the only system of record.** "From the agent's point of
   view, anything it can't access in-context while running effectively doesn't
   exist." Slack, Google Docs, people's heads — invisible. Push everything
   into versioned in-repo artifacts.
3. **Enforce invariants, not implementations.** "With agents, strict rules
   become multipliers: once encoded, they apply everywhere at once."
   Mechanically enforce architectural layer dependencies, structured logging,
   file size, naming. Error messages from these lints inject remediation
   instructions into agent context. They didn't dictate "use Zod" — they
   required boundary parsing and let the agent pick Zod itself.
4. **Make the application legible to the agent.** Worktree-bootable app,
   Chrome DevTools Protocol wired into agent runtime, ephemeral per-worktree
   observability stack, LogQL/PromQL queryable. Prompts like "ensure service
   startup completes in under 800ms" become tractable.
5. **Flip the merge philosophy.** "In a system where agent throughput far
   exceeds human attention, corrections are cheap, and waiting is expensive."
   Minimal blocking gates, test flakes addressed with re-runs not blocks.
6. **Continuous garbage collection.** Used to burn 20% of each week
   (Fridays) cleaning up "AI slop." Replaced with golden principles + a
   "recurring 'doc-gardening' agent that scans for stale or obsolete
   documentation and opens fix-up pull requests." Most refactor PRs auto-merge
   in under a minute. "Technical debt is like a high-interest loan: almost
   always better to pay it down continuously."
7. **Boring tech wins.** "Technologies often described as 'boring' tend to be
   easier for agents to model due to composability, API stability, and
   representation in the training set." Sometimes cheaper to re-implement a
   utility than work around opaque upstream behavior.

**Numbers**: ~1M LOC in 5 months. ~1,500 PRs merged. 3 → 7 engineers.
3.5 PRs/engineer/day average — throughput **increased** with team growth.
Single Codex runs sometimes work 6+ hours on one task (often overnight).

**Autonomy ladder crossed** (one prompt): validate state → reproduce bug →
record video of failure → implement fix → drive app to validate → record
video of resolution → open PR → respond to feedback → detect+remediate build
failures → escalate only on judgment → merge.

> "This behavior depends heavily on the specific structure and tooling of this
> repository and should not be assumed to generalize without similar
> investment."

---

### Symphony (Apr 2026)

**Authors**: Kotliarskyi, Zhu, Brock. Direct follow-up to harness engineering.
After agents became fast, the next bottleneck was human attention: context
switching for the humans steering them.

> "We realized we were optimizing the wrong thing. We were orienting our
> system around coding sessions instead of the work itself."

**Pivot**: Stop tracking work via agent sessions. Track via project-management
state. Result: Symphony — an agent orchestrator that turns a project-management
board like Linear into a control plane for agentic work.

**Effect claimed**: 500% increase in landed PRs on streams that used it. PMs
and designers can file feature requests that agents complete end-to-end
without engineering intermediaries.

**Shape**: Symphony itself is small. SPEC.md + reference implementation.

> "When you open the Symphony repository, the first thing you'll notice is
> that Symphony is technically just a SPEC.md file."

Symphony is:
- A scheduler/runner + a tracker reader. Not a workflow engine, not a CI
  replacement.
- A polling loop on Linear (active states: Todo, In Progress, Rework, Merging)
- Per-issue isolated workspace (sanitized identifier → directory)
- Spawns Codex in App Server mode inside that workspace
- Streams updates back, tracks tokens, detects stalls, retries with
  exponential backoff
- Stops + cleans when ticket moves to terminal state (Done, Closed, Cancelled,
  Duplicate)

**The agent does ticket writes, not Symphony.** State transitions, comments,
PR links — all done by the coding agent using tools available in its runtime.

**In-repo contract**: single `WORKFLOW.md`. YAML front-matter + Liquid prompt
body. Versioned with the code. Hot-reloads on change. Six top-level keys:
tracker, polling, workspace, hooks, agent, codex.

Example front-matter (elixir reference):

```yaml
tracker:
  kind: linear
  project_slug: "..."
  active_states: [Todo, In Progress, Merging, Rework]
hooks:
  after_create: |
    git clone --depth 1 https://github.com/openai/symphony .
agent:
  max_concurrent_agents: 10
  max_turns: 20
codex:
  command: codex --config 'model="gpt-5.5"' app-server
  approval_policy: never
  thread_sandbox: workspace-write
```

Prompt body uses Liquid with `{{ issue.identifier }}`, `{{ issue.title }}`,
`{% if attempt %}…continuation guidance…{% endif %}`. Unknown variables fail
rendering (strict). Hot-reload is a hard requirement.

**Lifecycle hooks** (portable idea):
- `after_create` — runs once when workspace dir is born. Failure aborts.
  Typical: `git clone ... .` + dependency fetch.
- `before_run` — pre-flight before each agent attempt. Failure aborts attempt.
- `after_run` — post-attempt, success or failure. Logged-only on failure.
- `before_remove` — cleanup before workspace deletion. Logged-only on failure.

**State machine** (orthogonal to ticket state):

- Internal claim states: `Unclaimed → Claimed → {Running | RetryQueued} → Released`
- Run-attempt phases: `PreparingWorkspace → BuildingPrompt → LaunchingAgentProcess → InitializingSession → StreamingTurn → Finishing → {Succeeded | Failed | TimedOut | Stalled | CanceledByReconciliation}`

A single worker can run multiple back-to-back Codex turns on one issue if it's
still active (capped by `agent.max_turns`, default 20). First turn = full
rendered prompt; continuation turns send only continuation guidance to the
same thread.

**The most important late lesson**:

> "Treating agents as rigid nodes in a state machine doesn't work well. Models
> get smarter… So we eventually moved toward giving agents objectives instead
> of strict transitions, much like a good manager would assign a goal to a
> direct report."

**This is the same shift KubeDojo's `docs/archive/2026-07-goal-driven-runs.md` (formerly `.claude/rules/goal-driven-runs.md`; PR
#1082) encoded for `/goal`. Independent convergence — Symphony reached this
conclusion from the orchestration side, we reached it from the rule side.**

**Their `WORKFLOW.md` body**: ~200-line markdown defining status routing
(Backlog → ignore, Todo → move to In Progress + create workpad, In Progress →
continue, Human Review → wait, Merging → run land skill, Rework → full reset),
a mandatory single persistent workpad comment per ticket (## Codex Workpad
with Plan / Acceptance Criteria / Validation / Notes / Confusions), a PR
feedback sweep protocol, blocked-access escape hatch rules, and a completion
bar before Human Review. "Read like a senior engineer's onboarding doc — in
the same way you would onboard a new teammate."

---

## B. Curriculum slot — where this goes in KubeDojo's AI track

Best fit: `src/content/docs/ai/ai-native-work/` (already has modules 1.1–1.4
on AI tool use, agents, workflow design, human-in-the-loop habits).

Recommended module(s):

- **Module 2.1 — Harness engineering: designing environments agents can
  succeed in.** Covers the seven principles, the autonomy ladder, the
  AGENTS.md ToC pattern, mechanical-invariant lints, app legibility, merge
  philosophy, doc-gardening agents, boring-tech bias.
- **Module 2.2 — Orchestrating fleets: Symphony and project-management-as-
  control-plane.** Covers the pivot from sessions-as-unit to issues-as-unit,
  WORKFLOW.md contract shape, lifecycle hooks, the state machine, the late
  shift to objective-driven agents, KubeDojo's `/goal` convergence.

These modules should be written using `scripts/prompts/module-writer.md` and
reviewed cross-family per `docs/review-protocol.md`. Do NOT include in
tonight's #388 lift batch — that's existing-module density work, not new
content. Write these as fresh modules in a follow-up dispatch.

### Core teaching point: the layered-harness mental model

The most important thing Module 2.1 should teach is NOT the seven principles
or the Symphony state machine — it's the mental model that makes those
principles actionable for any reader on any platform.

**Every agent harness has three layers:**

1. **Platform defaults** — what the AI tool / coding agent / CLI gives you
   by default. Hardcoded behaviors, system-prompt rules, default tool wiring.
   Examples: Claude Code's "Edit is the editing tool", Codex's `AGENTS.md`
   convention, Cursor's `.cursorrules`. You can't change these without
   changing platforms.
2. **Project advisory** — what your repo's docs say. `CLAUDE.md`, `AGENTS.md`,
   `.claude/rules/`, memory files, README sections aimed at agents. Read by
   the agent; honored when it doesn't conflict with platform defaults. When
   it does conflict, the platform layer wins.
3. **Project enforcement** — what your repo can mechanically force regardless
   of the platform layer. For Claude Code: `.claude/settings.json` hooks +
   permission denies. For Codex: pre-commit hooks, CI gates, sandbox
   wrappers. **The only layer where your project rules override platform
   defaults.**

The harness-engineering discipline is **"push every rule down to the lowest
enforceable layer."** A rule in advisory text that the agent ignores half
the time is not a rule, it's a wishlist. The same rule encoded as a hook
that exits non-zero when violated is enforcement.

Concrete worked example — the same rule at each layer:

| Layer | "Don't direct-commit to main" |
|---|---|
| Platform default | Nothing — `git commit` is allowed |
| Project advisory | `feedback_no_direct_push_to_main.md`, `CLAUDE.md` rule |
| Project enforcement | `pre-tool-use` hook in `.claude/settings.json` blocking `git commit` when branch == `main` with no PR ref |

The advisory version gets violated. The enforcement version cannot be
violated. That difference is the discipline. This lesson generalizes across
every agent platform — it's the most reusable thing the module teaches.

**What this module should NOT do**: hold KubeDojo up as a model of strong
enforcement. As of 2026-05-12, KubeDojo's harness is mostly project-advisory,
with limited mechanical enforcement (sandbox modes, density verifier,
citation gate). The friction this creates is documented in this repo's
feedback memory files — useful candor signal, but not a success case study.
External success stories (OpenAI's Codex internal team, Symphony) carry the
positive worked-example role. KubeDojo's friction can appear as one short
anti-example for principle #3 (Enforce invariants, not implementations).
That's it.

---

## C. How this maps to KubeDojo (parallel analysis from learn-ukrainian)

We have already been doing harness engineering. Quite a lot of it. The OpenAI
posts give us vocabulary + reference architecture for things we evolved by
trial and error. Concrete tool-by-tool map:

| Their pattern | What KubeDojo has today |
|---|---|
| AGENTS.md as table of contents (~100 lines) | `CLAUDE.md` + `~/.claude/projects/-…-kubedojo/memory/MEMORY.md` (just hit 25.2KB / 24.4KB limit) + `.claude/rules/` scoped rules + API-served `/api/briefing/session` |
| Structured `docs/` system of record | `docs/session-state/` (per-session handoffs, HTML-first), `docs/decisions/{pending,active}`, `docs/bug-autopsies/INDEX.md`, `docs/review-protocol.md`, `docs/pedagogical-framework.md`, `docs/quality-rubric.md` |
| Mechanical enforcement / custom lints | Verifier density gates (`median_wpp≥28 / mean_wpp≥30 / short-para-rate≤20%`), `dispatch_smart.py` task-class clamps (`feedback_batch_worker_cap.md` hard cap 3), `verify_review.py` quote-line verification, ruff + tsc + eslint pre-commit, `check_site_health.py` |
| Agent-legible application surfaces | Local API at `:8768` (`/api/briefing/session`, `/api/tracks/readiness`, `/api/quality/scores`, `/api/pipeline/leases`, `/api/module/{key}/state`, `/api/reviews`, `/api/activity`), quality-board HTML at `/quality-board`, `mcp__rag__*` for Ukrainian linguistic verification |
| Per-worktree isolated runs | `agent_runtime/runner.invoke` worktree-mandatory dispatch pattern; `feedback_codex_workspace_write_default.md` + `feedback_codex_danger_for_git_gh.md` enforce isolation defaults |
| Bug autopsies / continuous GC | `docs/bug-autopsies/INDEX.md`, MEMORY trim cadence (just triggered), STATUS.md index-only pattern (was 1623-line log) |
| Repo as only state | Briefing API parses STATUS.md `## TODO` + `## Blockers`; decisions in `docs/decisions/`; agent comms in `.bridge/messages.db` served by API |
| Multi-agent feedback loops | `scripts/ab discuss` channels with `[AGREE]/[OPTION X]/[DEFER]` convention; cross-family review per `docs/review-protocol.md` (Codex→Claude, Claude→Codex/Gemini, Gemini→Claude/Codex) |
| Two-tier handoffs | `docs/session-state/YYYY-MM-DD-*.{md,html}` narrative + STATUS.md index pointer; HTML-first artifact policy per `docs/migrations/html-first/plan.html` |
| Objectives over rigid state transitions | `docs/archive/2026-07-goal-driven-runs.md` (formerly `.claude/rules/`; PR #1082, archived 2026-07-07 as dormant) — independent convergence with Symphony's late lesson, reached 2026-05-12 |

### Where KubeDojo materially differs from Symphony

Symphony's orchestrator is **Linear → agent**. PM files a ticket, system picks
it up, agent does it end-to-end, no human in between. Loop is
autonomous-continuous.

KubeDojo's orchestrator is **Claude (me) + local API + manual dispatch**. Loop
is event-driven with a human (and orchestrator-Claude) in the steering chair
on every dispatch decision. That's deliberate — worth naming the choice.

### The critical caveat — why we can't naively port their model

Symphony's entire system is built around the assumption that **bad output is
cheap**: a flaky test gets re-run, a bad PR gets reverted, a stale doc gets
garbage-collected by the next gardening run. The 500% PR throughput claim
depends on a regime where shipping speculative tries is approximately free.

**KubeDojo is education.** Module content is the opposite regime: bad
pedagogy trains bad habits into real learners' foundation, and you cannot
silently roll back what a learner has internalized. The standing brief:
**5 excellent modules beat 55 mediocre ones** (matches the `5 excellent beats
55 mediocre` principle from learn-ukrainian and the
`feedback_teaching_not_listicles.md` rule here).

So:
- **Harness engineering principles map cleanly** to KubeDojo's `scripts/`,
  infrastructure, CI, dispatch routing, briefing API. Keep building this.
- **Symphony's autonomous-dispatch pattern maps cleanly** to a narrow band of
  mechanical work: lint hygiene PRs, dependency bumps, doc-gardening,
  bug-autopsy backfills, MEMORY trims, STATUS.md compaction, phantom-service
  cleanups, stale-pid sweeps. Cheap-to-rollback infrastructure work.
- **Neither maps to module content production.** The bottleneck there is
  judgment + technical accuracy + pedagogical review — none of which
  parallelize the way Symphony assumes. The current cross-family-review +
  density-verifier + rubric-board gate stack already enforces this; do not
  weaken it for throughput.

### What's adoptable, in priority order

1. **Adopt the vocabulary.** "Harness engineering" is more precise than
   "agent orchestration scaffolding." Drop it into `CLAUDE.md` Agent
   Orientation section or a new `docs/best-practices/harness-engineering.md`
   so future agents can name what we're doing. Low risk, high clarity.
2. **`WORKFLOW.md`-style single-file workflow contract per pipeline phase.**
   We currently spread `#388` config across `scripts/quality/dispatch_388_pilot.py`,
   `scripts/quality/run_388_batch.py`, `scripts/prompts/module-rewriter-388.md`,
   `scripts/prompts/module-writer.md`, `.claude/rules/`. A `WORKFLOW.md` per
   phase with YAML front-matter (tracker / agent / codex) + Liquid-templated
   prompt body would put the contract in one place. Low risk, high clarity.
3. **Lifecycle hooks** (`after_create`, `before_run`, `after_run`,
   `before_remove`) on `agent_runtime/runner.invoke` for dispatched
   worktrees. We currently re-create worktree setup in every dispatch brief —
   centralizing removes a class of inconsistency bugs (the
   `feedback_codex_danger_for_git_gh.md` pattern, e.g.).
4. **Doc-gardening agent** for STATUS.md / MEMORY.md / session-state /
   `.claude/rules/` staleness. Scheduled `/loop` that scans last-modified vs
   last-referenced, opens fix-up PRs. MEMORY.md just hit its index size
   limit — this is overdue.
5. **GH issue → autonomous Codex dispatch** for a narrow class of work,
   gated by label `agent:codex-autonomous`. Specifically: lint hygiene,
   dependency bumps, doc-gardening, autopsy backfills, MEMORY trims, phantom
   service cleanups (like tonight's local_api.py:106 fix), stale-pid sweeps.
   **Explicitly NOT for module content.**

### What's NOT adoptable

- Auto-merge on module-content PRs without cross-family review. Education
  regime defeats Symphony's bad-output-is-cheap assumption.
- Single-agent end-to-end without human review for any content touching
  `src/content/docs/`. The cross-family-review rule stays.
- Symphony-style "ticket → agent → done" autonomy for anything pedagogical.
  Even the #388 pilot keeps Gemini review + density verifier in the loop.

### Suggested next-steps (post-overnight-batch)

1. Read Symphony SPEC.md end-to-end once (~2,200 lines, RFC-2119, well
   structured). Cleanest reference architecture in this space right now.
2. `ab discuss` channel: **"narrow autonomous-dispatch label"** — should
   `agent:codex-autonomous` be a labeled-issue convention that means
   something? Decide deliberately, not by drift.
3. Open the priority-1 issue: add "harness engineering" vocabulary to
   `CLAUDE.md` Agent Orientation.

---

## D. Status

- **Curriculum (B)**: Not in tonight's #388 batch scope. Open issue post-batch
  for module-writer dispatch.
- **Self-application (C)**: Multi-week initiative. `ab discuss` first to
  agree on priority order before opening sub-issues.

This file is the durable record. STATUS.md has a pointer in `## TODO`.

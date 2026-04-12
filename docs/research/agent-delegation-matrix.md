---
title: Agent Delegation Matrix
date: 2026-04-12
status: living document
related:
  - fact-grounding-calibration-2026-04-12.md
  - writer-calibration-2026-04-12.md (preliminary)
  - writer-calibration-RIGOROUS-2026-04-12.md (pending — being generated)
---

# Agent Delegation Matrix

This document defines which AI agent gets which kind of task in the KubeDojo
multi-agent setup. It is the practical answer to the question
*"who should do this?"* — informed by capability inventory + empirical
calibration data.

## Capability inventory (2026-04-12)

Tested via CLI flag inspection on the actual installed binaries.

| Capability | Claude (main session) | Codex (`codex exec`) | Gemini (`gemini --review`) |
|---|---|---|---|
| **Read local files** | Direct via Read tool | Direct in `workspace-write` sandbox | Via stdin only (no file traversal) |
| **Edit local files** | Direct via Edit/Write | Direct in `workspace-write` sandbox | NO — output is just stdout |
| **Run shell commands** | Direct via Bash | Direct in sandbox modes | NO |
| **Git operations** (commit, push, branch) | Direct | Direct in sandbox | NO |
| **Web search** | WebFetch + native | Built-in | Built-in (`--review` mode) |
| **Image input** (screenshots, diagrams) | YES — Read tool on .png/.jpg | YES — `-i, --image <FILE>...` flag | NO — text only |
| **UI debugging via Chrome** | YES — `mcp__claude-in-chrome` | NO | NO |
| **Multi-file refactor** | Direct | YES in sandbox | NO (one file at a time via stdin) |
| **Iterative test loop** (write code → run test → fix → repeat) | Direct via Bash | YES in sandbox — designed for this | NO (one-shot only) |
| **Long context** | 1M (Opus 4.6 1M variant) | gpt-5.4 frontier-tier (large) | Pro = 1M+, Flash = lower |
| **Streaming output** | N/A in main session | YES | YES |
| **MCP tools** | Many available | A few codex-specific | Some via `--mcp` flag |
| **JSON output schema enforcement** | Via prompt + validation | YES — `--output-schema` flag | Via prompt only |
| **Output to file** | Direct | YES — `--output-last-message` flag | Via shell redirect |

### Capabilities only Claude has

- UI debugging via Chrome extension (`mcp__claude-in-chrome`)
- Direct integration with the user's main session and conversation memory
- Native handling of complex multi-modal context (images mixed with code)
- Persistent session state across many operations

### Capabilities only Codex has

- `--output-schema` flag for forcing JSON shape compliance at the API level
  (no prompt engineering needed)
- `--image` flag accepting multiple files at once
- `gpt-5.3-codex-spark` and other Codex-tuned variants specialized for
  narrow tasks
- 10x usage tier through 2026-05-17 (highest current quota envelope)

### Capabilities only Gemini has

- Built-in `--review` mode that prepends KubeDojo review context
- MCP RAG integration for Ukrainian translations (`learn-ukrainian` server)
- Cheapest at the production-quality writer tier (until 2026-05-05)

## Calibration findings (relevant to delegation)

From `fact-grounding-calibration-2026-04-12.md`:

- **`gpt-5.3-codex-spark`** — best fact-grounder. 25/25 perfect on the proven
  flap zone. Self-consistency confirmed. Cheapest Codex tier.
- **`claude-sonnet-4-6`** — best cross-family fact-grounding fallback. 23/25.
  Use when Codex is rate-limited.
- **`gpt-5.4`, `gemini-3.1-pro-preview`, `claude-haiku-4-5`, `gemini-3-flash-preview`**
  — DISQUALIFIED for fact-grounding. All confidence-error on contradictory sources.

From `writer-calibration-2026-04-12.md` (PRELIMINARY — see rigorous re-test):

- All 5 tested writers (Gemini Pro, gpt-5.2, gpt-5.3-codex, Sonnet, Opus)
  scored 17-18/18 on a single PSA section. **No clear winner.**
- The preliminary scoring did NOT include hallucination fact-checking and is
  being re-run with `gpt-5.3-codex-spark` as the verifier.

## Delegation matrix

This matrix names the FIRST CHOICE agent per task. Fallbacks are noted in
brackets where relevant. The principles below the matrix explain why.

### Pipeline / content tasks

| Task | First choice | Fallback | Why |
|---|---|---|---|
| Initial module draft (full module, 4-8K words) | `gemini-3.1-pro-preview` | `claude-sonnet-4-6` | Production writer of record. Quality-tied with alternatives but cheapest at the level. Pre-May-5 Gemini quota is plentiful. |
| Targeted fix on rejected module section | `claude-sonnet-4-6` | `gpt-5.3-codex` | Sonnet is the existing `write_targeted` model. Strong instruction-following. PR #221/222 deterministic-apply path is built around this. |
| Fact-grounding pass (verify factual claims) | `gpt-5.3-codex-spark` | `claude-sonnet-4-6` | Calibration winner. Cheapest Codex tier. Honest about source contradictions. |
| Structural review (LAB/COV/QUIZ/EXAM/DEPTH/WHY/PRES) | `gemini-3.1-pro-preview` | `claude-sonnet-4-6` | After the architecture redesign in `feat/fact-ledger-architecture`. Stable, consistent rubric judgment. Self-review is acceptable for structural axes (not factual). |
| Knowledge card generation | `gpt-5.3-codex-spark` | `claude-sonnet-4-6` | Same role as fact-grounding — pin authoritative facts before writing. |
| Ukrainian translation | `gemini-3.1-pro-preview` (Pro model via uk_sync) | `gpt-5.4` | Gemini's strongest specific role. MCP integration with learn-ukrainian RAG. |

### Code / pipeline-engineering tasks

| Task | First choice | Fallback | Why |
|---|---|---|---|
| Greenfield function implementation (new feature from a clear spec) | `gpt-5.3-codex` (via `codex exec --sandbox workspace-write`) | `gpt-5.4` | Codex-optimized agentic coding model. Designed for exactly this. Has 10x tier through May 17. |
| Multi-file refactor (mechanical edits across many files) | `gpt-5.3-codex` (sandbox) | `gpt-5.4` | Codex sandbox is the right shape. Tests run inline. |
| Writing unit tests for new code | `gpt-5.3-codex` (sandbox) | `claude-sonnet-4-6` | Test code is what codex models are best at. |
| Debugging a failing test (diagnosis + fix) | `gpt-5.4` (sandbox) | `claude-sonnet-4-6` | Frontier reasoning helps with diagnosis. Use the more capable Codex variant. |
| Architecture spec writing (the brief Codex executes against) | Claude (main session) | — | Needs full session context, design history, user preferences. Cannot be delegated without losing nuance. |
| High-cost-of-error edits (prompt templates, MODELS dict, public APIs) | Claude (main session) | — | Subtle wording matters; same context-loss problem as architecture spec. |
| Reading dispatch outputs / triaging logs | Claude (main session) | — | Token-cheap with `tail -N`; needs context to triage. |
| Final review of a PR before merge | Claude (main session) + user | Gemini Pro adversarial pass | Last sanity check; merge gate. |

### Review / second-opinion tasks

| Task | First choice | Fallback | Why |
|---|---|---|---|
| Adversarial PR code review (cross-family) | `gemini-3.1-pro-preview` | `gpt-5.4` | Cross-family review catches bugs same-family review misses. Used on PR #218-#224 successfully. |
| Adversarial PR code review (same family, independent model) | `gpt-5.4` reviewing `gpt-5.3-codex` work | — | Same-family-different-model independence is real (we proved this on PR #224). |
| Architecture / design critique | Both Gemini Pro AND `gpt-5.4` in parallel | `claude-opus-4-6` last resort | Two independent critiques catch more. Use Claude only when both are unavailable or when context-rich session reasoning is needed. |
| Calibration test scoring / fact verification | `gpt-5.3-codex-spark` | Manual by Claude | Calibrated for this. Cheap. |
| Reading and synthesizing review feedback | Claude (main session) | — | Synthesis needs session context. |

### Bulk / repetitive tasks

| Task | First choice | Fallback | Why |
|---|---|---|---|
| Bulk module drafting (10+ modules) | `gemini-3.1-pro-preview` via dispatch script | `claude-sonnet-4-6` | Cheapest at quality. Sequential per the never-parallelize-Gemini rule. |
| Bulk fact-check pass on existing modules | `gpt-5.3-codex-spark` | `claude-sonnet-4-6` | Calibrated. Cheap. Spark is fast. |
| Bulk content audit (find broken examples, dead links) | Codex sandbox running deterministic checks | — | Not an LLM task — use deterministic tools. |

### What stays with the user

- **Final merge decisions** — never delegate the merge gate.
- **Budget / billing decisions** — only the user can decide what tier to subscribe to.
- **Curriculum scope / direction** — only the user knows the teaching goals.
- **Anything involving real-world consequences** (deploys, posts, money) — confirm first.

## Principles

### 1. Pick the cheapest model that produces production quality

The fact-grounding calibration showed that `gpt-5.3-codex-spark` (cheapest Codex
tier) outperformed `gpt-5.4` (frontier) by 5 points on the proven flap zone.
Don't reflexively pick the most expensive model. Calibrate and use the cheapest
that does the job.

### 2. Use ROLE assignments, not MODEL identities

The `MODELS` dict in `scripts/v1_pipeline.py` maps roles (writer, fact_grounding,
review, write_targeted) to specific model names. The model names will change as
pricing shifts, new models land, and tiers rebalance. The roles are stable.
Always think "who fills the writer role this week?" not "is gemini-3.1-pro-preview
better than gpt-5.4?"

### 3. Cost-of-error determines who does the task

High cost-of-error tasks (prompt templates, architecture decisions, merge
decisions, anything affecting many users): Claude main session, because the
context for the call lives there.

Low cost-of-error tasks (greenfield function from a spec, mechanical refactor,
unit tests): delegate to Codex/Gemini in their sandboxes.

### 4. Save Claude budget for things only Claude can do

Claude main session is the bottleneck — peak hours penalty, finite Sonnet/Opus
calls, irreplaceable for synthesis tasks. Anything that can plausibly be done
by Codex or Gemini SHOULD be done by them, especially while Codex is on the
10x tier through 2026-05-17.

### 5. Cross-family review is non-negotiable

Per the never-merge-without-review rule: every PR gets adversarial review by an
INDEPENDENT model family before merge. The architecture decision settled in
this session adds: same-family-different-model is also acceptable as one of the
two reviews (gpt-5.4 reviewing gpt-5.3-codex's work). But there must be at
least one truly cross-family review.

### 6. Calibrate before you trust

The fact-grounding calibration taught us that priors about which model is best
are often wrong (frontier Codex was BEATEN by ultra-fast Codex on its own
specialty). Before settling on a model for a critical role, run a 30-minute
calibration test on the actual task. The cost of calibration is much lower than
the cost of shipping the wrong model.

## Open questions / pending data

- **Writer test rigorous re-run** — currently in flight (`writer-calibration-rigorous.py`).
  Will publish as `writer-calibration-RIGOROUS-2026-04-12.md` when complete.
  May change the writer first-choice from Gemini Pro to a different model if
  hallucination data reveals a clear winner.
- **Sonnet writer cost vs Gemini Pro** — preliminary writer test treated Sonnet
  as expensive without checking. Sonnet 4.6 on the Anthropic Pro plan is actually
  cheap. Re-test in flight.
- **Image input testing** — Codex `--image` flag is documented but not yet
  tested with a real diagram or screenshot. Should be smoke-tested before
  relying on it for UI debugging delegation.
- **gpt-5.4 writer dispatched late** — already folded into the rigorous re-test.
- **Capability test for sandbox subprocess scope** — Codex `--sandbox
  workspace-write` allows file edits, but the exact subprocess permissions
  (can it run `kubectl`? `helm`? `curl`?) need a smoke test before relying on
  it for the deterministic integrity layer.

## Living document

This matrix should be updated when:

1. A new model is added to the rotation (re-test capability + run a calibration)
2. Pricing changes (re-evaluate cost-quality tradeoffs)
3. A delegation produces a noticeably bad result (record the failure mode)
4. A new task type emerges that doesn't fit the existing categories

Last updated: 2026-04-12 (initial creation, preliminary writer data, rigorous
re-test in flight).

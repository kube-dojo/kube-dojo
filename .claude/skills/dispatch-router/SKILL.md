---
name: dispatch-router
description: Pick the right KubeDojo agent for a task across ALL activities — write / code / review / research / mechanical, not just review. Activity × lane matrix → agent → model → dispatch command. Roster as of 2026-06-04 (cursor, codex, opus, agy[model-selectable], gemini, deepseek, grok via hermes). Use before any dispatch. Triggers on "which agent", "dispatch", "route to", "who should do this".
last_calibrated: 2026-06-04
---

# Dispatch Router Skill

Pick the right agent + model + tier for a task before firing a dispatch. This skill is the orchestrator's pre-flight checklist. It encodes [[reference_provider_routing_economics]] and the rotation of caps as of `last_calibrated`.

**Always cross-check memory keys** below before relying on an agent — caps and prices rotate weekly.

## Activity × lane matrix (2026-06-04) — route by ACTIVITY, not just review

Pick the row for the activity, then the **primary doer**; for any write/author row, send the output to a **cross-family reviewer** (a DIFFERENT model family than the doer). All lanes below are flat-rate/cheap **except opus headless** (the one metered-after-2026-06-15 lane → cap at ≤1–2 of the hardest reviews per wave).

| Activity | Primary doer | Cross-family reviewer(s) | Off-load / candidates |
|---|---|---|---|
| **Curriculum content — WRITE** (prose modules, expand-to-floor) | **cursor** `--model auto` ‖ **codex** gpt-5.5 (quality-critical first pass) | opus(≤1/wave) + agy(3.1-pro-high) + gemini + deepseek + grok-4.20-0309-reasoning — pick ≥1 of a different family than the author | agy (2nd writer), deepseek, grok-4.3 |
| **Curriculum content — REVIEW** | — | **opus** (strongest) / **cursor** / **agy** (the Google lane) / **deepseek** (cheap) / **grok-4.20-0309-reasoning** | mix ≥2 families; ≤2 per OAuth; ground-check ALL. ~~gemini-cli~~ RETIRED ~2026-06-15 → use agy |
| **Code / tooling — WRITE & FIX** (scripts, adapters, pipeline) | **cursor** `--model auto` (strongest fixer, 3/3) | **codex** (danger+worktree) / **opus** / **grok-build-0.1** / **deepseek** | codex |
| **Code / tooling — REVIEW** | — | **codex** (danger+worktree) / **opus** (best code-correctness) / **grok-build-0.1** / **deepseek** | feed grok-build COMPLETE diffs |
| **Code-heavy MODULE content** (extending-k8s, tool certs — modules WITH code that must build) | **codex** gpt-5.5 (factual/version/runnability best) | **opus** (route ≥1 here — caught every extending-k8s P1) + **grok-build-0.1** (code) + **deepseek** | cursor, agy |
| **Research / gap-analysis / architecture** | **codex** (architect/consult) + **opus** (architect class) | `ab discuss --with claude,codex,gemini` for high-leverage ([[.claude/rules/decision-card]]) | deep-research harness; chrome MCP for source fetch |
| **Mechanical / deterministic** (gate fixes, link fixes, batched edits, search) | **cursor** or **codex** (cheap tier: composer-fast / spark / mini) | self-verify (`verify_module.py`, build, health) | — |

**Cross-family map** (reviewer ≠ author family): OpenAI = codex · Anthropic = claude/opus · Google = **agy** (gemini-cli RETIRED ~2026-06-15, user 2026-06-07) · DeepSeek = deepseek · xAI = cursor(composer-2.5) **and** grok. ⚠️ cursor(composer-2.5) and grok-composer are the SAME model — they cannot cross-review each other; grok-4.x/grok-build are a distinct xAI line (OK to review cursor-authored, with care).

**Cost order (use flat-rate first; deepseek is dirt-cheap, not avoided):** cursor (Pro+ 3×, the volume workhorse) · codex (weekly cap → quality-critical) · agy (the Google pool; gemini-cli RETIRED ~2026-06-15) · deepseek (≈free, the off-seat reviewer) · grok (xAI sub via hermes). **opus headless is the only genuinely metered lane post-2026-06-15 → ≤1–2 hardest reviews/wave; before then (Max 20× weekly) use it freely** ([[feedback_claude_billing_reroute]]).

## Roster details — 2026-06-04

> **What changed (2026-06-04, session 100):** agy `--model` now works (#1780) → agy is a Gemini-3.1-Pro-High **content/reviewer lane**; cursor review default fixed `gpt-5.5`→`auto` (#1782) — cursor uses **auto or composer-2.5 ONLY**; grok reachable via **hermes `--provider xai-oauth`** (#1783) — grok-4.20-reasoning (content) + grok-build-0.1 (code) both validated disciplined/no-fabrication; **deepseek is dirt-cheap** (use freely, NOT avoided). See [[feedback_cursor_proplus_3x_roster]], [[feedback_grok_cli_candidate_roster]].

| Agent | Access path | Strength | Constraint | Memory key |
|---|---|---|---|---|
| cursor (composer-2.5 / auto) | `dispatch_smart --agent cursor --model auto`; OR cursor IDE | **Volume workhorse** (Pro+ 3×): T0 content author, code/throughput, strongest bug-fixer, cross-family reviewer (in-cluster-verifying). | Use `auto` (preferred) or `composer-2.5` ONLY — never gpt-5.5 (review-class default fixed in #1782). composer-2.5 == grok-composer (same family). | [[feedback_cursor_proplus_3x_roster]], [[feedback_cursor_model_auto_not_composer]], [[feedback_cursor_is_strong_bug_fixer]] |
| codex (gpt-5.5 / spark / mini) | `dispatch_smart --agent codex` | Quality-critical author (factual/version/runnability), code review, architecture. gpt-5.5 top tier; spark=edit/draft; mini=search. | Weekly cap → reserve for quality-critical. Review ALWAYS `--mode danger --worktree X` (cwd mandatory for danger). Content fixes via `draft`+gpt-5.5+`--timeout 3600` (edit-class SIGKILLs). | [[feedback_codex_model_routing]], [[feedback_codex_review_danger_mode]] |
| opus headless (claude) | `dispatch_smart --agent claude --model claude-opus-4-8` | **STRONGEST reviewer** (content + code-correctness; caught the verifier-blind P1s). Review-class = read-only, no MCP-bloat. | Can stall ~20min/0-output in read-only → re-route if >10min. **Metered programmatic pool post-2026-06-15 → ≤1–2/wave**; free on weekly quota before then. | [[feedback_claude_billing_reroute]] |
| **agy (Antigravity 1.0.6, model-selectable) — THE Google lane** | `dispatch_smart --agent agy --model gemini-3.1-pro-high` (Flash for review/search) | Gemini-class content writer + cross-family reviewer; independent Google pool. Replaces retired gemini-cli. **RAG-CAPABLE headless.** | `--model` works since #1780. RE-PROVE write on 3.1-pro before load-bearing (fabricated on Flash). **MCP/RAG works NOW (1.0.5+ `url` in `mcp_config.json`): the `sources` server (`:8766/mcp`, the RAG dictionaries) is pre-configured in `~/.gemini/config/mcp_config.json` + loads on startup; verified agy lists & calls `check_russian_shadow`/`query_sum20`/`verify_word` in `-p` (adapter's `--dangerously-skip-permissions` auto-approves). → agy = the flat-rate RAG reviewer for UK translation (#1829), no orchestrator/claude-budget bottleneck.** Confirm usable past the 2026-06-18 free-tier transition. | [[feedback_gemini_cli_sunset_pivot_to_agy]], [[reference_agy_antigravity_cli]] |
| ~~gemini-cli~~ **RETIRED ~2026-06-15** | — (do NOT route here) | _was_ the Google reviewer → **use agy** | Unusable from ~2026-06-15 (user 2026-06-07). Its `--mcp` was inert anyway (#1827 pilot). | [[feedback_gemini_cli_sunset_pivot_to_agy]] |
| deepseek-v4-pro | `dispatch_smart --agent deepseek` (via hermes provider=deepseek; review needs `--mode workspace-write`+`--worktree`) | **Dirt-cheap off-seat cross-family reviewer + 2nd fixer.** Use freely. | Hallucinates numbers/schemas → ground-check. NEVER from GH Actions (China-host 403). | [[feedback_deepseek_v4_pro_viable_for_t0_content]], [[feedback_deepseek_hallucinates_on_gh_schemas]] |
| grok via hermes (xai-oauth) | `dispatch_smart --agent hermes --model grok-4.20-0309-reasoning` (content) \| `grok-build-0.1` (code) — routes to provider `xai-oauth` | grok-4.20-reasoning = content reviewer; grok-build-0.1 = code reviewer/fixer (code ONLY). Both validated disciplined, no fabrication. | Needs `hermes login --provider xai-oauth` (OAuth, re-login after a hermes rebuild — only deepseek survives). Standalone `grok` CLI headless is transport-broken. Feed grok-build COMPLETE diffs. n=1 each → keep ground-checking. | [[feedback_grok_cli_candidate_roster]] |
| grok-4.3 / grok-4.20-non-reasoning | `dispatch_smart --agent hermes --model grok-4.3` | Content candidates (smoke-pass; not yet quality-trialed). grok-4.20-multi-agent FAILS plain oneshot (needs agentic mode). | xai-oauth via hermes. | [[feedback_grok_cli_candidate_roster]] |
| hermes / opencode / qwen (metered) | `hermes -z --provider <p> -m <m>`; `dispatch_smart --agent {opencode,qwen}` | Multi-provider reach (hermes is also the deepseek + grok transport). | Pay-per-call beyond the subscription paths → only for x.com fetch (grok-4.3), grok-4.x content-candidate eval, or models no sub reaches. | [[feedback_grok_for_x_dot_com_links]], [[reference_qwen_hermes_openrouter]] |

## Task class → agent decision tree

> The **Activity × lane matrix above is the authoritative router** — use it first. The command-level detail below is reference for each `dispatch_smart` task class.

### Search / read-only research
1. **Cheapest first**: `dispatch_smart search --agent codex` (gpt-5.4-mini) OR `claude-haiku` inline.
2. Do NOT use Opus or gpt-5.5 for search — overkill ([[reference_dispatch_smart]]).
3. For browser-required source fetch: `mcp__claude-in-chrome__*` ([[feedback_chrome_for_primary_source_fetch]]).
4. For x.com links: hermes grok-4.3.

### Edit / sweep over many files
1. `dispatch_smart edit --agent <claude|codex>` (sonnet via subprocess for claude; spark for codex).
2. **NEVER use Agent-tool subagents for per-file sweeps** — 5x cost ([[feedback_dispatch_smart_for_sweeps]]).

### Draft (new content / module write)

T0 author primary is **codex-or-cursor** depending on codex weekly-cap state — quality-best lane per [[feedback_quality_over_budget_in_role_allocation]]:

1. **Codex cap healthy (default)** → `.venv/bin/python scripts/dispatch_smart.py draft --agent codex --mode danger --worktree X`. Stronger first-pass quality (factual/version/runnability). Codex `--search` is set automatically by the `draft` task class (`codex_search=True` at `scripts/dispatch_smart.py:168`); do NOT pass `--search` on the dispatch_smart CLI — it's a codex-CLI flag exported via `KUBEDOJO_CODEX_SEARCH=1`. The default codex model for `draft` is `gpt-5.3-codex-spark`; override with `--model gpt-5.5` for the top tier (higher per-call cost but cleaner first-pass). See [[feedback_codex_writer_needs_search]].
2. **Codex cap thin / throttle (or just high volume)** → cursor via `.venv/bin/python scripts/dispatch_smart.py draft --agent cursor --model auto` (headless) or cursor IDE. Use `auto` (preferred) or `composer-2.5` — never gpt-5.5. Verifier-pass ≠ runnability ([[feedback_composer_2_5_viable_for_t0_content]]); pair with a cross-family R1 review. Session 52 cursor-authored tooling/api/docs cohort measured 4/7 (57%) first-pass NEEDS_CHANGES — proxy signal that fix-pass is reliable but it's 2-3 rounds per PR. (No curriculum-T0 cohort yet at scale to measure directly.)
3. **Off-load (3+ codex authors in-flight)** → `dispatch_smart draft --agent deepseek`. Spread parallel-cap per [[feedback_parallel_rewrite_cap_three]].
4. **Bug fixes (any cap state)** → cursor composer-2.5. Proven 3/3 first-commit on session 51 bug PRs per [[feedback_cursor_is_strong_bug_fixer]]; different lane than T0 author.
5. See [[curriculum-writer]] for the author contract that binds every lane.

### Review (cross-family PR review)
1. Pick reviewer per Decision Card C routing — see [[cross-family-reviewer]].
2. Mix agents for 3+ parallel reviews ([[feedback_parallel_review_oauth_burst]]).
3. Always `--mode danger --worktree X` for codex review ([[feedback_codex_review_danger_mode]]).

### Architect / consult / decision
1. `dispatch_smart architect --agent codex` (gpt-5.5).
2. For high-leverage decisions: `scripts/ab discuss --with claude,codex,gemini` ([[.claude/rules/decision-card]]).
3. Consult codex on non-trivial scope decisions ([[feedback_consult_codex_on_decisions]]).

## Pre-flight checklist (before EVERY dispatch)

1. **Is the agent's auth alive?**
   - Codex: `codex exec --help` should not 403. If it does, `codex login`.
   - Gemini: cycle OAuth account if recent rate-limit (4 manual OAuth rotation).
   - Agy: open agy panel, verify Claude tier selected.
2. **Are caps healthy?** Check the panel/dashboard before firing 3+ in parallel.
3. **Will this burn the cheap-tier first?** If the cheap tier (mini/spark/flash-lite) can do it, use it. Don't reflex-bump to gpt-5.5 ([[feedback_codex_model_routing]]).
4. **Will this fan out beyond the parallel cap?** Hard cap 3 parallel rewrites ([[feedback_parallel_rewrite_cap_three]]).
5. **Will this trip the OAuth burst limit?** Mix agents for 3+ parallel reviews ([[feedback_parallel_review_oauth_burst]]).
6. **Warn the user** before 3+ parallel OR 5+ sequential to any single agent in 10 min ([[feedback_warn_before_gemini_quota_burn]]).

## During Anthropic throttle (recurring constraint)

When the orchestrator's chat tier is throttled:
- **Preserve opus orchestrator** (this terminal). Do NOT spawn `dispatch_smart --agent claude` headless.
- Route review → codex / agy (Claude tier) / gemini-3.1-pro-preview.
- Route edit → codex / agy.
- Route draft → composer-2.5 (cursor) / codex / deepseek.

The throttle window passes; resume normal routing post-reset. Default Claude weekly reset = Monday morning.

## After dispatch

1. Use `run_in_background: true`. Read `logs/dispatch_responses/<task-id>.txt` when notification fires.
2. **Do NOT spawn `until grep ... do sleep` watchers** — the wrapper notification IS the signal ([[feedback_no_separate_dispatch_watcher]]).
3. On finalize: check PR status, read produced reports, apply deltas, file follow-ups.

## Heredoc workaround for danger-mode briefs

After 2-3 consecutive `cat /tmp/brief.md | dispatch_smart --mode danger` calls, auto-mode classifier blocks the pattern. Workaround: inline heredoc so the brief is visible inline:

```bash
.venv/bin/python scripts/dispatch_smart.py draft --agent codex --mode danger \
  --worktree foo --prompt-file - <<'BRIEF'
... brief content ...
BRIEF
```

Heredoc satisfies the auditability intent; not for smuggling unreviewed content ([[feedback_heredoc_for_danger_dispatches]]).

## References

- [[reference_dispatch_smart]] — `scripts/dispatch_smart.py` task-class wrapper.
- [[reference_provider_routing_economics]] — provider vs agent vs model distinction.
- [[reference_agy_antigravity_cli]] — agy CLI details.
- [[reference_claude_i_billing_split]] — claude-i interactive-pool billing split.
- [[cross-family-reviewer]] — review-side routing protocol.
- [[curriculum-writer]] — author-side routing protocol.
- [[curriculum-orchestrator]] — the parent role that calls this skill.
- [`scripts/dispatch_smart.py`](../../../scripts/dispatch_smart.py) — the wrapper itself.
- [`scripts/ab`](../../../scripts/ab) — multi-agent bridge for `ab discuss`.

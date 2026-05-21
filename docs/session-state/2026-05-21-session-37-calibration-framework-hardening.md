---
title: Session 37 — Calibration framework hardening + Wave C/D sweep + new lanes
session_label: session-37-calibration-framework-hardening
date: 2026-05-21
driver: claude-opus-4-7 inline (single session)
predecessor: docs/session-state/2026-05-21-session-36-overnight-cks-rewrites-plus-calibration-report.html
---

# Session 37 — Calibration framework hardening + Wave C/D sweep + new lanes

2026-05-21 ~04:00 → 2026-05-21 ~10:00 local (~6h) · driver: claude opus 4.7 inline

User signals:
> "orientate then continue from last session handoff [...] pls continue with the benchmarking framework, the benchmarks and i am waiting for th result. we should add to the test how the model is using mcps and following the harness if possible as well"
>
> "we should use more often the /code-review command imo"
>
> "add it to your memory the /code-review or you will forget it"
>
> "do we need to redo some earlier test because of bugs maybe > ie gemini 3.5 flash ? or deepseek ? lets add different kind of languages: python, nodejs, java, rust, go. do you have other siggestions ?"
>
> "we still should use grok, ie when i give you a x.com link you should call grok through hermes to get the content. voila!"

## TL;DR

Took the session-36 calibration foundation from "ran one sweep, several known
bugs" to a hardened framework with a 168-cell ledger, two new lanes (mcp-use +
harness-following), a properly-scored CodeReview lane (no more 0.50 all-tied),
a cost/quality Pareto module, and a committed wave runner with pre-flight
adapter probes. Fired an 88-cell Wave C/D sweep that ran 88/88 ok, with the
pre-flight catching one broken deepseek adapter on first try and saving an
estimated $5 + 60 min of wasted dispatch. Re-ran 7 gemini-3.5-flash-high
writer cells corrupted by the session-36 agy-hang bug; re-scored 40 Wave A+B
prose cells with the proper sonnet + gemini-3.5-flash-high judge pair (session
36 had fallen back to sonnet × sonnet because of the same agy bug). Did not
yet add per-language code-writing fixtures because the existing
CodeWritingScorer is Python-specific (pytest + ruff); deferred per-language
test harness to next session per user decision.

## Framework changes landed this session

| File | Change |
|---|---|
| `scripts/calibration/schema.py` | WAL mode by default in `init_db` — kills the session-36 lock contention. |
| `scripts/calibration/run_cell.py` | `_effective_cwd` contextmanager swaps in a tempdir cwd when dispatching to agy-cli — fixes the 1800s judge-hang from session 36. |
| `scripts/calibration/score_cell.py` | (1) Per-lane judge timeouts (`JUDGE_TIMEOUTS_S`: 90s for mcp-use/harness-following, 180s for prose lanes). (2) Parallel judge1+judge2 dispatch via ThreadPoolExecutor. (3) New `McpUseScorer` + `HarnessFollowingScorer` classes. (4) `_assert_lane_set_consistency` at module load. (5) `CodeReviewScorer` switched to ratio-gates (finding_recall ≥0.6 + hallucination_rate ≤0.25) — fixes the v1 all-tied-at-0.50 collapse. |
| `scripts/calibration/models.py` | `LANES` extended from 10 to 12 (added `mcp-use`, `harness-following`). |
| `scripts/calibration/run_wave.py` | NEW — committed family-parallel wave runner with pre-flight adapter probes. Smoke flag, lane filter, summary JSONL. Includes `_assert_lane_fixture_consistency`. |
| `scripts/calibration/pareto.py` | NEW — cost-per-quality Pareto computation; subscription-tier and hermes/openrouter $/sec rates; quality floor at 1.0 sinks empty-response models. |
| `scripts/calibration/prompts/v1/{code-review,debugging,mcp-use,harness-following}/*.md` | 5 new fixture prompts: `k8s-controller-leader-election` (Go controller, 6 planted findings), `pod-pending-topology-mismatch` (EKS multi-AZ), `define-the-word-in-uk` (Ukrainian RAG tool plan), `inline-write-falco-module` (v1 — too easy), `claude-md-context-cks-tweak` (v2 — rules in simulated CLAUDE.md). |
| `scripts/calibration/ground-truth/v1/.../*.yaml` | 5 corresponding ground-truth YAMLs. |
| `tests/calibration/test_score_cell.py` | +6 fixture-coverage tests; updated CodeReview gate-name assertions for the ratio-gate rename. |
| `tests/calibration/test_models.py` | Lane count assertion bumped 10 → 12 (with explicit `in LANES` checks for new lanes). |

## Wave C/D + new-lane backfill — results

88 cells dispatched and scored ok. Ledger grew 80 → 168 cells. Wall-clock
~50 min (openai serialized at 26 cells dominated). Pre-flight aborted the
first dispatch on a 120s deepseek timeout; bumped to 240s and re-fired.

Headline ranking (all 14 anchors, det+judge/10):

1. `gpt-5.5` (1.66) — overall #1 with new lanes counted
2. `claude-opus-4-7` (1.65)
3. `claude-sonnet-4-6` (1.62)
4. `gpt-5.3-codex-spark` (1.62) — **cheap-tier winner; new**
5. `gpt-5.4-mini` (1.61) — **slow on prose (1116s on content-review); new**
6. `gemini-3.1-pro-preview` (1.59)
7. `gemini-3.1-flash-lite-preview` (1.56) — **new**
8. `deepseek-v4-pro` (1.50)
9. `grok-4.3` (1.49) — **Wave C anchor**
10. `gemini-3.5-flash-high` (1.47 — pre-rerun; updated below)
11. `deepseek-v4-flash` (1.47)
12. `claude-haiku-4-5` (1.42) — **new**
13. `qwen3.6-plus` (1.39)
14. `qwen3.6` (0.83) — **collapsed; not production-viable**

Surprising findings (full detail in `docs/audits/2026-05-21-calibration-wave-cd-results.html`):

- `gpt-5.3-codex-spark` ties opus on mcp-use lane (1.00 / 10.00) and wins
  the cost/quality Pareto outright at $0.0144/quality unit.
- `harness-following` lane was **too easy** (13/14 perfect score) because
  the v1 fixture spelled all 4 rules in the immediate prompt. Rebuilt for
  v2 with rules in a simulated CLAUDE.md context (not yet re-run).
- New `k8s-controller-leader-election` code-review fixture STILL collapsed
  to 0.50-tied across Wave C/D models — it was a scorer-side problem, not
  fixture-side; the ratio-gate fix landed this session.
- `qwen3.6` (non-plus) produced empty / refused responses on 6 of 12 cells.
- `gemini-3.5-flash-high` recovered on the new lanes (was collapsed on
  prose in Wave A+B) and is the #2 cost/quality model in the Pareto.

## Re-runs landed this session

Phase 1: re-dispatched 7 `gemini-3.5-flash-high` writer cells that were
corrupted by the session-36 agy-hang bug (empty responses). Run with the
agy-cwd fix in place.

Phase 2: re-scored 40 Wave A+B prose cells with the proper sonnet +
gemini-3.5-flash-high judge pair (session 36 had to fall back to sonnet ×
sonnet — no inter-family signal). New scorer rows (`scorer='llm-judge:
gemini-3.5-flash-high'`) inserted alongside existing sonnet rows;
additive, doesn't lose old data.

## Memory writes

- `feedback_use_code_review_command_often.md` — user wants `/code-review`
  (renamed from `/simplify` in v2.1.146) invoked routinely after non-trivial
  changes. `high` effort for money-burning paths.
- `feedback_grok_for_x_dot_com_links.md` — x.com / twitter.com URLs must be
  fetched via grok-4.3 over hermes; native X integration that no other
  adapter has. Coverage > general benchmark score.

Both added to MEMORY.md TOP PRIORITY.

## Carryovers — next session

1. **Per-language test harness** (user decision in this session). Wire
   pytest + ruff (existing), node/jest, javac + junit, cargo test, go test
   into a per-language CodeWritingScorer dispatch. Need: install toolchains
   in the venv or call out to system, language-detection in code-block
   extraction. ~1 day infra.
2. **Language fixture sweep** once the per-language scorer lands. Cover
   Python (harder), TypeScript, Java, Rust, Go × code-writing + code-review
   + debugging = 15 fixtures. Estimated ~$10 + 90 min wall-clock for the
   first sweep.
3. **Stability runs** (user asked for) — pick 3-5 high-variance cells per
   model and run them 3× to compute variance. Tells us whether a 0.50 score
   is solid or noisy.
4. **Real-execution mcp-use lane** (user asked for) — wire the
   learn-ukrainian RAG MCP server (port 8766) so the calibration cell
   actually executes the planned tool calls instead of just describing
   them. Score on chain outcome (does the lookup succeed, is the answer
   correct).
5. **Re-fire harness-following on v2 fixture** — the new
   `claude-md-context-cks-tweak` fixture is committed but not yet dispatched.
6. **Stage 1 sweep results** — re-run report once Phase 1 / Phase 2 finish;
   the gemini-3.5-flash-high prose scores will shift meaningfully (8 lanes
   × 2 judges now vs. 2 lanes × 2 judges before).
7. **Continue CKS rewrites** (still 155 critical-quality modules in queue).
   Module 5.4 Admission Controllers, 6.1 Audit Logging, 6.2 Falco, 6.3
   Container Investigation.

## End state

- Branch: main at d709538c (handoff PR landed last session)
- Tests: 34 / 34 pass; ruff clean across calibration package
- Worktrees: only primary
- Untracked files this session: 5 new fixture prompts + 5 ground-truth
  YAMLs + 1 new `run_wave.py` + 1 new `pareto.py` + 1 new audit HTML + 1
  new session-state .md
- Modified files: schema.py, run_cell.py, score_cell.py, models.py,
  test_models.py, test_score_cell.py, MEMORY.md

## References

- Predecessor: docs/session-state/2026-05-21-session-36-overnight-cks-rewrites-plus-calibration-report.html
- Wave C/D audit: docs/audits/2026-05-21-calibration-wave-cd-results.html
- Wave A/B audit: docs/audits/2026-05-21-calibration-wave-ab-results.html
- Calibration spec: docs/calibration/v1-spec.html
- Framework source: scripts/calibration/

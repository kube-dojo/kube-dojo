# DECISION — Optimized UK translation REVIEW workflow (single-translation) — AGREED 2026-07-02

**Method:** `ab discuss uk-review-workflow --with claude,codex,agy --max-rounds 2`.
**Outcome:** claude ⟂ codex **converged, both [AGREE]** (Anthropic + OpenAI, 2 independent families).
agy failed both rounds (headless no-write flake #2099 — see caveat 3; it did not contribute).
**Hard constraint (user, not debated):** SINGLE translation (Sonnet-5 + `sources` MCP). No
double/multi-translation. The REVIEW carries the load — because it's *structured*, not redundant.

## The root cause of the s190 waste (~11 dispatches)
Not "too few reviewers." **Unstructured, scan-by-vibe review** + defects that should never have
reached a reviewer. A `redact` false-friend sat in a TABLE CELL that R1 skipped and only a post-fix
re-read caught. The fix is to *move coverage left*: mechanize the mechanical, front-load the known,
and force the review's single pass to be exhaustive.

## The agreed workflow (per module, after the Sonnet+MCP translation)

1. **Deterministic gates FIRST**, and they now carry more:
   - existing: `ab_parity.py`, `check_uk_changed.py` (CI russicism), `uk_calque_v2.py`, `uk_guards.sh`.
   - **NEW gate (claude amendment, agreed): the `rg`/`grep` exercise-consistency detector.** A ~20-line
     check alongside `uk_guards.sh`: for every UK exercise, grep its `rg`/`grep` command for surviving
     English tokens that are the *search target* while the prompt output was translated to Ukrainian →
     flag the mismatch. Converts s190 defect-class #4 from "hope a reviewer notices" to a free gate.
     codex lab-execution stays as backstop for the residue.
   - **NEW deterministic step: a risky-EN-term ANCHOR LIST** — mechanically extract from the EN every
     token matching the known false-friend / idiom / drain-class dictionaries, plus every `rg`/`grep`
     target. No model call. This list is fed to the reviewers as forced focus anchors.

2. **TWO cross-family reviewers, ONE parallel round — orthogonal axes (not redundant):**
   - **`codex/gpt-5.5` = FIDELITY axis — MANDATORY floor on every module.** Table cells, exercise/lab
     command consistency, `rg`/`grep`, code/prompt parity, executable/static checks. The only reliable
     catch for mechanical/parity defects.
   - **`agy/gemini-3.1-pro` = LINGUISTIC axis — when linguistic risk is real** (normal-and-above:
     non-trivial anchor density, idioms, prose-heavy). Ukrainian naturalness, russicisms, idioms,
     false-friends. MCP settles "is `викатка` a real lemma" (`verify_word`→NOT FOUND); it does NOT
     settle "does this technically-valid sentence read as translationese" — a distinct competency the
     corpus can't adjudicate. A thin, exercise-free stub gets **codex-floor + orchestrator inline only**.
   - **`deepseek-v4-pro` = optional cheap 3rd spotter, HIGH-RISK modules only**, never authoritative
     without MCP adjudication.
   - Tier at BOTH ends: codex always · agy when linguistic risk is real · deepseek high-risk only.

3. **Structured review output (kills the R1-miss→R2-find loop in ONE pass):** each reviewer must return
   - a **Coverage table**: `EN quote | UK rendering | verdict | source/tool (if linguistic) | defect class`
     — pre-seeded with the anchor-list rows, so a reviewer *cannot* skip the `redact` table cell.
   - **Findings**: only P1/P2, with a file quote + proposed fix.
   - Explicit rule in the prompt: **table cells / callouts / quiz answers / exercises are first-class
     prose; find one defect → scan for ALL siblings and report the count** (the s190 class-A lesson).
   - **Reject** by-dimension decomposition (one pass per dimension × modules) — dispatch blow-up, loses
     whole-document coherence. All classes go in one structured prompt per reviewer.

4. **MCP-ground the reviewers (#2086) — target state:** wire `sources` into the codex+agy review
   dispatch so they self-adjudicate (`verify_word`/`search_style_guide`) *before* flagging → flags arrive
   pre-verified, and the hallucination class drops (a reviewer forced to cite `verify_word` output can't
   invent `відповідєю`). Until #2086 lands, **orchestrator MCP-adjudication is the mandatory bridge/backstop**.

5. **Front-load the AUTHOR BRIEF (cheapest lever — a prevented defect costs ZERO review/fix dispatches):**
   promote every settled ruling into a hard substitution table in `scratchpad/uk-author-brief-*.md`:
   `redact→маскування/маскувати`, `drain node→вивести/дренувати вузол`, `SLO burn→спалювання`,
   `assumed→припущений`, `fluent→плавний`, `production→продакшен` (#2110), **+ the rg-pattern rule**
   (a translated exercise's verification command must search the UK string the learner types, or a
   language-neutral token — never the English word). **Flywheel:** each wave's *generalizable* review
   findings get promoted into the brief → the review surface shrinks every wave. (Ceiling: the brief
   prevents *known* classes; novel false-friends still need review.)

## Budget target
| Stage | s190 | Target |
|---|---|---|
| Author rounds | 1 + slippage | 1 (brief kills known classes) |
| Review | ~8 across 2 rounds | 1 structured round: codex-floor + agy-when-warranted (parallel) |
| Fix-pass | 3 | ≤1 class-A (same Sonnet+MCP subagent, fix ALL siblings) |
| **Total / module** | **~11 dispatches** | **~2–3 dispatches** |

## Caveats / dependencies (from the deliberation)
1. Reviewer-count: claude R1 argued for one grounded reviewer; **conceded** to codex's 2-specialist
   model — the axes are orthogonal (fidelity ⟂ naturalness), so it's coverage of two axes, not redundancy.
2. `deepseek` is net-negative on this task until MCP-grounded (sandboxed false-friends + no corpus).
3. **agy dispatch reliability is a live risk** — it flaked in THIS very deliberation (#2099) and carries
   ~1 hallucination/review. #2086 blunts the hallucination but NOT the flake → the linguistic axis needs
   a reliable fallback (composer-2.5 or a 2nd grounded pass), tracked as a dependency of the 2-reviewer default.

## Build follow-ups (to actually run the workflow)
- [ ] Write the `rg`/`grep` exercise-consistency gate detector (~20 lines, beside `uk_guards.sh`).
- [ ] Write the risky-EN-term anchor-list extractor (mechanical, from EN + the failure-mode dictionaries).
- [ ] Harden `scratchpad/uk-author-brief-*.md` with the s190 substitution table + rg-rule.
- [ ] Structured-review prompt template (coverage table + siblings rule) for codex & agy dispatch.
- [ ] #2086 — wire `sources` MCP into codex+agy review dispatch; harden the agy dispatch path (#2099).

**References:** channel `uk-review-workflow` (thread aa9144d466e6); `docs/session-state/2026-07-02-session-190-*.html`; #2086 (reviewer MCP), #2099 (agy dispatch), #2110 (production spelling).

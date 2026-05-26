# Tiered back-catalog review policy (amends Decision Card C)

**Date decided:** 2026-05-26
**Decided by:** user (explicit "do what the majority votes for")
**Deliberation channel:** `auto-approve-policy-2026-05-26`
**Thread:** `f79da8109c7f447999a072e6ccbeb5b5`
**Rounds:** 2
**Agents:** claude, codex, gemini -- all `[AGREE]` on Option B' in round 2

## Amends

[`docs/decisions/2026-05-24-reviewer-routing-composer-2-5.md`](2026-05-24-reviewer-routing-composer-2-5.md) (Decision Card C). C committed to backfilling composer-2.5 cross-family review records on ALL 277 `shipped_unreviewed` modules. This decision tiers that backfill instead of running it blanket.

## Context

`/quality` board shows 277 modules in state `shipped_unreviewed` -- they passed the heuristic rubric (score >=4) and merged to main, but have stage=UNAUDITED because there's no formal composer-2.5 review record. The two gates catch different failure modes:

- **Rubric heuristic** = structural compliance (lines, quiz, exercise, citations, diagrams)
- **composer-2.5 review** = semantic correctness (factual accuracy, runnability, version slips, hallucination)

When Decision Card C locked, we didn't have the live stratification data: 44/44 prereqs all rubric 5.0/5.0 on the live site for months, no user issues filed. Backfilling 277 composer-2.5 reviews = 3-4 weeks of reviewer capacity that would displace forward content work.

## Chosen option: B' (stratified Option B)

Tier the review requirement by risk class. Auto-approve only after a stratified sample validates the assumption.

### Eligibility for auto-approve

A module is eligible for `heuristic_auto` stamping only if ALL of the following hold:

- Rubric >=4.5
- Not in labs/security/cert tracks with runnable commands
- `revision_pending` is false
- On site >90 days
- No open GitHub issues filed against the module
- Positive traffic signal where available (Plausible analytics) -- claude's round-1 refinement, soft requirement

### Mandatory review remains for

- Brand-new content (post-2026-05-24)
- Recently T0-rewritten modules
- Rubric <4.5 OR `revision_pending` set
- Labs / security / cert modules with runnable command risk

### Validation protocol (sample first, schema after)

1. Sample 30 modules from the eligible pool, **stratified across tracks** (k8s / AI-ML / cloud / linux / prereqs), with explicit oversampling of lab/security/cert modules that have runnable commands.
2. composer-2.5 reviews each.
3. Verdicts classified by severity:
   - **Class A** (blocks learner): wrong CLI flag / API version in runnable command, broken lab, hallucinated tech
   - **Class B** (misleading but recoverable): stale version comment, weak citation, outdated link
   - **Class C** (cosmetic): typo, style nit -- does NOT count
4. Decision rule:
   - 0 Class A AND <=2/30 Class B (<10%) -> proceed: build `heuristic_auto` schema + stamp eligible modules
   - 0 Class A AND 3-9/30 Class B (10-30%) -> expand sampling on failing stratum
   - Any Class A in stratum X, OR >=10/30 Class B (>30%) -> fallback to Option A on stratum X only (not blanket)
5. If sample fails for all strata: revert cleanly to Decision Card C policy. No schema work was built, no stamping happened -- clean revert.

## Why this won

- **Rubric and review catch different things** -- neither C nor a blanket-drop is correct. Tiering is the only option that preserves both gates where they add value.
- **The 90-day user-gate is doing real work** -- established modules with no issues have already passed the most rigorous review possible (real readers).
- **Reversible** -- sample-first ordering means if the assumption fails, we revert with zero artifacts to undo.
- **Severity-tiering** -- codex's threshold pushback (Class A blocks regardless of %) prevents "10% wrong kubectl flag" from being treated like "10% stale citation".
- **Stratification** -- gemini's primary insight; foundational prereqs aren't representative of CKS lab content.

## Implementation sequence

1. Decision record written (this file)
2. Next: codex PR -- `/api/quality` redirect-stub bug fix + `generated_at` field on upgrade-plan + `scripts/quality/sample_back_catalog_review.py` (stratified sampler)
3. Run sampler -> 30-module list
4. Pace 30 composer-2.5 reviews (~3/hour to respect OAuth burst limit)
5. Tally A/B/C; apply decision rule
6. Branch: stamp via `heuristic_auto` schema OR fallback per stratum; close or supersede `#1504` accordingly

## Memory + cross-thread coherence

- Update `feedback_composer_2_5_sharper_reviewer.md` cross-link to point here when amending C
- This decision relaxes the orchestrator-skill clause "every shipped module must carry a composer-2.5 cross-family review record" -- that clause now applies only to the mandatory tiers above
- `#1504` epic stays open until step 5 result; outcome determines whether it closes or supersedes

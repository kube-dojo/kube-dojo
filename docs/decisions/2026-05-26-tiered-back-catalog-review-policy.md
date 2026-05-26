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

## Result (2026-05-26)

**Outcome: B' aborted. Universal stratum failure. Reverted to Decision Card C (full backfill via #1504).**

### What was sampled

- 15 of the originally planned 30 modules reviewed (sampling stopped early after the n=15 signal became conclusive).
- Stratified across all 7 tracks per the protocol; mixed-agent reviewer pool (cursor composer-2.5 + codex gpt-5.5 + gemini-3.1-pro-preview) to spread OAuth burst risk per `feedback_parallel_review_oauth_burst`.
- Sample output frozen at `logs/quality/back_catalog_sample_2026-05-26.json` (seed=2026, eligible pool 429).

### Per-stratum result

| Stratum | n | NEEDS_CHANGES | Modules w/ Class A | Total Class A defects | Decision |
|---|---:|---:|---:|---:|---|
| prereqs | 3 | 2 | 2 | 4 | FALLBACK |
| AI/ML | 1 | 1 | 1 | 2 | FALLBACK |
| linux | 2 | 2 | 2 | 5 | FALLBACK |
| cloud | 1 | 1 | 1 | 3 | FALLBACK |
| k8s | 1 | 1 | 1 | 1 | FALLBACK |
| on-premises | 3 | 2 | 2 | 2 | FALLBACK |
| platform | 4 | 3 | 3 | 7 | FALLBACK |
| **TOTAL** | **15** | **12** | **12** | **24** | **UNIVERSAL FALLBACK** |

80% of sampled modules had `NEEDS_CHANGES` verdict; 80% had at least one Class A learner-blocker. Every stratum had at least one Class A — triggering per-stratum fallback for all 7. The "all strata fail" clause of the converged decision rule applies: revert cleanly to Decision Card C policy.

### What Class A defects looked like (representative)

- `bash` code blocks labeled as runnable when the content is program output ("Hello from Go!", `apt`/`tree` output) — fails on copy-paste.
- Title-content mismatch (`neural-network-fundamentals.md` actually teaching NumPy/pandas).
- Lab manifests using fake/placeholder images (`my-company/backend-api:v2.4.1`).
- Wrong service names for the target distro (`sshd.service` in Ubuntu modules where `ssh.service` is canonical).
- Hallucinated tech (`k8sattributes` collector config with invalid metadata fields that crash the OTel collector at startup).
- Dangerous misconceptions (GitOps "pruning deletes a Service that was never declared in Git" — Argo/Flux prune only manages tracked objects).
- Multi-step labs where intermediate files referenced by later commands are never created in the visible flow.

These are bugs the rubric heuristic (line count + has-quiz + has-exercise + has-citations) cannot catch and that real users haven't filed issues against (most don't file issues — they hit the wall, get frustrated, and move on).

### Counterevidence — modules that passed cleanly

3 of 15 (20%) were APPROVE or APPROVE_WITH_NITS-cosmetic-only:

- `prerequisites/git-deep-dive/module-8-scale.md` — APPROVE clean
- `on-premises/planning/module-1.1-case-for-on-prem.md` — APPROVE_WITH_NITS (3 cosmetic only)
- `platform/disciplines/core-platform/platform-engineering/module-2.2-developer-experience.md` — APPROVE_WITH_NITS (6 cosmetic only)

These show the back-catalog is not uniformly broken — but a 20% clean rate is far too low to support auto-approve.

### Why the assumption failed

The Decision Card B' bet was: "rubric ≥4.5 AND no-issues-filed AND on-site >90 days = stable enough to skip formal review." Two reasons it failed:

1. **The rubric heuristic is purely structural.** It counts lines, looks for section headings, checks for `## Sources`. It cannot detect a mismatched title, broken bash, fake image refs, or hallucinated tech. A module can have a perfect structural rubric and still mislead learners. This is the classic structural-vs-semantic gap (see `feedback_teaching_not_listicles`).
2. **"No GitHub issues filed" is a weak proxy for "real users validated this."** Most learners who hit a broken `kubectl` flag or a non-runnable lab don't file an issue — they get frustrated and switch sites. Issue-count-zero ≠ correctness.

### Actions taken

- `#1504` epic stays as-is (composer-2.5 review of all 277 shipped_unreviewed modules). The systematic backfill IS the work.
- The `heuristic_auto` schema in `scripts/local_api.py` was never built. No stamping happened. Clean revert with zero artifact debt.
- 24 Class A defects from the sample are filed as a tracking issue (referenced from this section once created) for downstream content fixes — these are immediate-fix candidates regardless of policy outcome.
- `agents_extensions/shared/skills/cross-family-reviewer/SKILL.md` proved its weight here: the reviewer panel produced consistent, severity-tiered findings across 3 different agent families (cursor, codex, gemini) using the same brief. This validates the cross-family review skill, even as the back-catalog auto-approve policy didn't.

### Lesson for future deliberations

The deliberation protocol worked exactly as designed: codex's "sample first, schema after" ordering meant we paid only the sampling cost, not the stamping-then-unwinding cost. Even though the converged decision turned out to be wrong, the framework caught the error before it shipped. **Sample-first ordering is the load-bearing property of any decision built on an optimistic assumption about an unknown distribution.** Carry forward.

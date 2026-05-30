# RESOLVED 2026-05-30 (user)

- **Q1 kubectl-alias (129 mods):** KEEP `k` shorthand, RETUNE the gate. → DONE: PR #1669 (`fix/kubectl-alias-gate`). Gate now passes when `alias k=kubectl` is defined; only alias-less `k` usage flagged. **86 modules cleared, 67 → T0**; 43 still fail (alias-less `k` = real copy-paste bug, content follow-up).
- **Q2 war-stories (155 files):** REQUIRE real sources or REMOVE. Each incident told **once**; if mentioned elsewhere, **refer** to it — never retell. (Dovetails with the CI incident-dedup gate.) → TODO authoring pass (fabrication-vigilant). Inventory: 171 markers / 155 files (platform 100, k8s 36, ai-ml-eng 13, cloud 10, linux 11, on-prem 1); 11 modules have >1 war story.
- **Q3 body_words (462 mods):** Floor (5000) is CORRECT — failing modules are genuinely thin (median 2012 words; 341 under 4000). Author real content in curriculum order, cross-family reviewed. → TODO big authoring backlog.

---

# DECISION REQUIRED — How to remediate the 636 failing modules (de-frag is the wrong primary tool)

**Date:** 2026-05-30 · **Session:** 73 (overnight autonomous) · **Author:** claude (orchestrator)
**Scope:** the whole content-remediation effort (636 failing modules). Blocks: the bulk authoring/de-frag waves only. Safe deterministic cleanup already proceeded.

## Context — what changed tonight

You corrected two things: (1) process in **curriculum order** (`prerequisites → linux → ai → ai-history → k8s → cloud → ai-ml-engineering → on-premises → platform`), not `worklist.json`'s alphabetical order; (2) include ai / ai-ml tracks. Both are saved to memory.

Acting on that, I rebuilt the worklist in curriculum order and ran a **gate-by-gate diagnostic** on all 898 modules. It overturned the inherited "de-frag engine" premise:

| Defect class | Modules failing | Right fix |
|---|---|---|
| body_words (thin content) | **462** | author real content |
| other (structure/outcomes/sources) | **468** | author/restructure |
| density (fragmented prose) | 276 | de-frag |
| leaked source-H1 | 175 | **deterministic script ✓ DONE** |
| kubectl-alias in runnable code | 129 | policy (see below) |
| anti-fab "War Story" | 154 | policy (see below) |

**Killer stat:** exactly **1** module in the whole curriculum is *density-only* (de-frag alone reaches T0). De-frag — the inherited engine's main tool — completes one module. The real backlog is **content authoring at scale**, which is fabrication-prone (per `feedback_defrag_is_fabrication_prone`) and needs per-module cross-family review.

## Already shipped (safe, deterministic, no decision needed)

Repo-wide leaked source-H1 cleanup — removed the redundant `# Module X.Y:` H1 that duplicates `title:`:
- #1666 linux (27 mods, 8→T0) **merged**; #1667 k8s (87, 33→T0) **merged**; #1668 remaining 61 **auto-merging**.
- 175 modules cleaned, **42 → T0**, build-green, 0 tier demotions, reconciled exactly vs the verifier.
- New tool: `scripts/quality/fix_leaked_source_h1.py`.

## The decisions

### Q1 — kubectl-alias gate (129 modules): fix content, or fix the gate?
The curriculum **deliberately** teaches `alias k=kubectl` then uses `k get` as a documented shorthand. The verifier gate `runnable_no_kubectl_alias` penalizes exactly that.
- **Option A — expand content:** dispatch agents to expand `k `→`kubectl ` in code blocks + remove the alias + reword the prose, across 129 modules. High effort, fabrication-light but tedious; loses the shorthand the curriculum chose.
- **Option B — relax/retune the gate:** allow a single documented `alias k=kubectl` + `k` usage (one-line gate change in `verify_module.py`). 129 modules clear at once. Keeps the pedagogy.
- **Orchestrator recommendation: B**, unless the shorthand is genuinely a problem for copy-paste learners. One gate change vs 129 risky edits.

### Q2 — anti-fab "War Story" gate (154 modules): source, reframe, or retune?
"War Story:" is a recurring pedagogical device (realistic incident scenarios). The gate flags them as unsourced anecdotes. Many pre-exist on `main` and are good teaching.
- **Option A — author:** source or rewrite each as an explicitly-hypothetical scenario (154 modules, fabrication-prone — agents will be tempted to invent citations).
- **Option B — retune the gate** to accept a clearly-marked hypothetical framing (e.g. a `> Scenario (illustrative)` convention) instead of demanding a citation.
- **Orchestrator recommendation: B + a light convention.** Asking agents to "source anecdotes" is the single most fabrication-inducing task we could dispatch.

### Q3 — body_words (462) + other (468): the real backlog. How to attack?
This is genuine content authoring at scale — multi-session, must be per-module cross-family reviewed.
- **Option A — curriculum order, supervised waves:** small waves (cursor≤1 per your cap + codex), each cross-family reviewed before merge, you spot-check. Slow, safe.
- **Option B — re-examine the floors first:** confirm `body_words ≥ 5000` and the structural gates are calibrated right before authoring 462 modules to hit them. (7 linux modules sat 1–14 words over the floor — the floor bites hard.)
- **Orchestrator recommendation: B then A.** Validate the gates are the bar you actually want, THEN author in curriculum order with review. Don't author 462 modules to satisfy a possibly-miscalibrated floor.

## Awaiting
Your call on Q1 / Q2 / Q3. Until then I am NOT dispatching authoring/de-frag waves — only the deterministic H1 cleanup (done) was safe to run unsupervised. Wave-2 (6 cloud/k8s de-frags, done + gate-clean) is held on `remediate2/lane-*` for in-order merge.

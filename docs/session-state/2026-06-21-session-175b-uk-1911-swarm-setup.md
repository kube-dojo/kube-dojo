# Session 175b — #1911 UK Translation Swarm: setup brief (ready to execute)

**Continuation of s175. User is restarting for a clean session — this brief carries the full context.** Cold-start, load the curriculum-orchestrator skill, read this, then execute from "NEXT STEPS".

## Decision (user, s175)
Execute **#1911 (UK translation currency)** with a **Claude-subagent swarm ONLY** — do **NOT** dispatch external agents (agy / gemini / codex / cursor / deepseek). Parallel, MCP-validated, large overnight token budget ("lots of context until tomorrow — do as much as possible with swarm").

## WHY Claude subagents, not the usual dispatch (the load-bearing insight)
The `sources` MCP — VESUM morphology, СУМ-11/20, **Antonenko-Davydovych** style guide, **UA-GEC** calque corpus, **r2u** Russian→Ukrainian, GRAC frequency, `check_russian_shadow`, `query_pravopys` — is **subagent-accessible but NOT reachable by the external dispatch lane** ("MCP tools are orchestrator-only" per `feedback_uk_calque_review_sentence_reframe_not_grep`). So a **Claude subagent swarm can produce self-validating, calque-checked translations that the agy/gemini lane cannot.** This is the right tool for the job.

## Currency data — the real scope (computed s175, deterministic)
- EN pages: **1080**. UK pages: **447**.
- **633 MISSING** — EN exists, no UK file at all.
- Of the 447 existing pairs (word-ratio UK/EN): **133 current** (≥85%), **35 stale** (40–85%), **279 SEVERE STUBS** (<40% — nearly useless, obsoleted by the s100–175 EN expansion).
- **True current coverage: 133/1080 = 12.3%. Debt ≈ 947 pages.**
- Measure currency by **word-ratio + git-recency, NOT file existence** ([[feedback_translation_coverage_measure_staleness_not_existence]]).
- Recompute with the inline python from the s175 transcript (or re-run: walk `src/content/docs/**/*.md` excl `/uk/`, pair with `uk/<rel>`, ratio = UK_words/EN_words).

## Per-page pipeline (each Claude subagent does)
1. Read the EN page **and** `src/content/docs/glossary.md` (5.4 KB — MUST follow its term mappings).
2. Translate EN→UK at **95–100% length**, natural Ukrainian — **reframe Russian sentence patterns, do NOT calque** (sentence-level reframing, not word-swap — [[feedback_uk_calque_review_sentence_reframe_not_grep]]).
3. **MCP self-validation** (the quality gate the external lane can't do):
   - `verify_words` — every UK content word form must exist in VESUM (catch hallucinated forms).
   - `search_style_guide` (Antonenko-Davydovych) + `search_ua_gec_errors` + `check_russian_shadow` + `query_r2u` — scan for calques/Russianisms; **reframe each flagged sentence**.
   - `query_pravopys` for orthography edge cases (апостроф, м'який знак, у/в).
   - Known false-positives to LEAVE (don't "fix"): `являється`(=з'являється), `в якості`, `діючи`(gerund), `задача`, `даний`(=data), `один в один`(idiom), `вірний` substring of достовірний/перевірити. Disambiguate every grep stem.
4. Preserve frontmatter: translate `title`, keep `sidebar.order`; **add explicit `slug:` if the filename has dots** (per `.claude/rules/new-content-checklist.md`). Output to `src/content/docs/uk/<same-rel-path>`.
5. Stamp the `calque_review` frontmatter (see `scripts/quality/calque_review_stamp.py`).

## ⚠ PILOT FIRST — do not burn the overnight budget on an unproven pipeline
Claude's base **Ukrainian quality + calque-cleanliness is UNPROVEN for this project** (the roster historically used gemini/agy for UA, rated 9–10/10). **Run a 2–3 page pilot, orchestrator reads the output (calque scan + native-quality read), THEN scale.** If opus's Ukrainian is sub-par or calque-prone, adjust the pipeline (more aggressive MCP reframe loop, or reconsider the Claude-only constraint with the user).

## Swarm vehicle + git
- **Workflow tool** (background, context-isolated, pipelines over pages, ≤16 concurrent, ≤1000 agents/run). One workflow per track/batch (~30–50 pages); iterate; budget-scaled loop.
- Outputs → a **worktree** per batch → **PR** (build-check CI is a required gate). **Do NOT auto-merge** bulk translation — it needs the build gate + eventual human/quality review. Batch into reviewable PRs (per-track).
- A reference **current** UK page (e.g. a `prerequisites/` one, ≥85%) is a good few-shot quality anchor for the subagent prompt.

## Prioritization (proposed — confirm or adjust)
Biggest value first: the **279 severe stubs + 633 missing**. Suggest by track: finish **CKA/CKAD** (cert flagship, partially translated) → prerequisites gaps → cloud/k8s/kcna → platform. Extend the currency script to emit a **ranked page list** before launching.

## Services / environment
Healthy — `dev` (:4333) + `api` (:8768) running; `sources` MCP live; `feedback` service stopped (irrelevant). **No restart needed** beyond the session refresh the user is doing.

## NEXT STEPS (fresh session)
1. Cold-start (orchestrator skill + this handoff).
2. Extend the currency scan to emit a **ranked page work-list** (priority order).
3. Build the per-page subagent prompt (pipeline above) + run a **2–3 page PILOT Workflow**; orchestrator reviews Ukrainian quality + calque-cleanliness.
4. Pilot good → **scale to the overnight swarm** (Workflow over the prioritized batch, worktree → per-track PRs, build-gated).

## State at handoff
- Open issues: **only #1911** (board cleaned to 1 in s175). #1876 SOLVED+closed; 8 triaged; #1823 mermaid fixed; 3 PRs merged (#2071/#2072/#2073). 355 review records now tracked; STATUS.md pruned 333→140 KB.
- Tree clean, main green. Only the retained `.worktrees/g2-craft` (not ours, #1623).

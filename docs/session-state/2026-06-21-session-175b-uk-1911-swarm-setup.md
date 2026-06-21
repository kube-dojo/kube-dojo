# Session 175b — #1911 UK Translation Swarm: setup brief (ready to execute)

**Continuation of s175. User is restarting for a clean session — this brief carries the full context.** Cold-start, load the curriculum-orchestrator skill, read this, then execute from "NEXT STEPS".

## Decision (user, s175)
Execute **#1911 (UK translation currency)** with a **Claude-subagent swarm ONLY** — do **NOT** dispatch external agents (agy / gemini / codex / cursor / deepseek). Parallel, MCP-validated, large overnight token budget ("lots of context until tomorrow — do as much as possible with swarm").

## ⏱ Operating window (user, s175)
**High-throughput swarm runs NOW → tomorrow (2026-06-22) afternoon.** Push volume during this window. **The user will explicitly signal when to STOP and switch to "slower mode"** — until that signal, keep the swarm going (respect the pilot gate first). After the signal: wind down to normal one-at-a-time cadence. Do not self-throttle before the user's signal, but don't sacrifice the pilot-first quality gate for speed.

## WHY Claude subagents, not the usual dispatch (the load-bearing insight)
The `sources` MCP — VESUM morphology, СУМ-11/20, **Antonenko-Davydovych** style guide, **UA-GEC** calque corpus, **r2u** Russian→Ukrainian, GRAC frequency, `check_russian_shadow`, `query_pravopys` — is **subagent-accessible but NOT reachable by the external dispatch lane** ("MCP tools are orchestrator-only" per `feedback_uk_calque_review_sentence_reframe_not_grep`). So a **Claude subagent swarm can produce self-validating, calque-checked translations that the agy/gemini lane cannot.** This is the right tool for the job.

## Currency data — use the AUTHORITATIVE API, not an ad-hoc script
**`GET http://127.0.0.1:8768/api/uk/board`** (backed by `translation_v2.build_translation_board`; threshold ratio<0.60 OR metadata-stale → "stale"). It returns `totals`, per-`track` rollups, AND a per-track **`pages[]` work-list** — each page has `rel`, `status` (current/stale/missing), `ratio`, `en_words`, `uk_words`, `calque_review`. **This IS the ranked work-list — do not recompute with a python script.** (My s175 ad-hoc script used different thresholds; the API is canonical.)

Authoritative totals (s175): **total 1083 · current 152 (14%) · stale 297 · missing 634 · calque-reviewed 51 (5%).** Debt = 297 stale + 634 missing = **931 pages.**

Per-track to-do (stale+missing):

| track | current | stale | missing | to-do |
|---|---|---|---|---|
| prerequisites | 51 | 0 | 0 | **DONE ✓** (all 51 calque-reviewed) |
| **k8s** (CKA/CKAD/CKS/KCNA — cert flagship) | 49 | **160** | 52 | **212** |
| cloud | 12 | 78 | 14 | 92 |
| linux | 4 | 37 | 8 | 45 |
| platform | 25 | 20 | **241** | 261 |
| ai-ml-engineering | 0 | 0 | 142 | 142 |
| ai-history | 0 | 0 | 74 | 74 |
| on-premises | 7 | 2 | 58 | 60 |
| ai | 0 | 0 | 44 | 44 |
| root | 4 | 0 | 1 | 1 |

Measure by word-ratio + metadata-staleness, NOT file existence ([[feedback_translation_coverage_measure_staleness_not_existence]]).

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
The work-list IS `/api/uk/board` `pages[]` (filter `status != "current"`). Suggested order:
1. **k8s stale (160)** — refresh the cert flagship (CKA/CKAD/CKS/KCNA); highest learner value, existing structure to refresh (cheaper than net-new).
2. **k8s missing (52)** — complete the cert tracks.
3. **cloud stale (78) + linux stale (37)** — more refreshes.
4. Then the big **missing** blocks: platform (241), ai-ml-engineering (142), ai-history (74), on-premises (58), ai (44).
Rationale: stale-refresh > net-new for early wins; cert tracks > others for learner value. prerequisites is DONE — skip.

## Services / environment
Healthy — `dev` (:4333) + `api` (:8768) running; `sources` MCP live; `feedback` service stopped (irrelevant). **No restart needed** beyond the session refresh the user is doing.

## NEXT STEPS (fresh session)
1. Cold-start (orchestrator skill + this handoff).
2. Pull the **work-list from `/api/uk/board`** (`pages[]`, `status != "current"`) — already ranked by track + status; no script needed.
3. Build the per-page subagent prompt (pipeline above) + run a **2–3 page PILOT Workflow**; orchestrator reviews Ukrainian quality + calque-cleanliness.
4. Pilot good → **scale to the overnight swarm** (Workflow over the prioritized batch, worktree → per-track PRs, build-gated).

## State at handoff
- Open issues: **only #1911** (board cleaned to 1 in s175). #1876 SOLVED+closed; 8 triaged; #1823 mermaid fixed; 3 PRs merged (#2071/#2072/#2073). 355 review records now tracked; STATUS.md pruned 333→140 KB.
- Tree clean, main green. Only the retained `.worktrees/g2-craft` (not ours, #1623).

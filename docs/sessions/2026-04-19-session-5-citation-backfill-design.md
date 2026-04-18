---
title: Session 5 handoff — citation backfill design + truth-telling scorer
date: 2026-04-19
---

# What landed this session

## 1. Heuristic scorer now tells the truth (commit `c1220cd0`)

`scripts/local_api.py :: build_quality_scores` was rubber-stamping
4.71 across 726 modules without ever checking for a `## Sources`
section. Zero modules had citations; every score was fabricated.

The scorer now detects `## Sources` + markdown links; modules
without citations are clamped to 1.5 and severity `critical`, with
`no citations` leading `primary_issue`.

**Real baseline after the fix:**

| | Before | After |
|---|---|---|
| Average | 4.71 | 1.50 |
| Critical | 7 / 726 | 726 / 726 |

Also cleared four pre-existing Pyright errors in `local_api.py`
(asdict narrowing, tuple-index guard, dict-value widening, dead
`_v_always_fresh` stub).

**Test-helper breaking change:** `_seed_quality_module` gains
`citations: bool = True` default. Any future test that seeds an
excellent-severity module WITHOUT citations must explicitly opt out
with `citations=False`. The live-repo regression guard for #303 is
flipped to assert the new truth (those modules ARE critical until
citations land).

## 2. Contract unification for `## Sources` (commit `1918d262`)

`scripts/check_citations.py` looked for `## Sources`.
`scripts/v1_pipeline.py` injected `## Authoritative Sources`.
`docs/citation-upgrade-plan.md` canonicalizes `## Sources`. That
drift meant the deterministic checker silently failed on every
pipeline draft.

- `AUTHORITATIVE_SOURCES_BLOCK_TEMPLATE` now writes `## Sources`.
- `AUTHORITATIVE_SOURCES_HEADING_RE` accepts both forms so drafts
  already in flight keep verifying.
- CITE-step evidence strings + review prompt wording rewritten to
  `## Sources`.
- 6 test fixtures updated.

# The plan the next session picks up

User goal: citation-backfill across 726 modules. No humans in the
review loop. Strategy agreed: **surgical retrofit** (Strategy C) —
Codex adds `## Sources` + inline `[claim](url)` markers only;
existing prose, visuals, quiz, exercise are never touched.

## Consultation outcome (Gemini + Codex, both adversarial)

Their pushback rewrote four defaults I had:

1. **Citation floor.** Drop the ≥3-links numeric floor; it pads
   simple modules. Replace with claim-class rule: every war story,
   incident, statistic, standard/regulation, vendor capability
   claim, pricing/benchmark, security claim tied to a real event
   must have an inline citation. Teaching prose exempt. Zero-claim
   modules land with 1–2 Further Reading entries and no inline
   markers.
2. **Reviewer gate.** Split fetching from judgement. Python fetcher
   (with browser UA + redirect handling) caches page text and
   verifies 2xx/3xx per URL. LLM never touches the network; it reads
   module + ledger + cached text and emits a SUPPORTED/UNSUPPORTED
   label per claim row. 2-LLM unanimity on LABEL (not exact quote
   wording — that causes retry storms). 100% coverage, not 15%
   sampling, because there is no human tiebreaker.
3. **Seed strategy.** LLM parametric memory will hallucinate deep
   paths (`/docs/1.22/concepts/security`). Require a grounded search
   API (Tavily or equivalent) restricted to allowlist domains at
   query time. Allowlist tiered by claim class: standards →
   k8s.io/NIST/OWASP/MITRE/cncf.io; vendor capability/pricing →
   vendor docs; incidents/benchmarks → prefer neutral primary
   reporting over vendor blogs.
4. **Calibration.** ZTT 0.1 and DNS don't exercise claim extraction
   because they have no claims. Four-module calibration: ZTT 0.1
   (trivial), Linux DNS (medium), one CKS CVE-heavy (claim-dense
   security), one cloud vendor-claim-heavy (allowlist tiering
   stress).

Missing dimensions both agents surfaced:

5. **Contract freeze.** Done this session for the section header.
   Still to freeze: per-module seed path (current: per-track
   `docs/citation-seeds-{track}.md`; proposed: per-module
   `docs/citation-seeds/{track}/{module-key}.md`), ledger JSON
   schema, verifier JSON output.
6. **AST-aware diff linter.** Plain `git diff` rejects valid
   citation injections when a wrapped line reflows. Parse markdown
   to AST (remark in JS, mistletoe/markdown-it in Python). Allow
   only: new `## Sources` subtree + new link nodes wrapping existing
   inline text. Any other AST mutation → reject.

## Architecture for v2

Confirmed with `scripts/pipeline_v2/`: v2 is the orchestrator
(queue, budgets, leases, workers). It imports step functions from
`scripts/v1_pipeline.py`. Citation backfill lives in both layers:

- **v1 layer** — new step functions that do NOT regenerate content:
  - `step_research_citations(module_key) -> seed_path` — Codex reads
    module, queries grounded search against the allowlist, writes
    per-module seed file.
  - `step_inject_citations(module_path, seed_path) -> staging_path`
    — Codex appends `## Sources` + adds inline `[claim](url)`
    markers. Must produce a ledger JSON alongside.
  - `step_verify_citations(staging_path, ledger_path) -> verdict`
    — second LLM reads module + ledger + cached page text, emits
    label per row. Unanimity check.
  - `step_diff_lint(original_path, staging_path)` — AST diff gate.
- **v2 layer** — new phase + worker:
  - Phase name: `citation_backfill` (or split into
    `citation_research`, `citation_inject`, `citation_verify`).
  - Worker: `scripts/pipeline_v2/citation_worker.py` that picks up
    jobs from the queue, invokes the v1 steps, records ledger +
    verdicts, opens PR on success.
  - Failure modes: if research fails → module stays critical, not
    requeued (allowlist gap is a config issue, not a retry issue).
    If inject/verify fails → 3 retries then stop.

## Pre-Phase-0 blockers still open

**B2. Prove the fetcher** (blocker both Gemini + Codex named).
Before any LLM prompt is written, stand up
`scripts/fetch_citation.py` that takes `(url,)` and returns
`(status_code, extracted_text)`. Test against 5 URLs from each
allowlist tier. Bot-protected domains (NIST, some vendor docs,
Medium) MUST return text via browser UA + follow redirects. If the
fetcher is unreliable, the semantic gate is unviable.

**B3. Commit `docs/citation-trusted-domains.yaml`.** Tiered by
claim class per Codex's addendum.

**B4. Freeze the ledger schema.** Proposed row:
```json
{
  "claim_span": "line 42, chars 10-68",
  "claim_text": "NIST AI RMF 1.0 was published in January 2023",
  "url": "https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf",
  "quote_span": "page 1, paragraph 1",
  "quote_text": "This AI RMF 1.0 is released...",
  "claim_class": "standard",
  "support_label": "SUPPORTED",
  "verifier": "codex|opus|gemini-pro",
  "fetched_at": "2026-04-19T...",
  "fetch_status": 200
}
```

**B5. Decide: new v2 phase, or bolt onto existing write phase
with a `skip_regen=True` flag.** I lean new phase — cleaner
separation, simpler retry semantics, easier to gate on queue state.

## Execution order (user-confirmed this session)

Priority sequence across the 726:

1. ZTT (11 modules)
2. AI section (the `AI` track, 25 modules)
3. Prereqs (remaining tracks — Git Deep Dive, K8s Basics, Modern
   DevOps, Cloud Native 101, Philosophy & Design)
4. Cloud (85 modules)
5. AI/ML Engineering (separate track from AI; 4 modules per scorer)
6. Linux (Foundations + Operations + Security, 37 modules)
7. On-Premises
8. Platform (199 modules)
9. Certifications (CKA/CKAD/CKS/KCNA/KCSA — highest stakes, last)

User granted latitude to reorder; I'd keep as-is. Certs last is
right — they're the highest-stakes content and the pipeline should
be battle-hardened by the time it hits them.

## Next session: executable first task

1. Write `scripts/fetch_citation.py` (~150 LOC).
2. Commit `docs/citation-trusted-domains.yaml` (tiered allowlist).
3. Dry-run fetcher against 5 URLs × 4 tiers = 20 URLs. Document
   which domains need domain-specific fetch policy.
4. Only after fetcher is proven: design v2 `citation_worker` and
   v1 step functions; calibration on the 4 modules; scale to ZTT.

## Open questions for the user

- **Grounded search API:** Tavily ($) vs Google CSE ($) vs
  SerpAPI ($) vs a local `searxng`? Budget + reliability call.
- **Ledger storage:** per-module sibling file
  `{module}.citations.json`, or centralized SQLite in
  `.pipeline/citations.db`? I lean SQLite for queryability.
- **Budget ceiling per module run.** Codex 10x budget runs to
  2026-05-17. Back-of-envelope: 726 × (research + inject) × 2 LLM
  verifier passes ≈ 6 runs/module ≈ ~4,400 Codex runs. Feasible
  within 10x, but we should cap weekly spend and let the v2
  `control_plane.budgets` enforce it.

# Operator checklist

- ✅ Local API restarted this session — dashboard reflects the new
  critical counts.
- ✅ `.cache/` remains untracked (ignored).
- ⚠️ Pre-existing Pyright errors in `v1_pipeline.py` (lines 1613,
  1707, 2431, 2435, 2444, 2451, 2468, 3002, 3419, 3963) — NOT
  touched this session. The 3419 one (`Path | None` into
  `step_check_citations` which expects `Path`) will surface in the
  new citation phase unless fixed; worth an early fix in next
  session.
- ⚠️ 28 pre-existing test failures (`ModuleNotFoundError: No module
  named 'scripts'`) reproduce on `main` independently of this
  session's diff. They appear to be a test-runner sys.path
  config issue; separate cleanup.

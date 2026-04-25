# 2026-04-25 — Quality Improvement Action Plan

> Companion to [`2026-04-25-v2-smoke-green.md`](2026-04-25-v2-smoke-green.md) (the v2 pipeline handoff). This plan turns the gap-analysis findings into a sequenced, measurable program — one with progress visible at the briefing endpoint week-over-week, and quality improvement measurable on the rubric scorer and on real-LLM rubric scores.

## Context (today's baseline)

```
total modules:         726
average rubric:        2.65 / 5
critical (<2.0):       484  (66.7 %)
modules shipped via v2: 4   (1.1, 1.2, argo-events, plus 1.4 in flight)
```

Top critical-rubric buckets:

| # | Track                  | Critical |
|---|------------------------|---------:|
| 1 | Platform Disciplines   | 78       |
| 2 | Platform Toolkits      | 70       |
| 3 | CKA                    | 32       |
| 4 | CKS                    | 30       |
| 5 | Platform Foundations   | 30       |
| 6 | KCNA                   | 28       |
| 7 | KCSA                   | 26       |
| 8 | CKAD                   | 24       |

Pipeline-relevant constraints (from memory):
- **Codex**: 10x usage budget until 2026-05-17 (22 days runway).
- **Gemini**: scheduled downgrade 2026-05-05 (10 days). Audit-only and citation-verify run on Gemini, so audit work should weight earlier in the timeline.
- **Worker cap**: hard 3 (Gemini 429s above that). Default 1.
- **Writer policy** (decided this session): codex-only until claude-as-writer length-compliance is investigated separately. Codex hits ~1500–2000 lines reliably; claude lands ~440–800 even after the print-mode fix.

## Goal & success metrics

> **Updated after codex + gemini cross-family review** (both verdicts: NEEDS_REWORK / NEEDS_CHANGES). Original 4-week targets were mathematically inconsistent (484 → 200 critical needs 284 to exit, but plan only committed 120 rewrites; 2.65 → 3.40 average needs 545 rubric-points but 120 rewrites yield ~360). Replaced with throughput-anchored targets recalibrated after one stable workers=3 day.

The headline KPI is **modules verified-shipped via v2** — not `critical_count`, because the heuristic scorer is gameable per `reference_rubric_heuristic_structural.md` (structural padding can drop the count without real teaching gain). `critical_count` and `average rubric` stay as derived signals, with explicit anti-gaming sampling.

| Metric                                  | Today | Phase-A end (~7d) | Phase-B end (~10d) | Phase-D end (~30d, observed-throughput) |
|-----------------------------------------|------:|-------------------:|--------------------:|-------:|
| Verified-shipped modules (v2 + greenfield) | 4 | 15 (cluster + greenfield) | 34 (incl. AUDITED queue drain) | 60–90 (with 1.5× friction) |
| Spot-check rubric-delta sample           | n/a | 2 of 11    | 6 of 19              | 12 of 26+              |
| `critical_count`                          | 484 | ≤478 (–6, MLOps cluster) | ≤460 | ≤390 (estimate, depends on heuristic noise) |
| `average rubric`                          | 2.65 | ~2.67 | ~2.72 | ~2.85 |
| MLOps cluster modules at critical         | 7 | 0    | 0                    | 0                      |
| Greenfield modules added                  | 0 | 4 (KServe/Seldon/BentoML/bare-metal MLOps) | 4 | 8–12 (E.1 partial) |
| Teaching-rubric spot-checks/week (real-LLM scored vs `docs/quality-rubric.md`; pass = ≥33/40 sum AND every dim ≥4) | 0 | ≥5/wk | ≥5/wk | ≥5/wk |
| UK net-new debt (EN-rewritten, UK-stale)  | 0 | tracked in `STATUS.md` | tracked in `STATUS.md` | re-synced at end of each track's D-pass |

**Anti-gaming gate** (per codex review): every batch of 10 rewrites samples 2 modules for a real-LLM rubric delta vs the pre-rewrite baseline. If sampled modules show heuristic-up but teaching-flat, **pause the batch and investigate the prompt**. Sample size is ~20 % of rewrites, which both reviewers called the right ratio.

**Why teaching-rubric spot-checks are a separate metric** (per `reference_rubric_heuristic_structural.md`): the heuristic scorer at `/api/quality/scores` is a regex scan for quiz/exercise/diagram/Sources presence, NOT a teaching-quality measurement. A "critical" score often means missing Sources, not bad teaching. Conversely, a non-critical score can hide a listicle. Fridays we draw 5 random modules from the week's shipped batch and run a real-LLM rubric scoring against `docs/quality-rubric.md` — pass requires ≥33/40 sum AND every dimension ≥4. Failures route to immediate re-write the next Monday.

**Visibility cadence**: dump `critical_count` + `average rubric` + `modules-verified-shipped` at the start and end of every session into `STATUS.md`. Weekly: write to a `docs/quality-progress.tsv` ledger so the curve is queryable without re-walking git log.

## Phases

The plan is six phases, sequenced by leverage. Each phase has an exit criterion that's checkable from a single API call or `git log` query.

### Phase A — MLOps interview track (priority lane, this week)

Two threads run in parallel — one for existing-but-thin modules, one for genuine missing content.

**A.1 Rewrite the existing MLOps cluster** (7 modules at score 1.5):
- `Platform Disciplines: MLOps Fundamentals`
- `Platform Disciplines: Feature Engineering & Stores`
- `Platform Disciplines: Model Training & Experimentation`
- `Platform Disciplines: Model Serving & Inference`
- `Platform Disciplines: Model Monitoring & Observability`
- `Platform Disciplines: ML Pipelines & Automation`
- `On-Premises Ai Ml Infrastructure: Private MLOps Platform`

Method: `pipeline run --only <slug...>` then `backfill-pending`. Codex writer, claude reviewer. Estimated wall-time 1.5–2 hours at workers=1, 30–45 min at workers=3.

**A.2 Greenfield write the four missing MLOps modules**:
- KServe deep-dive
- Seldon Core deep-dive
- BentoML deep-dive
- Bare-metal MLOps end-to-end recipe (RKE2 + GPU operator + Kubeflow + storage)

Method: not pipeline-able (no module to rewrite). Use `scripts/prompts/module-writer.md` as the prompt; codex drafts + cross-family review, then run citation_backfill on each. Per codex review: realistic estimate is **8–12 wall-hours** for four modules including duplicate-detection, nav/frontmatter placement, source quality verification, build validation, and review iteration — NOT 2-3 hours.

**Exit criterion (Phase A)**: 0 MLOps cluster modules at critical, 4 new MLOps modules in `src/content/docs/`. MLOps cluster average rubric ≥ 4.0.

### Phase B — Drain the AUDITED queue (this week)

19 modules are already AUDITED but unrouted. They're the cheapest wins because the audit step is paid.

Method: `pipeline run --workers 1` (no `--only` flag — run all 19). Then `pipeline backfill-pending`.

Estimated wall-time: ~3 hours at workers=1, ~1 hour at workers=3.

**Cross-family review** (per `reference_review_protocol.md` and `feedback_review_policy.md`): mandatory before commit. Each codex-authored module gets a claude reviewer; reviews are filed in `/api/reviews` before the batch is "shipped." Tests-passing ≠ review.

**Exit criterion (Phase B)**: AUDITED count = 0; +19 to `quality(rewrite)` commits; all 19 reviews present in `/api/reviews`.

### Phase C — Mass-audit the 721 UNAUDITED (HARD GATE before D)

Audit tags every module with a teaching score and gaps via Gemini. Many modules will route to `CITATION_CLEANUP_ONLY` (already ≥4.0 teaching), which is a fast path — no rewrite, just verify & clean Sources.

**Two hard constraints** (per gemini review):

1. **Phase C blocks Phase D entirely.** D's "worst-first by audit teaching_score" ordering can't be available without C done. Don't start D rewrites concurrent with the mass-audit.
2. **Phase C must finish by 2026-05-05** (Gemini downgrade) or each subsequent audit-style call becomes 10× more expensive / slower. Citation verification and review steps in A/B/D are *also* on Gemini, but their per-module cost is much smaller than a full audit — the audit batch is the priority.

Method: `pipeline audit --workers 1` (audit-only batch). At ~140 s/module that's ~28 wall-hours raw; with the 1.5× friction multiplier (rate-limit pauses, retry on 429, dispatcher unavailability) plan for **40–45 wall-hours**, chunked into ~6-hour overnight runs over 7–8 nights.

**While Phase C runs**, A.1 and A.2 can still proceed because: A.1 modules are already AUDITED (Gemini step is paid); A.2 modules don't enter audit at all (greenfield writing skips it). Phase B ALSO runs against already-AUDITED modules. So A and B don't contend on the audit queue. They DO contend on the citation-verify Gemini calls — accept that the per-batch citation_verify will run slightly slower while the audit pool is hot.

Output: every module has `audit.teaching_score` populated. The `route` step then sorts them into `rewrite | structural | citation_cleanup_only | skip`.

**Exit criterion (Phase C)**: UNAUDITED count = 0, and audit run completed before May 5 09:00 local.

### Phase D — Critical-rubric blitz on the full backlog (after Phase C)

After Phase C, the routing decisions are made. **Ordering** (per gemini review — fixes the KPI/sorting disconnect): filter the backlog to **heuristic-rubric < 2.0 AND audit teaching_score < 4.0**, then sort that sub-list by worst teaching_score. This both moves the headline KPI and concentrates rewrites where teaching is genuinely thin.

Method: `pipeline run --workers 3` (or 1 if hitting rate windows). Continuous batches with overnight runs. After every batch: `pipeline backfill-pending` and the anti-gaming sample (2 of every 10 rewrites get a real-LLM rubric delta check).

**Cross-family review enforcement** (per `reference_review_protocol.md` and `feedback_review_policy.md`): mandatory on every rewrite. Codex-authored modules get a claude reviewer; reviews filed in `/api/reviews` before the batch is "shipped." A batch with any unfiled review is paused, not committed. Self-smoke ≠ review.

**Citation verify-or-remove gate** (per `feedback_citation_verify_or_remove.md`): during `pipeline backfill-pending`, citations classified anything other than `supports` (i.e., `partial`, `no`, `fetch_fail`, `ambiguous`) are **removed**, not retained. Unverified = lie. Burden of proof is on keeping the citation, not on removing it.

**UK translation re-sync** (Phase D.5 annotation): each rewritten EN module flags its `uk/` counterpart for re-sync. Net-new UK debt (EN-rewritten + UK-stale) is tracked in `STATUS.md` per session. Bulk `uk_sync` runs at the end of each track's D-pass — not per module — to amortize Gemini-translator dispatch overhead. Of the 484 critical EN modules, the subset with UK counterparts is concentrated in CKA/CKAD/CKS/Prerequisites (~110–140 modules estimated; verify with `git ls-files src/content/docs/uk/` against critical list before D starts).

Track-prioritization within the filter:
1. CKA / CKAD / CKS (certs the user already cares about — 86 critical combined)
2. Platform Disciplines + Toolkits (148 combined; the bulk of the backlog)
3. KCNA / KCSA (54 combined)
4. Platform Foundations (30)

**Throughput estimate (post-review, anchored on observed)**: codex 5-min writes + 4-min surrounding stages = ~9 min/module raw. With the 1.5× friction multiplier (queue failures, review rejects, citation backfill retries, build/site-health gates), realistic per-module wall-time is ~14 min. With workers=3 cap and contention, plan **~5 min wall-time per module** at peak. Daily processing floor: **30 verified-shipped modules/day**.

That floor over 14 working days yields ~420 attempted, ~370 verified-shipped (10–12 % failure rate per the rubric retry path). Realistic Phase D outcome: **300–400 modules through, ~20 % of the headline KPI fall (484 → 380–400)**, NOT 484 → 200.

**Budget check**: 484 codex writes through 2026-05-17 (22 days). At 30 modules/day × 22 days = 660 module-budget — plenty of headroom even at 1.5× per-module cost. The constraint is wall-time and operator attention, not budget.

**Exit criterion (Phase D)**: 250+ verified-shipped modules through Phase D; `critical_count` ≤ 380; anti-gaming sample shows ≥85 % real-rubric improvement on rewrites.

### Phase E — Greenfield expansion (parallel to D, finish after)

Two sub-tracks, both greenfield:

**E.1 — Verify-and-fill 2026-03-24 expansion plan**:
- Release Engineering (5)
- Chaos Engineering (5)
- FinOps expansion (Kubecost/OpenCost, showback/chargeback, cost-aware architecture, FinOps culture)
- Engineering Leadership (incident command, blameless postmortems, on-call, ADRs/RFCs, stakeholder mgmt)
- Advanced Networking (DNS at scale, CDN/edge, WAF/DDoS, BGP, IPv6/dual-stack)
- Data Engineering on K8s (Kafka/Strimzi, Spark operator, Flink operator, lakehouse, real-time ML)
- Extending K8s expansion (CRD advanced, Kubebuilder controllers, controller testing, admission webhooks, API aggregation, scheduler plugins)
- eBPF foundation, Edge K8s

First step is **verification**: walk the existing index files, mark which titles already shipped, write only the deltas. Don't burn cycles on duplicates.

**E.2 — On-prem expansion** (per `project_onprem_vision.md`):
- VMware Tanzu, OpenStack on K8s, Gardener, private LLM hosting, MetalLB / kube-vip / BGP
- Bare-metal observability stack
- Multi-cluster on-prem with Karmada / Liqo

**Exit criterion (Phase E)**: ≥30 new modules shipped; on-prem track and Platform Disciplines / Toolkits no longer dominate the critical bucket.

### Phase F — Lab quality audit (#179, parallel)

Open since before this session. The "explanation → can-do-under-exam-pressure" gap. Not pipeline-able.

Method: a separate batch script that reads each lab, scores it on a small lab rubric (clear setup + acceptance criteria + clean teardown + realistic time estimate), and emits a punch list. Then expand or rewrite labs in priority order.

Out of scope for the current quality-pipeline plan — but flagged here so it's not forgotten.

**Exit criterion (Phase F)**: every CKA/CKAD/CKS lab scored; top-quartile-worst labs rewritten.

## Sequencing summary

```
Week 1 (Apr 25 – May 02):  A.1 + A.2 + B   (MLOps cluster shipped, AUDITED queue drained)
Week 1–2 (Apr 25 – May 05):  C            (mass-audit before Gemini downgrade)
Week 2–4 (May 02 – May 17):  D            (critical-rubric blitz)
Week 4+ (May 17 onward):   E + F          (greenfield + lab audit)
```

Phase C must overlap A/B because of the Gemini downgrade deadline. Phases A and B can run sequentially or in parallel — A wins on personal-relevance, B wins on cheapness.

## Risk register

| Risk                                       | Mitigation                                                                  |
|--------------------------------------------|-----------------------------------------------------------------------------|
| Codex print-mode failure on a module       | Already handled — diag persisted; reset-stage and retry                     |
| Claude length-compliance                   | Already handled this session — codex-only until investigated                |
| Gemini downgrade hits mid-Phase C          | Front-load audit before May 5; be willing to switch audit to claude         |
| `critical_count` heuristic vs real teaching| Real-LLM rubric is the truth — spot-check 5 modules / week to calibrate     |
| Operator (us) burns out                    | Cadence is overnight batches, not interactive; review every morning         |
| Site build breaks mid-batch                | After every batch: `npm run build` + `.venv/bin/python scripts/check_site_health.py`  |

## Batch rollback gate

A batch is **reverted** (via `git revert` of every commit in the batch, then modules re-routed individually for diagnosis) if any of the following triggers fire:

- (a) **>10 % of modules in the batch show rubric_score regression** vs the pre-batch snapshot from `/api/quality/scores`.
- (b) **Any module loses an ASCII or Mermaid block** in the diff (per the visual-aid preservation gate, see Tracking & cadence). Visual aids are protected assets per `module-quality.md` ("NEVER remove or simplify existing visual aids").
- (c) **`npm run build` fails OR `.venv/bin/python scripts/check_site_health.py` reports new errors** post-batch.
- (d) **>20 % of citations in the batch route to `remove`** during `pipeline backfill-pending`. A high removal rate suggests Stage 4 (citation research) is misfiring on that batch — fix before continuing.

When a rollback fires, the modules are not lost — they're re-routed individually so the failure is isolated. A second consecutive batch rollback on the same track triggers a full pipeline pause until the failure mode is diagnosed (likely a prompt regression or dispatcher change).

## Tracking & cadence

**Daily** (start of session):
1. `curl -s http://127.0.0.1:8768/api/briefing/session?compact=1`
2. `curl -s http://127.0.0.1:8768/api/quality/scores | jq '{average, critical_count}'`
3. `git log --since=yesterday --grep='quality(' --oneline | wc -l` (modules shipped yesterday)
4. **Codex usage delta vs 22-day runway** to 2026-05-17 — if projected daily-burn × days-remaining > remaining budget, drop workers to 1 and pause greenfield (Phase E) until Phase D completes. Reference `project_budget_and_delegation.md`.

**Weekly** (Sunday): write the three values to a row in a `docs/quality-progress.tsv` ledger so the curve is queryable without re-walking git log.

**Friday teaching spot-check**: pull 5 random modules from that week's `quality(rewrite)` commits and run a real-LLM rubric scoring (per `docs/quality-rubric.md`). Pass requires ≥33/40 sum AND every dimension ≥4. Failures route to immediate re-write the next Monday, ahead of any new track. Fewer than 5 shipped that week → spot-check whatever did ship.

**Per-batch** (each `pipeline run` invocation):
- Pre: `npm run build` succeeds; record per-module `ascii_blocks_pre` and `mermaid_blocks_pre` counts (simple `grep -c '^```'` and `grep -c '^```mermaid'` against each target file).
- Post: `npm run build` succeeds + `.venv/bin/python scripts/check_site_health.py` 0 errors.
- Post: re-count `ascii_blocks_post` / `mermaid_blocks_post`. **Any module with a decrease must be reverted and re-routed** — visual-aid regression is a hard fail per `module-quality.md`.
- Post: file each module's cross-family review in `/api/reviews` before the batch is "shipped."

## Decisions (already made — kept here for traceability)

- **Worker count** — start at 1 for the first batch of each phase, ramp to 3 once that batch lands clean (per `feedback_batch_worker_cap.md`).
- **Claude-as-writer** — codex-only writer until Phase D completes; revisit only if codex budget runs out before 2026-05-17. The print-mode `Task` fix in `ba32654b` makes claude technically reliable, but codex hits 1500–2000 lines consistently while claude lands at ~440 — length consistency wins for a batch program.

## Open decisions for the user

1. **Budget cap per phase**: codex has the 10x budget until 2026-05-17. Should we set a soft daily cap (e.g., ~30 modules/day matching the Phase D floor) to spread runway, or burn at full throttle and re-budget if we run out?
2. **Lab audit start date** (Phase F): block on Phase D completion, or carve a few hours/week starting now?

---

## What's been done this session that feeds this plan

- v2 pipeline cleanup commit (`2e3c48b0`) — diagnostic file isolation, fixes `pipeline status`.
- Module 1.2 shipped (`d4426d19` + `b9fc1e49`) — codex writer, rubric 4.75, 2202 lines, 3 Sources.
- **Claude-writer print-mode fix** (`ba32654b`) — `Task` added to `--disallowedTools`. Empirically validated on 1.4. Major reliability unblock for any future return to claude-writer rotation.
- Module 1.4 (claude-written, 440 lines) reverted (`08a5e693` + `7ba0da47`) — below 600-line minimum; codex re-run in flight.
- Memory: `project_topical_gap_analysis.md` saved.

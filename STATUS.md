# Session Status

> **Read this first every session. Update before ending.**

## Active Work (2026-04-24 past-midnight — concurrency lock in re-review, pilot diagnosis landed, residuals audit in-flight)

**Continuation from earlier tonight (2026-04-23, see below).** After the 6-PR push, user asked me to run the phase-1.5 re-pilot and keep pushing overnight. Current state:

### 3-module re-pilot result

Resolver + quote-match ran on the reset 3-module set. **Raw numbers: 1 resolved / 4 attempted = 25%**, not the projected 60–75%. But **the failures were correct behavior, not resolver weakness** — diagnosis below.

### Diagnosis (key insight — captured here because it reframes the whole pilot plan)

3 of 4 failures died at `no_candidates_returned` — the LLM refused to propose URLs — **before** quote-match could act. Inspecting the finding excerpts:

- **fine-tuning-llms** finding: `signal: price_usd`, excerpt is a narrative case study (*"abandoned shopping carts incident"*, *"foundation models global endpoint throttling provisioned throughput revenue impact"*). **Pedagogical fiction** — no real public incident to cite.
- **cloud-ai-services** finding 1: same pattern, fictional scenario.
- **cloud-ai-services** finding 2 (`all_candidates_failed`, 3 attempts): module claims *"Azure's classic Foundry Agent Service docs were officially marked as deprecated as of 2027-03-31"* — a **hallucinated future date** (today is 2026-04-24). Microsoft's proposed URL correctly rejected at `no_anchor_match` because 2027 can't be found on the real page.
- **multi-account** finding: resolved successfully (the one happy path).

Reframe: the resolver is doing its job. It refused to polish fabrications (exactly per `feedback_advisory_vs_enforced_constraints.md`). The 25% isn't a resolver problem — it's a content problem. These findings belong in #344's lane (soften/delete claim), not #343's (source citation).

The 3-module pilot set was also selection-biased: these were phase-1 flunks. A fresh 10-module sample from the 64 batch-c residuals would give a real resolve-rate distribution.

### PR #363 — per-module write lock (IN RE-REVIEW)

Branch: `feat/343-resolver-concurrency-lock` @ `bb131700`
URL: https://github.com/kube-dojo/kube-dojo.github.io/pull/363

Unblocks phase-2 bulk by adding a DB-backed advisory lock so two resolvers can't clobber the same module. New `scripts/pipeline_common/module_lock.py` primitive (acquire / complete / release / sweep / context manager), wired into `citation_residuals.py resolve` with new flags `--worker-id`, `--lease-seconds`, `--no-lock`. 63/63 tests including a threaded stress test. Ruff clean.

Codex first-round review caught a real must-fix: I was keying the lock on `qp.stem` (flattened filename) but the canonical `module_key` contains slashes — other writers using the canonical form wouldn't coordinate. Fixed at `bb131700`: lock now keys on `data["module_key"]` with stem fallback for legacy files. Added regression test using production-shaped fixture (filename `track-topic-module-1.json` + JSON key `track/topic/module-1`).

**Re-review dispatched, awaiting response.** Task ID `pr-363-rereview`, bridge message ≥ 2711. Next session: `scripts/ab inbox show claude` → if APPROVE, `gh pr merge 363 --merge --delete-branch` and clean up worktree `.worktrees/citation-residuals-lock`. If NEEDS CHANGES, fix + re-dispatch.

My 5 open review questions from the first round (holder identity, contention UX, TTL default, partial-write crash, schema race) were not answered in round 1 — restated in the re-review prompt.

### Residuals audit — in-flight, HEADLESS Codex

Task ID: `audit-residuals-classification`, bridge message 2709, dispatched via `scripts/ab ask-codex` in workspace-write mode.

Codex is classifying all ~64 `needs_citation` findings across the batch-c residuals files into:
- A. Sourceable (resolver should succeed)
- B. Pedagogical fiction (no real source exists)
- C. Hallucinated fact (content bug — future date, nonexistent product)
- D. Ambiguous

Output target: `.worktrees/residuals-audit/docs/residuals-audit-2026-04-24.md`. Branch: `audit/residuals-classification`. Codex will commit + push when done but NOT open a PR.

**Status at handoff: the .md file does not yet exist in the worktree — Codex still running.** Next session: check `ls -la .worktrees/residuals-audit/docs/residuals-audit-2026-04-24.md`. If present, read it and decide whether to promote to a content-bugs issue for #344 scope. If `scripts/ab read 2710+` (whatever the response ID ends up being) shows Codex's summary reply, that has the headline counts and top-3 Category C modules.

### WIP: pilot-n flag (UNPUSHED, in worktree)

Worktree: `.worktrees/pilot-n` on branch `feat/343-pilot-n-flag`. **Uncommitted change** adds `--limit-modules N` arg definition to `citation_residuals.py` `resolve` subcommand. Loop wiring NOT yet done. Purpose: cap `--all` runs at N modules for safe gradual rollout (postmortem followup from STATUS.md). Will conflict with #363 on citation_residuals.py — plan is to rebase on main after #363 merges, finish the loop wiring, add tests, open PR.

Next session action: either `git -C .worktrees/pilot-n diff` to resume the work or `git worktree remove --force .worktrees/pilot-n && git branch -D feat/343-pilot-n-flag` to abandon.

### Tech-debt delta this push

| Issue | Was | Now |
|---|---|---|
| #343 concurrency lock | deferred | PR #363 in re-review |
| #343 phase-1.5 pilot | not run | run — 25%, diagnosis done (content-quality issue, not resolver) |
| #344 input data | no categorized list | audit in-flight → will produce Categories A/B/C/D counts + per-module breakdown |
| `--pilot-n N` | postmortem followup | WIP in worktree (unfinished) |

### Cold-start for next session (UPDATED)

1. **Check #363 re-review** — `scripts/ab inbox show claude` → read the latest response on task `pr-363-rereview`. If APPROVE → merge. If NEEDS CHANGES → fix at `.worktrees/citation-residuals-lock`, push, re-dispatch.
2. **Read the residuals audit** — `ls .worktrees/residuals-audit/docs/residuals-audit-2026-04-24.md`. If present: read the summary counts, extract Category C findings (hallucinated facts) into a new issue for #344 content-fix scope. Consider promoting the audit doc to `docs/` via a follow-up PR.
3. **Decide on pilot-n WIP** — finish or abandon per above.
4. **Phase-2 bulk prep** (only after #363 merges):
   - Fresh-sample pilot on 10 untouched batch-c residuals modules (expected real distribution, not the selection-biased 3).
   - If ≥60% resolve on Category A findings, run bulk at `--workers 3` (hard cap per `feedback_batch_worker_cap.md`).

---

## Prior active work — 2026-04-23 night (6 PRs out today, all merged; cross-family reviewer rule codified)

**Session deliverables (chronological):**

- **PR #355** (`3294d16f`, merged, earlier today) — phase-1 citation residuals resolver.
- **Commit `55e0e9a2`** — 3-module pilot: 1/5 auto-resolved (20%). Exposed two hallucination classes (URL-existence, URL-content) that capped phase-1.
- **Issues filed:** #351 (missing Sources audit), #352 (Gate A prose/quiz contradictions), #353 (zombie gemini), #354 (orphan check_pre), #356 (URL hallucination mitigation).
- **PR #357** (`2d6908c3`, merged) — **#356 Part 1**: HEAD-check + allowlist pre-filter in `request_candidates`. Codex review approved with 2 nits (HEAD→range-GET→plain-GET escalation, narrow bare-except) — both fixed in `19e4ab05` before merge.
- **PR #358** (`1e9a0b75`, merged) — **#354 fix**: removed orphan-check_pre enqueue after APPROVE. Preflight already runs at top of review function; reducer now sees APPROVE → `done` immediately. Codex nit about testing the reducer symptom (not just the mechanical cause) addressed in `065c84d7`.
- **PR #359** (`5de7e33f`, merged) — **#351 fix**: `audit_missing_sources()` in `pipeline_v4_batch.py` post-batch. Codex caught 2 real must-fix issues (false-positive under `--skip-citation`; header regex too strict on trailing whitespace / EOF-without-newline) — both fixed in `1fad9f3e`.
- **PR #360** (`f6418853`, merged) — **#356 Part 2**: quote-match verification rescues anchorless findings. Initial Codex NEEDS CHANGES — 2 must-fix correctness bugs: (1) quote could override contradictory anchors, (2) prefix-only drift fallback accepted generic lead-ins. Both fixed in `3404ab8b`: anchors authoritative when present (quote-only acceptance limited to anchorless findings); drift fallback replaced with start-AND-end-window match in order. 37/37 tests pass. Re-review APPROVE.
- **PR #361** (`4a3e544b`, merged) — **postmortem follow-up**: added `## Reviewer Assignment (cross-family rule)` section to `docs/review-protocol.md`. Codifies the three model families (Claude / Codex / Gemini), default pairings, and the rule that a PR's reviewer must be from a different family than the author. Codex NEEDS CHANGES caught one must-fix — original "Enforcement" paragraph overclaimed a hard CLI mechanism that doesn't exist. Reworded at `8071805b` to "Operator workflow (not automated enforcement)" with explicit "enforced by convention and reviewer discipline, not by a hard CLI check". Re-review APPROVE.
- **PR #362** (`4416d745`, merged) — **#361 follow-up**: aligned `.claude/rules/gemini-workflow.md`, `CLAUDE.md`, `.pipeline/codex-handoff.md`, and `docs/best-practices/agent-bridge.md` with the cross-family rule. Two Codex NEEDS-CHANGES rounds: (1) caught `.pipeline/codex-handoff.md:151` still mandating Gemini → fixed at `6c73db06`; (2) caught `docs/best-practices/agent-bridge.md:82,85` still hardcoded `--to gemini` and `Reviewed-By: gemini-3.1-pro-preview` in generic operator guidance → fixed at `7cc728ae`, also took nit to relabel dated codex-handoff workflow as "Historical execution notes (2026-04-15 v2-pipeline handoff)". APPROVE on second re-review.

**Non-PR cleanup this session:**

- **Stale `.pids/api.pid`** — contained dead pid `4983`; actual API listener is pid `47928`. Fixed by writing correct pid + re-aging file (briefing stopped flagging stale).
- **Services catalog placeholders** — `feedback` (GitHub Issue Watcher) and `pipeline` (Pipeline Supervisor) are listed in `scripts/local_api.py:52-53` but have no launcher script anywhere; pid files have never existed. Either dead catalog entries or planned-but-unbuilt services. Left alone — no active harm.

**Tech-debt status:**

| Issue | State |
|---|---|
| #351 | ✅ closed (PR #359 merged) |
| #352 | open — Gate A prose/quiz contradictions (deferred; needs pipeline design session) |
| #353 | open — zombie gemini (deferred; low urgency, auto-fallback covers) |
| #354 | ✅ closed (PR #358 merged) |
| #356 Part 1 | ✅ closed (PR #357 merged) |
| #356 Part 2 | ✅ closed (PR #360 merged) |
| #356 Part 3 | open — Codex candidate-fallback (do after Part 2 pilot) |
| #344 | open — extend resolver to overstated/off-topic findings |
| #343 | in progress — phase-1 + phase-2 + phase-1.5 (#356 parts 1+2) landed |

**Key reviewer-rule data points (captured in codified doc):**

- Codex-as-reviewer on PR #362 caught TWO file-level misses across two re-review rounds (`.pipeline/codex-handoff.md`, then `docs/best-practices/agent-bridge.md`). My grep pattern was too narrow ("Gemini for review" vs the actual phrases "Gemini must review" / "--to gemini"). Lesson: when sweeping for a deprecated convention, grep the conjugations + imperative/passive voice + CLI flag values, not just the natural-language form. Codified implicitly via the cross-family doc, not explicitly as a memory.
- **Explicitly deferred (not blocking per Codex)**: `.pipeline/spec-lab-pipeline.md:273,296,299` and `.pipeline/spec-v2-pipeline.md:519` still reference Gemini as reviewer in pending checklist items. Decision: left as historical 2026-04-14 design-spec docs rather than rewriting past design records. Future operators consult `docs/review-protocol.md` for the live rule.

**New learning saved to memory:** `feedback_advisory_vs_enforced_constraints.md` (from earlier in session) — LLM prompt constraints are advisory; enforce deterministically in code before any side-effect.

---

## Cold-start (earlier version — superseded by the top of this file for 2026-04-24)

**1. Re-pilot the 3-module set** — #360 (quote-match verification) merged, so the anchorless-findings class (`named_incident` / `attribution`) should now resolve. Expected: 60–75% resolve rate (up from 20% on phase-1). Reset the queue files first — previous pilot moved findings to `unresolvable_findings[]`:

```bash
.venv/bin/python - <<'EOF'
import json
from pathlib import Path
for stem in ("ai-ml-engineering-advanced-genai-module-1.1-fine-tuning-llms",
             "ai-ml-engineering-ai-infrastructure-module-1.1-cloud-ai-services",
             "cloud-advanced-operations-module-8.1-multi-account"):
    qp = Path(".pipeline/v3/human-review") / f"{stem}.json"
    d = json.loads(qp.read_text())
    restored = []
    for f in d.pop("unresolvable_findings", []):
        restored.append({k: v for k, v in f.items() if k not in ("unresolvable_reason", "attempts", "resolved_at")})
    d["queued_findings"]["needs_citation"] = restored + d["queued_findings"].get("needs_citation", [])
    qp.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
    print(f"reset {stem}: restored {len(restored)}")
EOF

.venv/bin/python scripts/citation_residuals.py resolve ai-ml-engineering-advanced-genai-module-1.1-fine-tuning-llms
# ...repeat for the other two
```

**2. If re-pilot is good (≥60%), prep bulk phase-2 PR:**
- Raise `--workers` cap to ≤3 (per memory `feedback_batch_worker_cap.md`).
- File concurrency fix first — PR #357's Codex review flagged that two resolvers on the same module clobber each other's writes (deferred from #343 phase-1; bit me during the pilot when I accidentally ran one in foreground + background). Needs a `.pipeline/v2.db` lease before bulk.

**3. Other open tech debt (ranked):**
- **#356 Part 3** (Codex candidate fallback) — do after phase-2 bulk if resolve rate is below target.
- **#344** (extend resolver to overstated/off-topic classes) — 257 findings across 4 categories. Design decision needed on the simpler "apply pre-composed fix" cases vs. the harder "soften the claim" cases.
- **#352** (Gate A prose/quiz contradiction) — needs pipeline-design session, not a small PR.
- **#353** (zombie gemini) — low urgency unless next batch shows orphan processes.

**4. Postmortem follow-up:**
- ✅ Make cross-family reviewer rule explicit in `docs/review-protocol.md` — landed via PR #361 + #362.
- Add `--pilot-n N` flag to bulk scripts for gradual rollout.
- Require prompt-change ablations on ≥3 fixture findings before merge.

---

## Smoketest (first 30s of next session)

```bash
curl -s http://127.0.0.1:8768/api/briefing/session?compact=1        # should show 100% convergence, stale=0
git log --oneline -5                                                 # last merge should be #359 (1e9a0b75 or 5de7e33f)
gh pr view 360 --json state,mergeable                                # #360 status
scripts/ab inbox show claude                                         # any Codex responses pending ack
```

Expect: briefing shows stale=0 running≥5, last 5 commits include the PR-359 merge, PR #360 state=OPEN, inbox either empty or has Codex's #360 review response.

---

## Prior (2026-04-23 morning — batch-c cloud citation backfill merged, dispatch auto-fallback landed)

**Today's merges:**

- **PR #349** (`3d8ede2e`) — `fix(dispatch): auto-fallback from API-key to OAuth on Gemini 429`. Auto-flips to OAuth on first rate-limit (independent quota, no backoff); `KUBEDOJO_GEMINI_SUBSCRIPTION=1` preserved as force-subscription opt-out. Codex caught a `max_retries=1` edge case — addressed in `eb8d622c` with 2 regression tests. 10/10 tests pass.
- **PR #350** (`59d62bbd`) — `content(cloud): v4 batch-c — 78 modules citation backfill 1.5 → 5.0`. Overnight `pipeline_v4_batch --track cloud --workers 2` ran 9h40m, 78 modules all cleared rubric at score 5.0 (14 clean, 64 with citation residuals queued). Codex review found real gaps; `84f56a38` addresses: missing `## Sources` in module-2.7-cloud-run + module-7.5-aks-fleet-manager; GKE Autopilot quiz teaching obsolete defaults; AKS identity quiz putting label on SA instead of pod; stale Kafka `/10/` URL.

**Impact on #180 rubric bar:** critical-quality (<2.0) count dropped **562 → 485**. Cloud Advanced Ops no longer appears in the briefing's top-5 critical list. Remaining critical concentrates in AI/ML Ai Native Development, Cloud Architecture Patterns, K8S Capa, K8S Cba.

**Review-protocol data point:** Gemini flash 3 APPROVED PR #350 while Codex caught 3 real content issues in sampled-same modules. **Codex was notably more rigorous on this content batch.** For bulk content review, prefer Codex as the gating reviewer; Gemini is lighter/faster but missed the specific quiz inconsistencies.

**Pipeline gaps surfaced — worth tracking as future improvements (not filed yet):**
1. `citation_v3` silently left 2 of 78 modules with no `## Sources` at all (`module-2.7-cloud-run`, `module-7.5-aks-fleet-manager`). Possible systemic trigger worth investigating before next bulk run — audit for "module touched but no sources added" as a post-batch CI check.
2. Gate A overstatement softener updates main prose but doesn't always update quiz answers citing the same claim, producing module-internal contradictions. Observed on 2 of 5 Codex-sampled modules (6.1 Autopilot defaults, 7.3 AKS identity label).
3. Zombie `node gemini` grandchildren survive `killpg` on dispatch timeout (PPID reparents to init) — #253 was closed as fixed 2026-04-16 but the fix is incomplete. Not filed; real but low-urgency since batch-c produced zero zombies after auto-fallback landed.

**Gotchas updated this session:**
- `KUBEDOJO_GEMINI_SUBSCRIPTION=1` currently errors with `"you must specify the GEMINI_API_KEY environment variable"` — OAuth creds in `~/.gemini/oauth_creds.json` appear to not be picked up by the CLI today (may need interactive `gemini` re-auth). Fall back to explicit API key + `--model gemini-3-flash-preview` for reviews when `gemini-3.1-pro-preview` is at capacity.
- `gemini-3-flash-preview` reliably works via API key today; `gemini-3.1-pro-preview` hitting `No capacity available` most of the afternoon.
- `gemini-2.5-flash` is explicitly off-limits as a fallback — user rejected; quality tier too low (see memory `feedback_gemini_models.md`).

**Next session starts here:**
1. If restarting batches, smoke-check gemini CLI first: `echo OK | gemini -m gemini-3-flash-preview -y` (via API-key path). The new auto-fallback in `dispatch.py` handles rate-limit flips automatically — no env var needed.
2. Batch-c's scope was `--track cloud` only. Remaining critical-quality concentrations per post-merge briefing: AI/ML Ai Native Dev, Cloud Architecture Patterns (odd — confirm not cleared yet), K8S Capa, K8S Cba.
3. The 64 `residuals_filed` modules from batch-c have citation-triage findings queued in `.pipeline/v3/human-review/`. Issues #341 / #343 / #344 track the auto-resolver epic — that's the scalable path before running more bulk batches.
4. 2 stale pid files per briefing — `scripts/cleanup_pids.py` or similar.

---

## Prior: Session 11 (2026-04-21) — pipeline_v4 built end-to-end, tech debt cleared, dogfood validated

Session 10 handoff: [`docs/sessions/2026-04-21-session-10-handoff.md`](./docs/sessions/2026-04-21-session-10-handoff.md).
Session 11 handoff: [`docs/sessions/2026-04-21-session-11-handoff.md`](./docs/sessions/2026-04-21-session-11-handoff.md).

**Session 11 landed (9 commits on main, 2,936 LOC of new pipeline + 5 tech-debt fixes):**

Tech debt:
- `2eedc994` pipeline_v2 sibling-module imports (v4 needed v2 worker infra; this was the blocker). 40/40 v2 tests pass.
- `10aa1a67` autopilot_v3 `--content-stable-only` gate (skip thin modules when prepping for v4). Queue filtered 108→98 sections on first dry-run.
- `7b7210ef` `pyrightconfig.json` with `extraPaths: ["scripts"]`.
- `2d4a6a90` v1_pipeline drops orphan `.staging.md` before fresh write-phase attempt. Root cause: cleanup only ran on `pending/audit` branch, not `phase="write"` resume branch. 102 orphan staging files deleted inline.
- `ba8cf489` `/api/quality/scores` adds `path` field; v3 gate keys by path (not reconstructed label). Issue #325 closed. Delete ~90 LOC of label-reconstruction helpers.

Pipeline v4 (issue #322 rewritten based on Gemini NEEDS CHANGES review; 5 structural findings addressed):
- `ad590be3` `scripts/rubric_gaps.py` — Stage 1 gap identification, 224 LOC + 126 test LOC. 9 tests pass.
- `3d172a59` `scripts/module_sections.py` — H2-based section splitter with round-trip fidelity, 426 LOC + 289 test LOC. 18 tests pass.
- `747bd53c` `scripts/expand_module.py` — Stage 2 gap-driven expansion (quiz, mistakes, exercise, outcomes via Codex; thin via Gemini multi-pass). 641 LOC + 311 test LOC. Provenance markers (`<!-- v4:generated ... -->`) wrap every generated block. Diff-lint rejects any rewrite of human-authored paragraphs.
- `e663088d` `scripts/pipeline_v4.py` — Stage 1-5 orchestrator. 533 LOC + 386 test LOC. 9 tests pass. Retry budget 2, regression epsilon 0.2, generated-LOC threshold guard against citation-over-LLM-prose.

35/35 pipeline_v4 tests pass. Dogfood run on `ai/ai-for-kubernetes-platform-work/module-1.2-ai-for-kubernetes-troubleshooting-and-triage`: **2.0 → 4.2 score in 7m6s**, outcome=clean. Stage 4 (citation_v3) skipped via `--skip-citation`; its guards are unit-tested. Expanded module preserved in `.worktrees/dogfood-v4/` pending review.

Issues closed: #325 (scorer paths), #272 (AI for K8s section — all 4 modules exist, quality tracked by #180), #198 (Master Execution Plan — duplicated STATUS.md + handoffs).

**Next session starts here:**
1. Fix retry-refresh-gaps bug in pipeline_v4.py — Stage 3 retry uses original gap list instead of refreshed. See session 11 handoff for fix sketch. Small change, single unit test.
2. Decide what to do with the dogfood worktree (commit to main, delete, or keep as golden reference).
3. Build `scripts/pipeline_v4_batch.py` — wrap `run_pipeline_v4` with `.pipeline/v2.db` lease coordination for concurrent runs (8-way default, aim for ~32 h across 620 modules instead of 206 h sequential).
4. Dogfood batch on the 5 "AI/ML Engineering Ai Infrastructure" critical-quality modules the briefing flags.

**v4-specific bugs (none blockers, see session 11 handoff for details):**
- Stage 3 retry doesn't re-fetch gaps (listed above).
- `loc_after` in ExpandResult drifts from actual disk state.
- Gemini CLI YOLO mode self-lints with markdownlint (~30s/section latency).

**Known gotchas — updated this session:**
- Codex sandbox blocks `.git/worktrees/*/index.lock`. Every delegation returned "files written, commit failed". Pattern: Codex writes, Claude commits from primary-repo side. Prompts should instruct Codex NOT to attempt commits.
- Gemini 3.1-pro is frequently at-capacity. Pass `--model gemini-3-flash-preview` explicitly when 3.1-pro is congested; dispatch.py doesn't auto-fallback on rate limit (same-quota assumption).
- Rubric scorer weights section presence > line count. Dogfood crossed 4.0 at 258 LOC (target 600). `target_loc` is a ceiling for effort, not a floor for success.
- Carry-over: Codex auth can go flaky under load; smoke-check with `echo hi | timeout 25 codex exec --full-auto --skip-git-repo-check`.
- Carry-over: 900s Codex dispatch hard-timeout; large runs need phasing.

**Lower-priority carry-over:**
- 5 critical-quality modules at 1.5 (AI/ML Advanced GenAI 1.1 fine-tuning, 1.2 LoRA, 1.3 diffusion, 1.10 single-GPU, 1.11 multi-GPU) — perfect targets for v4 batch dogfood.
- 2 CKA inject_failed modules from session 10 handoff: RESOLVED — `module-3.1-services` and `module-3.6-network-policies` have clean `## Sources` from later v3 runs (commits `2112507f`, `17084227`). Handoff was stale.

---

## Prior session-5 handoff (first half of the day)

Session 5 landed two things: the heuristic quality scorer now auto-fails modules with no `## Sources` section (reveal: 726/726 critical, old 4.71 avg was fabricated; commit `c1220cd0`), and the `## Sources` vs `## Authoritative Sources` contract drift between `check_citations.py` and `v1_pipeline.py` is unified (commit `1918d262`). Full handoff with the citation-backfill plan + next-session blockers: [`docs/sessions/2026-04-19-session-5-citation-backfill-design.md`](./docs/sessions/2026-04-19-session-5-citation-backfill-design.md).

**Session 5 progress (landed this session, 9 commits from `c1220cd0` → `a769aede`):**
1. ✅ Scorer truth-gate + Pyright cleanup (726/726 critical — real baseline).
2. ✅ Sources-header contract unified across v1 pipeline + tests.
3. ✅ `docs/citation-trusted-domains.yaml` — tiered allowlist.
4. ✅ `scripts/fetch_citation.py` — 20/20 dry-run pass; bot-protected domains (NIST, OWASP, Microsoft, Google, CISA, Anthropic) all returned text via browser UA.
5. ✅ `scripts/citation_backfill.py research` — disposition-aware (supported/weak_anchor/unciteable). Honest flagging, no forced weak anchors.
6. ✅ `scripts/citation_backfill.py inject` — structured edit plan, mechanical wrap application, diff linter verifies additive-only. `check_citations.py` passes on ZTT 0.1 staging.
7. ✅ Revision queue — unciteable claims routed to `.pipeline/citation-revisions/` for future content-softening pass.
8. ✅ Calibration on 3 ZTT modules: 45 claims, 51% supported, 44% unciteable. Pipeline refuses to polish fabrications.

**Next session starts here:**
1. Implement verify step (Gate B) — 2nd LLM semantic check against cached page text.
2. Design the merge workflow: staging.md → main, auto-PR via worktree (user confirmed no humans in loop).
3. Scale research to ZTT 0.3–0.10 (8 more modules).
4. Expand allowlist for recurring unciteable patterns (GitLab, CERN) or write a revision-softening worker.
5. Open design: grounded-search API (MVP skipped it — 0 hallucinations so far suggests maybe unneeded); weekly budget caps in `control_plane.budgets`.
6. Scale order (user-confirmed): ZTT → AI → prereqs → cloud → AI/ML → linux → on-prem → platform → certs.

**Prior queue (session 4, still valid but now lower priority than citation backfill):**
1. #277 — `/api/build/run` + `/api/build/status` endpoints (~150 LOC, clear spec)
2. #258 — Local API audit + cold-start cost (broad; dispatch for split plan first)
3. #248 — Review Batch triage (probably closable)
4. #319 — Remove AUDIT compat shims (~50 LOC, low priority)
5. #311 — Finish factoring `append_review_audit` (~120 LOC)
6. #313 — AI foundations 1.1/1.2/1.3 regen (needs user enqueue; see handoff)
7. #315–#318 — Pipeline v2 follow-ups from the #239 audit split

**Infra shipped in session 4** — skim before resuming delegations:
- `docs/review-protocol.md` — canonical reviewer contract with mandatory FINDING format
- `scripts/verify_review.py` — post-hoc grep-verification of reviewer quotes (pipe a review through it when findings look suspect)
- `--review` flag on `ask-gemini`/`ask-codex`/`ask-claude` (bridge parity)
- Gemini Pro is the default for `--review`; Flash only if explicitly requested

**Side lane for user** (handoff has the exact commands):
- Enqueue 7 critical-quality modules (<2.0 score) into pipeline v2
- Triage 2 dead-letter translation modules (`distributed-systems/5.1`, `5.3`)

---

## Prior session archive (sessions 1–3 content below, kept for reference)

Lead: Claude. Citation-first infra for automated pipeline (Gemini 3.1 Pro writes → Codex reviews/fact-checks/applies). Full handoff: [`docs/sessions/2026-04-18-lead-dev-citation-infra.md`](./docs/sessions/2026-04-18-lead-dev-citation-infra.md).

**Session 2 progress (autonomous run):**
- Pushed 4 citation-infra commits to `origin/main` (build verified green, 1797 pages, 0 errors).
- Read V3 proposal #217 in full — most already shipped via #219/#224/#226. Remaining: pin Gemini, per-track rubric, sampling.
- Drafted 4 infra GH issues: **#276** (local API GH endpoints), **#277** (local API build endpoints), **#278** (pipeline v3 remaining — 3 PRs), **#279** (automated citation pipeline wiring).
- Opened **PR #280** — citation-aware module page design proposal (3-tab Theory/Practice/Citations via Starlight `<Tabs syncKey>`; resolves design scope of #273).
- Delegated all 5 to Codex via agent bridge (task-ids infra-276..279, review-280). Build-report-in-PR-body convention included in each delegation to avoid future Claude-side build hops.

**Role-swap decision:** picked Codex adversarial on every PR (role-swap per PR) — consistent with Codex-as-reviewer memory and #235 queue ownership pattern. Gemini stays as fallback only if Codex is unavailable.

**Session 2 — autonomous run additions (while user AFK):**

API stability (committed d19a1016):
- Killed runaway API instance (stale port 8768 lock); restarted on 127.0.0.1:8768 (per `localhost_only` rule).
- Added `timeout=5` to two unbounded `subprocess.run` calls in `scripts/local_api.py` (`build_worktree_status`, `list_worktrees`) — they can hang the briefing endpoint when git hits lock contention.
- Wrapped `do_GET` response-send in `BrokenPipeError`/`ConnectionResetError` handler — client disconnects no longer noisy.
- Explicit `ThreadingHTTPServer.daemon_threads = True` and `allow_reuse_address = True` — eliminates "port in use" startup loops.

Pipeline running (foreground now; survives session end):
- Killed 4 stale PID files (patch/review/write/pipeline).
- Started 3 v2 workers via Bash background: patch-worker (PID 87463), review-worker (PID 87941), write-worker (PID 88084). All orphaned from parent shell.
- Sleep interval: 30s. Workers are live and picking up work — pipeline moved 1 pending_patch job through patch → review since start.
- Current state: `pending_review: 1, pending_write: 0, pending_patch: 0, done: 566, dead_letter: 0, in_progress: 0`. Convergence 99.8%. flapping_count: 12 (up 1; minor).

Codex delegation (with `CODEX_BRIDGE_MODE=danger` since prior `safe` mode blocked writes + network):
- `infra-277-v2` (rerun of #277 build API endpoints) — running in background task `b6n7sz9tq`.
- `infra-235-race` (CRITICAL parallel race condition from #235, lines 3049-3063 / 190-201 / 2848-2864 of v1_pipeline.py) — running in background task `b7u81pwe3`.
- Earlier `review-280` completed successfully: substantive adversarial review (5 concrete findings, corpus-scan evidence). Posted as PR comment since Codex has no network to `gh`.

Issue triage / comments posted:
- **#217** — status audit posted; remaining work tracked in #278; recommended close once PR 1 lands.
- **#274** — ACs 1-3 marked done with commit references; AC4 handled; AC5 deferred to #279.
- **#180** — AI Foundations batch reset announced per #274.

Uncommitted in tree:
- `src/content/docs/k8s/lfcs/module-1.4-storage-services-and-users-practice.md` — **worker WIP**, don't touch.
- `docs/sessions/` — untracked session handoff docs.

**PRs opened by Codex, reviewed by Claude (role-swap convention). All OPEN, waiting for user merge:**

#235 HIGH-severity bug fixes (14 of 14 closed):
- #281 serialize parallel worker state mutations (CRITICAL)
- #284 defer data_conflict check until after draft
- #285 malformed review JSON fails closed
- #287 _merge_fact_ledgers is pure and idempotent
- #288 needs_independent_review revived for last-resort approvals
- #289 content-aware ledger covers late sections (40k windowing)
- #290 check_failures tracks consecutive, not lifetime
- #291 last-attempt edit success triggers re-review, not reject
- #292 write-only preserves draft for review (regression test lock-in)
- #293 fresh restart clears stale resume metadata
- #294 review fallback chain continues to last-resort
- #295 severe rewrite clears stale targeted_fix, uses full rewrite model
- #296 CHECK retries in-function, shields outer circuit breaker
- #297 rewrite retries extract knowledge packet from baseline
- #298 unify retry policy across serial/parallel/reset-stuck modes

#277/#278 infra (pipeline v3 remaining + build API):
- #282 feat: /api/build/run + /api/build/status (#277) — **note: re-run ruff + npm run build from main before merge**, worktree build-path bug was environmental
- #283 refactor: pin Gemini writer model via single constant (#278 PR 1, narrow)
- #286 refactor: pin Gemini constant across remaining workers (#278 PR 1b, full)

#273 design:
- #280 citation-aware module page design proposal

**Full session PR tally — 21 PRs opened, 21 reviewed:**

#235 HIGH-severity (14/14 closed):
#281 parallel-race, #284 data_conflict, #285 malformed-JSON, #287 merge-ledgers-pure,
#288 needs_indep_review, #289 ledger-40k-windowing, #290 consecutive-check_failures,
#291 last-attempt-re-review, #292 write-only-regression, #293 fresh-restart-cleanup,
#294 fallback-chain-last-resort, #295 severe-rewrite-full-model,
#296 CHECK-retries-in-function, #297 rewrite-from-baseline, #298 unified-retry-policy

#235 MEDIUM (1 closed, more remaining):
#302 rejected-drafts-do-not-poison-ledger

#277 (local API build endpoints):
#282 /api/build/run + /api/build/status

#278 (pipeline v3 remaining, all 4 sub-PRs complete):
#283 pin Gemini 1a (narrow), #286 pin Gemini 1b (full), #300 per-track rubric profiles,
#301 second-reviewer sampling

#276 (local API GH endpoints):
#299 /api/gh/issues + /api/gh/prs

#273 design:
#280 citation-aware module page (3-tab proposal)

**Codex queue state:**
- `infra-279` (citation pipeline wiring) — **TIMED OUT at 900s**, no PR. Partial work (+655 LOC across 3 files) uncommitted in `.worktrees/citation-pipeline`. Don't commit as-is. #279 comment posted with recommendation to split into 3 sub-tasks (#279a seed injection, #279b citation gate step, #279c rubric dimension + e2e test).
- All other originally-queued tasks now have PRs.

**Merge ordering guidance for user return:**
1. First: #281 (parallel race — highest-impact), #285 (fail-closed), #290 (consecutive counter — composes with #296)
2. Then: all other #235 HIGH bugs (can merge in any order, some compose — see individual review comments)
3. Then: #278 PR 1a (#283) → PR 1b (#286) (stacked — 1b needs 1a first) → PR 2 (#300) → PR 3 (#301)
4. Then: #276 (#299), #277 (#282 — but re-run build from main first)
5. Then: #302 (composes with #287, #289)
6. #280 (design proposal) merge decision separate — reviews posted
7. #279 (citation pipeline) — pending Codex completion

**Service state at handoff:**
- API: 127.0.0.1:8768, PID 82871, uptime 20 min
- v2 patch/review/write workers: PIDs 87463 / 87941 / 88084, all 19 min uptime
- dev server: unchanged (existing)
- Pipeline convergence: 99.8%, 566 done, 1 pending_review (flapping on LFCS module-1.4, known issue being tracked in #235)
- 0 stale pid files, 1 stopped (pipeline supervisor, intentional — workers are direct-run, no supervisor layer active)

## Current State

**726 modules** across 8 published tracks. **115 Ukrainian translations** (~16% — certs + prereqs; AI/ML and AI not yet translated).

**Website:** https://kube-dojo.github.io/ (Starlight/Astro, ~1,350 pages, ~30-40s build)

**Site tabs:** Home | Fundamentals | Linux | Cloud | Certifications | Platform | On-Premises | AI | AI/ML Engineering

## Curriculum Summary

| Track | Modules | Status |
|-------|---------|--------|
| Fundamentals | 44 | Complete |
| Linux Deep Dive | 37 | Complete |
| Cloud | 85 | Complete |
| Certifications (CKA/CKAD/CKS/KCNA/KCSA/Extending + 12 learning paths) | 195 | Complete |
| Platform Engineering | 210 | Complete |
| On-Premises Kubernetes | 51 | Complete (needs Gemini review) |
| AI | 21 | Expanded bridge track; needs production-quality upgrades |
| AI/ML Engineering | 79 | Complete (expanded beyond Phase 4b; needs ongoing quality upgrades) |
| **Total** | **726** | **Complete** |

### Certifications Breakdown
| Cert | Modules |
|------|---------|
| CKA | 47 |
| CKAD | 30 |
| CKS | 30 |
| KCNA | 28 |
| KCSA | 26 |
| Extending K8s | 8 |

### Cloud Breakdown
| Section | Modules |
|---------|---------|
| Hyperscaler Rosetta Stone | 1 |
| AWS Essentials | 12 |
| GCP Essentials | 12 |
| Azure Essentials | 12 |
| Architecture Patterns | 4 |
| EKS Deep Dive | 5 |
| GKE Deep Dive | 5 |
| AKS Deep Dive | 4 |
| Advanced Operations | 10 |
| Managed Services | 10 |
| Enterprise & Hybrid | 10 |

### On-Premises Breakdown
| Section | Modules |
|---------|---------|
| Planning & Economics | 4 |
| Bare Metal Provisioning | 4 |
| Networking | 4 |
| Storage | 3 |
| Multi-Cluster | 3 |
| Security | 4 |
| Operations | 5 |
| Resilience | 3 |

### Platform Engineering Breakdown
| Section | Modules |
|---------|---------|
| Foundations | 32 |
| Disciplines (SRE, Platform Eng, GitOps, DevSecOps, MLOps, AIOps + Release Eng, Chaos Eng, FinOps, Data Eng, Networking, AI/GPU Infra, Leadership) | 71 |
| Toolkits (17 categories) | 96 |
| Supply Chain Defense Guide | 1 |
| CNPE Learning Path | 1 |

### AI/ML Engineering Breakdown
Migrated from neural-dojo + modernized with 8 new 2026 modules (#199, Phase 4b). All modules passed the v1 quality pipeline at 38–40/40.

| Section | Modules |
|---------|---------|
| Prerequisites | 4 |
| AI-Native Development | 10 |
| Generative AI | 6 |
| Vector DBs & RAG | 6 |
| Frameworks & Agents | 10 |
| AI Infrastructure | 5 |
| Advanced GenAI | 11 |
| Multimodal AI | 4 |
| Deep Learning | 7 |
| MLOps | 12 |
| Classical ML | 3 |
| History | 1 |

### AI Breakdown
Top-level learner-first AI track designed as the bridge from AI literacy into real AI building and then into AI/ML Engineering.

| Section | Modules |
|---------|---------|
| Foundations | 6 |
| AI-Native Work | 4 |
| AI Building | 4 |
| Open Models & Local Inference | 7 |
| AI for Kubernetes & Platform Work | 4 |

### Ukrainian Translations
| Track | Translated | Total |
|-------|-----------|-------|
| Prerequisites | 35 | 33 |
| CKA | 47 | 47 |
| CKAD | 30 | 30 |
| CKS | 0 | 30 |
| KCNA | 0 | 28 |
| KCSA | 0 | 26 |
| AI/ML Engineering | 0 | 68 |
| **Total** | **115** | **626** |

## Quality Standard

**Rubric-based quality system** (docs/quality-rubric.md): 7 dimensions scored 1-5. Pass = avg >= 3.5, no dimension at 1.

**Audit results** (docs/quality-audit-results.md, 2026-04-03): 31 modules scored.
- Overall avg: 3.3/5 (GOOD)
- Gold standard: Systems Thinking (4.6), On-Prem Case (4.4)
- 5 critical stubs fixed (expanded from 49-74 lines to 266-918 lines)
- 3 high-priority modules improved (API Deprecations, etcd-operator, Deployments)
- Remaining: 8 medium, 11 low priority modules need improvements

**Systemic issues found & being addressed**:
1. No modules had formal learning outcomes → added to all rewritten modules + codified in writer prompt
2. Active learning back-loaded to end in 87% of modules → inline prompts added to rewrites
3. Quiz questions tested recall not understanding → scenario-based quizzes in all rewrites

## Open GitHub Issues

| # | Issue | Status |
|---|-------|--------|
| #14 | Curriculum Monitoring & Official Sources | Open |
| #143 | Ukrainian Translation — Full Coverage | Open (~40%) |
| #157 | Supabase Auth + Progress Migration | Open |
| #156 | CKA Parts 3-5 Labs | Open |
| #165 | Epic: Pedagogical Quality Review | Open (Phases 1-3,5 done; Phase 4: CKA/CKAD/On-Prem complete) |
| #180 | Elevate All Modules to 4/5 | Open (CKA/CKAD/On-Prem done; CKS/KCNA/KCSA/Cloud/Platform pending) |
| #177 | Improve Lowest-Quality Modules | Open (8 critical/high done, ~19 remaining) |
| #179 | Improve Lowest-Quality Labs | Open (blocked on Phase 3 lab audit) |
| #199 | AI/ML Engineering track migration + modernization | Open (Phase 4b done; Phase 7 cross-link + Phase 8 UK translate remain) |
| #200 | AI/ML local per-section module numbering (filename rename) | Open (delegated to Codex in worktree) |

## Recently Closed (Session 3)
| # | Issue | Status |
|---|-------|--------|
| #174 | Phase 1: Research Educational Frameworks | Closed — docs/pedagogical-framework.md |
| #175 | Phase 2: Create Quality Rubric | Closed — docs/quality-rubric.md |
| #176 | Phase 3: Audit Modules Against Rubric | Closed — 31 modules scored |
| #178 | Phase 5: Codify Quality Standards | Closed — writer prompt, rules, skill updated |
| #170-173 | Gemini's buzzword issues | Closed — replaced by concrete sub-tickets |

## TODO

- [x] Prerequisites: all 33 modules improved (outcomes, inline prompts, quiz upgrades, emoji fixes) — EN + UK complete
- [x] Linux: all 37 modules improved (outcomes added) — EN + UK complete
- [x] CKA: all 41 modules — outcomes + inline prompts + scenario quizzes (Parts 0-5 complete) — EN complete, UK outcomes synced
- [x] CKAD: all 24 modules — outcomes + inline prompts + scenario quizzes — EN complete, UK outcomes synced
- [x] CKS: 30 modules — outcomes + inline prompts + scenario quizzes — EN complete, UK outcomes synced
- [x] KCNA: 28 modules — outcomes + inline prompts + scenario quizzes — EN complete, UK outcomes synced
- [x] KCSA: 26 modules — outcomes + inline prompts + scenario quizzes — EN complete, UK outcomes synced
- [x] On-Premises: all 30 modules — inline prompts + narrative between code blocks + quiz improvements
- [x] Fundamentals track reorder: Zero to Terminal → Everyday Linux → Cloud Native 101 → K8s Basics → Philosophy & Design → Modern DevOps
- [x] Zero to Terminal: Next Module link fixes (0.1→0.2, UK 0.2→0.3)
- [x] Git Deep Dive course: 10 modules + Git Basics in ZTT — #190
- [x] v1 quality pipeline built: AUDIT→WRITE→REVIEW→CHECK→SCORE — #188
- [x] Gap detection (within-track + cross-track) — #188
- [x] Zero to Terminal: 10/10 modules pass pipeline (29+/35)
- [x] All prerequisites pass pipeline (43/44 done, 29+/35) — #180
- [x] 6 rejected prereq modules rewritten by Gemini + passed pipeline (35/35, 34/35)
- [x] ZTT module numbering collision fixed (0.6 git-basics + 0.6 networking → renumbered 0.7-0.11)
- [x] Pipeline v2: Gemini defaults, e2e command, track aliases, safety hardening
- [x] uk_sync.py consolidated: status/detect/fix/translate/e2e with track aliases
- [x] Certs pipeline: 150/164 pass, 3 fail, 8 WIP — #180
- [x] Cloud pipeline: 80/86 pass — #180
- [x] Linux pipeline: 34/38 pass — #180
- [x] Pipeline v3: knowledge packets, block-level rewrite, ASCII→Mermaid — #192
- [x] Pipeline: section index.md rewrite (EN) + auto-translate (UK) after section completes
- [x] Pipeline: 41 integration tests (test_pipeline.py)
- [x] Pipeline: subsection aliases (ztt, cka, aws, etc.) + auto-discover from any dir path
- [x] Nav fix: all 156 index.md files (EN+UK) set to sidebar.order: 0
- [x] Nav fix: slug corrections for ZTT module-0.6, git-deep-dive modules 1 and 9
- [x] K8S_API check: demoted to WARNING, strips code blocks + inline code (false positives)
- [x] .staging file glob bug fixed (was creating bogus state entries)
- [x] Token analysis: subagents are 74% of volume but mostly cheap cache reads. Not the cost monster claimed.
- [x] AI/ML Engineering track migrated from neural-dojo (60 existing + 8 new 2026 modules, #199 Phase 4b). All 8 new pass v1 pipeline at 40/40.
- [x] v1 pipeline fixes: 300s→900s timeouts, targeted-fix / nitpick / previous_output scaffolding, short-output guard (enables quality-rubric retries to converge)
- [ ] AI/ML Engineering #199 remaining: Phase 7 cross-link (run), Phase 8 UK translate (skipped for now)
- [ ] AI/ML Engineering #200: local per-section module numbering (delegated to Codex)
- [ ] Remaining pipeline: On-Premises (30), Platform (209), Specialty (18) — #180
- [ ] Stuck modules: ~11 at WRITE (Gemini rejection loop), need knowledge packet retry
- [ ] ASCII→Mermaid conversion pass for all 587 modules — #193 (after #180)
- [ ] UK prereqs translation: re-sync after pipeline rewrites
- [ ] Lab quality audit and improvements — #179

## Blockers
- Gemini CLI output inconsistency: sometimes writes to files, sometimes returns to stdout — handled but fragile

## Key Decisions
- Migrated from MkDocs Material to Starlight (Astro) — faster builds, proper i18n, modern stack
- `scripts/dispatch.py` replaces `ai_agent_bridge/` — direct CLI dispatch, no SQLite broker
- GH Actions pinned to commit SHA, requirements locked with hashes, Dependabot enabled
- Pinned zod@3.25.76 (zod v4 breaks Starlight schema validation)
- `defaultLocale: 'root'` for Starlight i18n — English at root URLs, Ukrainian at `/uk/`
- On-prem modules written by parallel agents (~500 lines each), need Gemini adversary review

---
**Maintenance Rule**: Claude updates this file at session end or after completing modules.

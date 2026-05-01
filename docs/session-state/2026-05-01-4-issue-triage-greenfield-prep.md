# Session handoff — 2026-05-01 (session 4) — issue triage (40 → 14 open) + greenfield priority + KServe dispatch staged

> Picks up from `2026-05-01-3-559-evidence-prep.md` (#559 + #394 closeout). Same session, second logical phase: a deep audit of every open issue against #388's actual scope, executing 26 issue closures (40 → 14 open), confirming greenfield-before-#388 sequencing, building the KServe dispatch brief, and locking the user's "REWRITE-tier first within #388" preference for later. Next session fires the KServe dispatch and runs the source-fidelity review.

## Decisions and contract changes

### Issue tracker triage — 40 open → 14 open (26 closures)

User asked for a deeper triage before kicking off #388: "go through the issues and triage them, some are replaced by 388 or completed already or stale, can you do that first? feel free to push back."

Pulled state on every open issue. Audited #388's body (scope = 1,339 modules, density triage + cross-family teaching judge + writer routing + citation verify + density gate, Phase 0 + Phase 1 ticked, Phase 2a triage to 2026-05-05, Phase 2b rewrite to 2026-05-17). Audited each candidate. Where evidence supported closure I closed; where I disagreed with the user's framing I pushed back.

**Closed in 4 categories:**

- **Subsumed by #388 (16)** — `--reason completed`. The #180 parent epic + its 8 per-track quality slices (#331-#338) + the queue and pipeline rebuilds (#348, #375, #376) + the Phase C/D/D.5 plan (#381, #382, #383) + showcase 5/5 (#181) all reduce to "the rewrite work that #388 now executes as one pipeline."
- **Genuinely completed (4)** — `--reason completed`. #248 (cert-prep + route work shipped 2026-04-16 in `f5818b32`); #378 (all 12 modules of Phase A.1 shipped, #387 spun-out manual rewrite closed, residual citation backfill is now #388 Stage 5); #384 (substantially shipped via various batches: Release Eng / Chaos / FinOps / Leadership / Networking / Data Eng / Extending K8s — only eBPF + Edge K8s + IPv6 residuals remain); #421 (ACs satisfied via #559 + #394 closeout; all 72 chapters now `cross_family_satisfied: true`).
- **Stale (5)** — `--reason "not planned"`. #142 (MDX never adopted); #156 (CKA Parts 3-5 Labs unfunded); #157 (Supabase auth — body says "not now"); #183 (CKA Part 6 Mock Exams — parent #180 dying); #246 (route design, no movement since 2026-04-17 + #248 already shipped some).
- **Substantially shipped (1)** — #503: dashboard book-progress + module-distribution panels shipped in `c70b6f2d` last session; module-status frontmatter (`revision_pending: true`) lives in #388.

**Pushback the user accepted:** the user's initial closure list included Phase A.2 (#379) and Phase E.2 (#385) under "net-new content but maybe stale." Audit showed #379's 4 modules (KServe, Seldon Core, BentoML, bare-metal MLOps recipe) genuinely don't exist on main — kept open. #385 was scope-decay (3/7 modules already shipped: private LLM serving via 9.3, MetalLB in toolkits, bare-metal observability via 7.4/7.8) — kept open with scope tightened to 4 modules (Tanzu, OpenStack on K8s, Gardener, Karmada/Liqo + kube-vip).

**Pushback the user accepted on #378/#384:** initially I had both as "keep open." On second look #378 was complete (modules shipped + #387 closed) and #384 was 80% shipped (residuals = 3 small modules). Closed both.

### Final open-issue inventory (14)

| # | Title | Status note |
|---|---|---|
| #14 | Curriculum Monitoring & Official Sources | Permanent tracker (body says "never close") |
| #143 | Ukrainian Translation full-site coverage | Active (translation lane separate from rewrite) |
| #186 | Ukrainian Translations sync with quality improvements | Active |
| #197 | On-Premises Track expansion | Strategic per `project_onprem_vision.md` |
| #341 | Citation residuals auto-resolver epic | Tooling, separate from #388 |
| #342 | pipeline-v4 rename `needs_human` → `residuals_filed` | 5-min mechanical task; could won't-do |
| #344 | Citation-residuals: extend resolver | In-flight per worktree `codex/issue-344` |
| #373 | Liveness probes for LLM-dispatch subprocesses | Stalled but coherent infra-reliability scope |
| **#379** | **Phase A.2 greenfield MLOps (KServe / Seldon / BentoML / bare-metal MLOps)** | **Tier 1 greenfield priority — KServe drafting next session** |
| **#385** | **Phase E.2 on-prem expansion** (scope-tightened to 4 modules) | **Tier 1 greenfield priority — after #379** |
| #386 | Phase F: Lab quality audit | Labs ≠ modules; distinct from #388 |
| #388 | Site-wide module quality rewrite | Active; **defer Phase 2b until #379 + #385 land** |
| #391 | Public-facing status page | Borderline-stale; coherent product idea |
| #393 | Post-#388 ML/AI history depth pass | Explicitly post-#388 |

### Sequencing decision (user-confirmed)

**Greenfield #379 + #385 ship BEFORE #388 Phase 2b heavy rewrite.**

User signal: "after closing please prio the new modules, even before 388 ok?"

Rationale: greenfield modules fill genuine user-facing topic gaps; #388 rewrites improve modules that already exist. Codex 10x window runs to **2026-05-17** (16 days from now), which fits ~10-12 greenfield modules cleanly with room left for #388. Gemini downgrade hits **2026-05-05** (4 days), so any Gemini-dependent triage work in #388 Phase 2a should run in parallel (deterministic Python triage, no quota cost).

### Writer/reviewer split (user-confirmed)

> User: "1: you are routing no gemini, and codex drafts claude reviews yes 2: confirm. 3: up to you"
> User followup: "rewriter is codex"

- **No Gemini** in routing for greenfield drafts (saving quota / past downgrade).
- **Codex drafts** all greenfield modules (gpt-5.5, danger mode, reasoning=high per `reference_codex_models.md`).
- **Claude reviews** source-fidelity (orchestrator pass, posts `<!-- prose review claude -->` marker on the PR per the AI history pattern).
- **For #388 rewrites** when we get to them: Codex is also the rewriter. Same routing.

### #388 sequencing preference (user-confirmed)

> User: "btw you see that the modules are marked for rewrite and some for review. we will focus on the rewrite part first."

Within #388, **REWRITE-tier (~165 modules at <18 wpp)** ships before **REVIEW-tier (additional ~85-200 modules at <22 wpp threshold needing teaching-judge LLM call)**. The rewrite-tier modules have the worst density signature (Codex pad-bombs at 10.9 wpp, v3 punchy-bullets at 15.6 wpp, Gemini v4 thin essays) and the highest visible damage to learners. Review-tier waits.

### KServe dispatch brief — staged, not fired

The dispatch brief is at `/tmp/kserve_dispatch_brief.md` (107 lines, will need to be re-staged next session since `/tmp` is volatile — see "Restart commands" below).

Module placement: `src/content/docs/platform/toolkits/data-ai-platforms/ml-platforms/module-9.3-kserve.md`. Slots in as 9.3 (after 9.1 Kubeflow at sidebar.order=2 and 9.2 MLflow at order=3, so KServe = order=4). The toolkit index `ml-platforms/index.md` currently advertises 9.3=Feature Stores, 9.4=vLLM, etc. — those are PLANNED but unshipped. Inserting KServe at 9.3 bumps the planned-but-unshipped chain down by one (Feature Stores → 9.4, vLLM → 9.5, Ray Serve → 9.6, LangChain → 9.7, GPU Scheduling → 9.8). Index needs updating after the draft lands.

Brief specifies:
- Binding spec: `scripts/prompts/module-writer.md` (read at top of run)
- Title, file path, slug, sidebar order, complexity (`[COMPLEX]`), time (55-65 min), prerequisites
- 8 topic-coverage bullets (architecture, InferenceService anatomy, model storage + runtimes, **serverless vs raw deployment** as the central pedagogical fork, rollout strategies, autoscaling, multi-model and InferenceGraph, production concerns)
- Hands-On Exercise concept (6 progressive tasks ending in canary rollout + raw-deployment-mode switch + optional explainer)
- Sources discipline: 10+ verified URLs in `## Sources`; per `feedback_citation_verify_or_remove.md` "unverified = remove"
- Anti-leak: forbidden words/phrases in body per `feedback_codex_prose_meta_diction_leak.md` ("the contract", "Yellow", "anchor", "deliberately cautious", "load-bearing", etc.)
- Output discipline: write only `module-9.3-kserve.md`, do NOT touch `index.md` (orchestrator handles)
- Frontmatter: NO `revision_pending: true` (this is greenfield, not a #388 rewrite)
- Reporting: line/word/`<details>`/Sources counts, list of any URL it couldn't verify, list of any topic it had to defer

## What's still in flight (next session)

### Block — KServe draft + review (the priority)

1. **Re-stage the brief** — `/tmp/kserve_dispatch_brief.md` is volatile across sessions. The brief content lives in this handoff (above) but the easiest restart is to grep this file for the `cat > /tmp/kserve_dispatch_brief.md <<'EOF'` block from the prior turn — it's preserved in the conversation transcript. Or just rebuild from the spec in this file.

2. **Smoke-check Codex** before dispatch (per `feedback_verify_codex_auth.md`): `echo "Reply with exactly OK and nothing else." | scripts/ab ask-codex --task-id smoke-pre-kserve --new-session --from claude --to-model gpt-5.5 -` — expect `✅ Codex finished (2 chars)` in <15s.

3. **Fire the dispatch SYNCHRONOUSLY (foreground)**:
   ```bash
   cat /tmp/kserve_dispatch_brief.md | scripts/ab ask-codex \
     --task-id kserve-draft-2026-05-02 --new-session \
     --from claude --to-model gpt-5.5 -
   ```
   **Do NOT use `run_in_background: true`** — confirmed this session that the wrapper dies silently with 0-byte output and stays `pending+unacknowledged` in the bridge when run in BG (two failed attempts on Ch03 review before falling back to FG, which worked first try). The dispatch takes 5-10 min foreground.

4. **Source-fidelity review pass** (Claude / orchestrator):
   - Read the generated `module-9.3-kserve.md`
   - Verify line count ≥ 600 content lines (visual aids excluded)
   - Verify EXACTLY 4 Did You Know facts; 6-8 Common Mistakes rows; 6-8 quiz questions with at least 4 scenario-based; 4-6 Hands-On Exercise tasks
   - For every URL in body text, confirm it appears in `## Sources` AND that the URL is reachable (curl headers; 200 acceptable, redirects to canonical fine)
   - Spot-check claims against KServe's official docs (use the URL list from the brief as the primary anchor pool)
   - Check for forbidden contract-language leaks
   - Post Claude source-fidelity review marker via `gh pr comment <PR> --body-file /tmp/kserve_claude_review.md` after the PR opens

5. **Update toolkit index** (`src/content/docs/platform/toolkits/data-ai-platforms/ml-platforms/index.md`):
   - Add 9.3 KServe row to the Modules table
   - Bump 9.3 Feature Stores → 9.4, 9.4 vLLM → 9.5, 9.5 Ray Serve → 9.6, 9.6 LangChain → 9.7, 9.7 GPU Scheduling → 9.8
   - Add KServe to Tool Selection Guide and ML Platform Stack diagrams (it's already mentioned as a tool but not a planned module — fix the inconsistency)
   - Add KServe to Study Path

6. **Build verification**:
   ```bash
   npm run build               # 0 errors
   .venv/bin/python scripts/check_site_health.py  # 0 errors
   ```

7. **Commit + push + open PR**:
   - One commit for the new module + index update + changelog entry
   - Body of PR description has the Codex draft report + Claude review summary
   - Link PR to #379

### Block — after KServe ships

**#379 remaining (3 modules):** Seldon Core, BentoML, bare-metal MLOps recipe. Same pattern as KServe (Codex draft → Claude review → PR). ~2-3h each module dispatched.

**#385 (4 modules):** VMware Tanzu, OpenStack on K8s, Gardener, Multi-cluster on-prem (Karmada/Liqo). After #379 wraps. Update #385 body to remove already-shipped items (private LLM, MetalLB, bare-metal observability).

**#384 residuals (file fresh issue):** eBPF foundation + dedicated Edge K8s + IPv6/dual-stack networking. 3 modules. Open as a fresh small issue once #379 + #385 are in flight.

**#388 sequencing:** Phase 2a triage (deterministic Python pass — free) can run any time; defer Phase 2b heavy rewrites until #379 + #385 land. Within Phase 2b, **REWRITE-tier first** (~165 modules at <18 wpp) per user signal.

### Carryover from prior handoffs (still open)

- **Ch02 line-119 fix** — the "five years before" → "more than a decade before" follow-up Codex caught at line 127 in commit `b4d09a00` but missed at line 119 (surfaced in the Claude source-fidelity backfill review on PR #479 this session). One-line fix; low priority.
- **Ch32–Ch37 research-pending** under strict-gh audit (out of #559 scope; could spin a fresh sub-issue or fold into next #394-adjacent work).
- **PR #567** review + merge → review-coverage schema work.
- **PR #558 + PR #565** — stale-prose cleanup (content already on main, just bookkeeping).
- **Issue #344** — citation-residuals resolver work in `codex/issue-344` worktree (local-only branch).
- **Google Search Console** — waiting on user to paste the meta-tag token.

## Cross-thread notes

**ADD:**

- **Issue tracker shrunk 40 → 14 open** via 26 closures on 2026-05-01. Subsumption pattern: #388 absorbed the entire #180 chain (8 slices + parent + showcase + queue + pipeline rebuilds + Phase C/D plan); #559+#394 closeout retroactively satisfied #421.
- **Greenfield-before-rewrite is now policy** for the next 2 weeks. #379 + #385 ship first; #388 Phase 2b heavy rewrites wait. Codex 10x window (until 2026-05-17) is the budget envelope.
- **Codex = primary writer for both greenfield and #388 rewrites.** No Gemini in routing post-this-session. #388's older comment about Gemini taking over is superseded.
- **Within #388, REWRITE-tier ships before REVIEW-tier.** Per user 2026-05-01: "we will focus on the rewrite part first."
- **Background `scripts/ab ask-codex` dispatches die silently** (confirmed twice this session on Ch03 review — 0-byte output, message stays `pending+unacknowledged` in the bridge). Always dispatch FG. Smoke-check first.

**DROP / RESOLVE:**

- "TODO: issue closeout audit" carryover — DONE this session (26 closures).
- "TODO: pick option (a/b/c) on #559" — DONE earlier this session (option c hybrid executed).
- "TODO: greenfield priority order before #388" — DONE this session (KServe = first; locked greenfield-before-#388 sequencing).

## Cold-start smoketest (executable)

```bash
# 1. Confirm 14 open issues + #388 still active
gh issue list --state open --limit 60 --json number --jq 'length'
# expect: 14

# 2. Confirm KServe module slot still empty
ls src/content/docs/platform/toolkits/data-ai-platforms/ml-platforms/ | grep -E "kserve|9\.3"
# expect: nothing matching kserve; module-9.2-mlflow.md present, no 9.3 yet

# 3. Smoke-check Codex (5-second sanity check before any draft dispatch)
echo "Reply with exactly OK and nothing else." | scripts/ab ask-codex \
  --task-id smoke-pre-kserve --new-session --from claude --to-model gpt-5.5 -
# expect: ✅ Codex finished (2 chars)

# 4. Confirm clean tree
git status -sb
# expect: ## main...origin/main (no dirty files)

# 5. Confirm 3 commits from session 3 + this handoff landed
git log --oneline origin/main~5..origin/main
# expect: 9aed10b8 + 2371dff6 + 262fa7a2 visible
```

## Files modified this session

```
(no source-tree edits this session — only GitHub state changes)

GitHub side:
  26 issues closed across #180/#181/#142/#156/#157/#183/#246/#248/#331-338/#348/#375/#376/#378/#381-383/#384/#421/#503
  Final open count: 14 (was 40)

Local artifacts (NOT committed):
  /tmp/kserve_dispatch_brief.md — 107-line dispatch brief, volatile
  /tmp/close_*.md — 7 close-comment bodies (used during the closure pass)

To be committed at session-4 end:
  STATUS.md                                                 — Latest handoff bumped + open-issue rows updated + greenfield priority logged
  docs/session-state/2026-05-01-4-issue-triage-greenfield-prep.md  — this file
```

## Blockers

(none — KServe dispatch is ready to fire, blocked only on context budget for sync wait)

# Session handoff — 2026-05-06 (session 2) — #388 meta-fix + autonomous chain

> Picks up from `2026-05-06-1-878-closed-and-388-prep.md`. Three things shipped:
>
> 1. **K8S Cgoa #388 batch fully closed** — 5 modules merged (PRs #911-#915), all scoring 5.0/5.0. Each had to be re-dispatched after gemini round-1 NEEDS CHANGES revealed three systemic defects: bash alias anti-pattern, fictional anecdotes, MCQ option stripping.
> 2. **Meta-fix PR #916 — writer prompt + verifier + dispatcher hardened** to prevent the three defect classes from recurring on the remaining 360+ critical modules. Three new deterministic gates (`runnable_no_kubectl_alias`, `anti_fabrication_no_unsourced_anecdote`, `practice_mcq_four_options_with_distractors`) plus prompt rules + dispatcher fix.
> 3. **Dispatcher PR-fallback patch PR #919** — orchestrator-driven PR creation when codex sandbox lacks `GH_TOKEN` (intermittent issue blocking auto-merge in batches), plus Gemini→Claude review fallback when Gemini rate-limits. Autonomous chain now runs end-to-end without manual orchestration per module.
>
> Also kicked off an autonomous 36-module chain (10 small cert tracks) that runs through the 14-20 cred window and beyond.

## Decisions and contract changes

### #388 prompt + verifier hardening (PR #916, commit `e65d1858`)

K8S Cgoa batch shipped 5/5 NEEDS CHANGES because writer prompt, dispatcher, and verifier disagreed on three rules. Aligned all three:

- **`scripts/prompts/module-rewriter-388.md`** — added 3 hard rules (bash runnability, anti-fabrication, practice-question MCQ structure)
- **`scripts/prompts/module-writer.md`** — stripped "War Story" encouragement, fixed alias instruction
- **`scripts/quality/dispatch_388_pilot.py`** — inverted alias instruction
- **`scripts/quality/verify_module.py`** — three new gates with regex precision per gemini round-1 review:
  - `SCENARIO_PREFIX_RE` allows leading `**`/`_`/`#`/whitespace (bold-prefix support)
  - MCQ fallback dropped — `<details>` required
  - Plural distractor regex (`options?` / `choices?` / `answers?`)
  - MCQ option counter `>= 4` (not `!= 4`), anchored at column 0
- **`scripts/quality/test_verify_module.py`** — inverted old alias tests, added 4 new tests for the gate edges

**Pattern saved as memory: `feedback_three_way_rule_agreement.md`** — every rule must be in writer prompt + dispatcher + verifier in lockstep. Patches that touch only one ship defects.

### Dispatcher PR-fallback (PR #919, commit `98e6310e`)

`GH_TOKEN` intermittently fails to propagate to codex sandbox. PR #917 succeeded; PR #918's predecessor (Pca module) failed with `gh: not authenticated`. Patches `dispatch_388_pilot.py`:

- **`orchestrator_open_pr(slug, module_path, codex_response)`** — when codex's response contains no PR URL, parent process verifies branch via `git ls-remote origin <branch>`, then runs `gh pr create` itself. Distinct log events per failure path.
- **`dispatch_claude_review(pr_num, module_path, slug)`** — when Gemini returns ERROR or UNCLEAR, falls back to headless Claude (sonnet) cross-family review. Saved as memory: `feedback_headless_claude_gemini_fallback.md`.
- **`main()` flow** — both fallbacks integrated.
- 12 new tests, 42 total pass; ruff clean.

**Effect:** autonomous batch runs truly end-to-end. K8S Cgoa needed ~15 min orchestrator overhead per 5 modules; this drops to ~0 absent codex/gemini failures.

### ch-10 sibling-file paraphrase fix (PR #910, commit `df615914`)

Carryover from session 1. `infrastructure-log.md` + `scene-sketches.md` carried wrong "2560 wheels with 1280-digit capacity" Manchester paraphrase. Replaced with canonical chapter wording.

## What's still in flight

### **Autonomous chain (background)**
Bash wrapper at `/tmp/chain-small-tracks.sh` (PID may have changed; check `pgrep -f chain-small-tracks`). Runs:

```
K8S Pca (1)         ✅ MERGED via PR #918 (with cosmetic nits queued)
K8S Finops (2)      ⏳ in flight when handoff written
K8S Kca (2)         queued
K8S Otca (2)        queued
KCSA (2)            queued
K8S Ica (4)         queued
K8S Cnpa (5)        queued
K8S Cnpe (5)        queued
K8S Lfcs (5)        queued
K8S Extending (8)   queued
```

Per-module flow (post-#919): codex writes → codex opens PR (or orchestrator falls back) → gemini reviews → APPROVE auto-merges (or claude fallback if gemini errors) → next module. Logs at `/tmp/chain-2026-05-06.log` and `logs/388_batch_*-2026-05-06_2026-05-06.jsonl`.

ETA at 13:48 start, 15 min/module average → completion around 22:30-00:30 local.

**On chain completion:** parse held-PR list (NEEDS CHANGES verdicts), surgical re-dispatches.

### Held PRs from this session
None outstanding — all 5 of K8S Cgoa (PRs #911-#915) merged after surgical re-dispatch. K8S Pca PR #918 merged with **2 cosmetic nits** queued in task #12 for batch follow-up.

## What remains to do

### Immediate (next session)

1. **Continue chain** — when current bash wrapper exits, queue task #11: cert tracks (CKAD 23 → CKS 29 → CKA 32). Same pattern.
2. **Drain held PRs** — at chain end, parse `merge_held` events from JSONL logs and re-dispatch surgically.
3. **Cosmetic nits batch** (task #12) — single codex dispatch covering all queued nits.
4. **Branch protection UI flag** (carryover from session 1) — make `Incident dedup gate` workflow check a `required` check via GH Settings.

### Out-of-scope follow-ups

- **Full-book AI-history dedup pass** (task #3) — user approved option A (build scanner first, review candidates, then phase). Not started; deferred until #388 chain completes.
- **Bridge sync PR 2** (carryover) — port learn-ukrainian `c36d159a26` to kubedojo.
- **Bridge sync PR 3** (plumbing) — defer indefinitely.
- **GH_TOKEN value still exposed in 2026-05-04 transcript** — operational hygiene.

### Worktree state at handoff

```
/Users/krisztiankoos/projects/kubedojo                                        main
/Users/krisztiankoos/projects/kubedojo/.worktrees/codex-334-backstage-catalog (codex-interactive — DO NOT TOUCH)
/Users/krisztiankoos/projects/kubedojo/.worktrees/codex-334-backstage-dev     (codex-interactive)
/Users/krisztiankoos/projects/kubedojo/.worktrees/codex-closed-ac-repair      (codex-interactive)
/Users/krisztiankoos/projects/kubedojo/.worktrees/codex-interactive           (detached HEAD, codex-interactive)
```

Plus: each running batch creates `.worktrees/codex-388-pilot-<slug>` and removes it post-merge (cleanup phase).

## Cold-start smoketest

```bash
cd /Users/krisztiankoos/projects/kubedojo

# 1. Briefing
curl -s http://127.0.0.1:8768/api/briefing/session?compact=1 | head -50

# 2. Recent commits — should show #919, #918, #917, #916, #911-915, #910
git log --oneline -15

# 3. Chain still running?
pgrep -f chain-small-tracks
ps aux | grep -E "run_388_batch|codex exec" | grep -v grep | grep kubedojo | head -5

# 4. How many merged so far this chain?
grep -ch '"event": "merged"' logs/388_batch_*-2026-05-06_2026-05-06.jsonl 2>/dev/null | awk -F: '{sum+=$2} END {print "merged:", sum}'

# 5. Held PRs from this chain?
grep -h '"event": "merge_held' logs/388_batch_*-2026-05-06_2026-05-06.jsonl 2>/dev/null | python3 -c "import sys,json; [print(f\"  PR #{e['pr']}  {e['module']}  verdict={e['verdict']}\") for e in (json.loads(l) for l in sys.stdin)]"

# 6. Critical-module count post-chain
curl -s http://127.0.0.1:8768/api/quality/scores | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'critical: {d[\"critical_count\"]} / {d[\"count\"]}')"

# 7. New deterministic gates pass on current main?
.venv/bin/python -m pytest scripts/quality/test_verify_module.py -q
```

## Files touched / commits this session

```
On main (chronological):
  df615914  fix(ai-history): align ch-10 sibling files with chapter Manchester paraphrase (#910)
  e65d1858  chore(388): harden writer prompt + verifier against systemic batch defects (#916)
  e639e3ca  feat(388): rewrite k8s/cgoa/module-1.1 exam strategy and blueprint review (#911)
  ffafe273  feat(388): rewrite k8s/cgoa/module-1.2 gitops principles review (#912)
  67ccd28e  feat(388): rewrite k8s/cgoa/module-1.3 patterns and tooling review (#913)
  0dff228d  feat(388): rewrite k8s/cgoa/module-1.4 practice questions set 1 (#914)
  c16a2297  feat(388): rewrite k8s/cgoa/module-1.5 practice questions set 2 (#915)
  47ea2379  feat(388): density+structure rewrite of Advanced Cilium for CCA (#388 pilot) (#917)
  eba1724b  feat(388): density+structure rewrite of Module 1.1: PromQL Deep Dive (#388 pilot) (#918)
  98e6310e  chore(388): orchestrator-driven PR fallback + Claude review fallback (#919)
  + chain-merged commits from autonomous run (Finops, Kca, Otca, KCSA, Ica, Cnpa, Cnpe, Lfcs, Extending) — see git log
```

**Net effect on critical bucket:** start 366 → expected ~328-330 by chain completion if 30+ modules merge cleanly.

## Cross-thread notes

**ADD:**

- **#388 hardened prompt + verifier in production** as of `e65d1858`. Three deterministic gates (`runnable_no_kubectl_alias`, `anti_fabrication_no_unsourced_anecdote`, `practice_mcq_four_options_with_distractors`) catch what density-only verifier missed. Test coverage at `scripts/quality/test_verify_module.py` (30 tests pre-#919, 42 post).
- **Dispatcher orchestrator-PR fallback live** as of `98e6310e`. `dispatch_388_pilot.main()` now handles `no_pr_in_response` by falling back to `orchestrator_open_pr` (parent has GH_TOKEN). Also: Gemini→Claude review fallback when Gemini errors/UNCLEAR.
- **Three-way rule agreement pattern proven** — when writer prompt, dispatcher, and verifier disagree on a rule, modules ship with that defect class systematically. K8S Cgoa batch (5/5 NEEDS CHANGES) was the canonical case study. PR #916 fixed all three components in one commit.
- **Headless Claude as Gemini cross-family fallback validated** — Gemini 503'd / OAuth-timed-out repeatedly during PR #912/#913 round-2 reviews; `dispatch_smart.py review --agent claude --mode read-only` ran in 25-65s and produced specific diff-driven verdicts. Now codified in dispatcher (PR #919) and as memory (`feedback_headless_claude_gemini_fallback.md`).
- **Cred-window discipline** — at 14:00-20:00 (this session, 2026-05-06), user reminded that Claude is rate-limited. Reroute writes to codex (already default), reviews to gemini (default), avoid headless Claude reviews unless gemini truly fails. Orchestrator stays minimal.

**DROP / RESOLVE:**

- "Continue #388 ai-ml-engineering batch" (carryover from session 1) — NEW PRIORITY: bucket already shifted; this session targeted CGOA/CCA/PCA. RESOLVED via #911-#918, #917, #918.
- "K8S Cgoa cluster of 5 modules at score 1.5" — RESOLVED. All 5 modules now score 5.0 post-merge.
- "GH_TOKEN does not propagate to codex sandbox" workaround documentation — RESOLVED via PR #919 (workaround is now automatic via `orchestrator_open_pr`).

## Blockers

- **Branch protection UI flag** (unchanged from session 1) — making `Incident dedup gate` a required check on `main` needs UI click.
- **Cred-window 14:00-20:00 active** — route writes to codex, reviews to gemini, minimize orchestrator-Claude usage.

## New / updated memory this session

1. **NEW: `feedback_three_way_rule_agreement.md`** — writer prompt + dispatcher + verifier must agree on every rule. K8S Cgoa batch shipped 5/5 NEEDS CHANGES because they disagreed.
2. **NEW: `feedback_headless_claude_gemini_fallback.md`** — when gemini 503s on cross-family review, fall back to `dispatch_smart.py review --agent claude` (25-65s vs 240s+ gemini hang).

## What was NOT done this session (carryover)

- Full-book AI-history dedup pass scanner build (task #3, user approved scope but not started).
- Bridge sync PR 2 (port learn-ukrainian `c36d159a26`).
- Cert exam tracks chain (CKAD/CKS/CKA, task #11) — comes after small tracks.
- Cosmetic nits drain (task #12) — single dispatch at chain end.
- ch-10 Manchester sibling-file fix had carryover items already resolved earlier this session.

End-of-session: 10 PRs merged (1 ch-10 fix + 5 CGOA + meta-fix + Cca + Pca + dispatcher fallback) plus an autonomous chain still running. Net rubric impact: 7 modules graduated 1.5 → 5.0 with verified upstream prompt+verifier+dispatcher hardening that should make the next 360+ critical modules pass first review more often than not.

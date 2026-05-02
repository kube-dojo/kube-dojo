# Session handoff — 2026-05-02 (session 1) — #388 Day 1: verifier shipped + 6 density fix-passes merged

> Picks up from `2026-05-01-5-greenfield-shipped-388-prep.md`. This session executed all of Day 1 of #388: built and audited the deterministic density+structure verifier, ran it across all 235 `revision_pending` modules, and merged the 6 density fix-passes the prior session left failing. Session ran autonomously while user slept; orchestration was Claude (this agent) dispatching Codex for content/code work + Gemini for cross-family review on every PR.

## Decisions and contract changes

### Verifier shipped — PR #724

`scripts/quality/verify_module.py` (849 LOC) is the canonical #388 contract.

Codifies Codex's prescription: density gates (mean_wpp≥30, median_wpp≥28, short_rate≤20%, max_consecutive_short_run≤2, body_words≥5000, mean_sentence 12-28), structural gates (LO 3-5, DYK=4, CM 6-8, Quiz 6-8 with `<details>`, Hands-On checkboxes, section order), sources reachability, anti-leak grep, learning-outcome alignment. Outputs JSONL per module + tier (T0/T1/T2/T3).

CLI: `--all-revision-pending`, `--glob`, `--out PATH.jsonl`, `--summary`, `--quiet`, `--skip-source-check`, `--tier-only`, `--max-workers`. Importable as `verify_module.verify(path)`.

13 tests passing at `scripts/quality/test_verify_module.py`. Codex-authored, Gemini-reviewed. Two NEEDS CHANGES iterations addressed:

- **2c395360** — kubectl-alias check now searches original body (not body_no_code) so legitimate `alias k=kubectl` inside fenced blocks doesn't false-fail. Tier classification now correctly puts modules with body_words 3000-4999 in T2/T1 instead of unconditionally T3, and adds `not other_failed` guard on T2.
- **04a911ec** — Section-name synonym detection. Centralized synonym lists at module top with prefix-match for `## Quiz: <topic>` / `## Hands-On: <topic>` / `## Common Mistakes and How to Avoid Them`.

### First audit complete — `scripts/quality/audit-2026-05-02-v2.jsonl`

Run across all 235 `revision_pending: true` modules with `--skip-source-check`. **Result: 235/235 → T3.**

Top failure gates (post-synonym-fix):
- `body_words_5000`: 234/235 fail
- `sources_min_10`: 233/235 fail
- `density_max_consecutive_short_2`: 231/235 fail
- `density_short_rate_20pct`: 231/235 fail
- `density_median_wpp_28`: 225/235 fail
- `density_mean_wpp_30`: 224/235 fail
- `outcomes_aligned`: 102/235 fail (was 222 pre-synonym-fix)
- `structure_quiz_6_8_with_details`: 163/235 fail
- `structure_common_mistakes_6_8`: 109/235 fail
- `structure_did_you_know_4`: 86/235 fail
- `structure_sections_present`: 82/235 fail (was 217 pre-synonym-fix)

The 100% T3 is **real**, not a verifier bug. Codex's consult predicted "T3 = 45-60% until audit proves otherwise" — empirical answer is 100%. The dominant gate is the 5000-word body floor: most modules are 1000-4500 words. The #388 plan IS to expand all 235 to meet this bar. The 50,000-foot conclusion: every `revision_pending: true` module needs a full rewrite, not a structural patch.

Section-name variants observed across the curriculum (verifier matches all):
- Learning Outcomes: 457 `## What You'll Be Able to Do`, 261 `## Learning Outcomes`, 104 `## What You'll Learn`, 2 `## Learning Objectives`
- Did You Know: 675 `## Did You Know?` (with question mark)
- Common Mistakes: 685 + minor variants
- Quiz: 662 `## Quiz` + 28 `## Knowledge Check` + ~10 `## Quiz: <topic>`
- Hands-On: 324 `## Hands-On Exercise` + variants like `## Hands-On: <topic>`
- Sources: 282 `## Sources`, 165 `## Further Reading`

This is **low-priority cosmetic drift**, not a real problem — "What You'll Be Able to Do" is arguably better pedagogically than "Learning Outcomes" (Bloom's action framing). The verifier handles it; learners don't notice. Annoyance only when (a) site-search for "Learning Outcomes" misses 561 of 822 modules, or (b) a future tool needs section-aware logic and has to redo the synonym table. A one-time normalization sweep (1-2h) when convenient — never a blocker.

### 6 density fix-pass modules merged

All 6 modules from session 5's batch that failed Codex's tighter density bar have been re-fixed and merged. Each PR was Codex-authored, Gemini-reviewed (cross-family), and squash-merged.

| Module | PR | Before max_run | After max_run | Body words after |
|---|---|---|---|---|
| 5.6 Gardener | #726 | 3 (boundary) | 2 | 6873 |
| 5.7 Multi-cluster on-prem | #725 | 19 (worst) | 2 | 6232 |
| 5.8 OpenStack on K8s | #727 | 5 | 1 | 7620 |
| 5.9 VMware Tanzu | #728 | 15 | 0 | 5744 |
| 9.10 BentoML | #729 | 10 | 2 | 6514 |
| 9.11 Bare-metal MLOps | #730 | 9 | 0 | 5001 |

All 6 PRs received APPROVE from Gemini with no needs-changes. Protected assets bit-identical in every case (code blocks, mermaid, ASCII, tables). Section counts (DYK=4, CM 6-8, Quiz 6-8 with `<details>`, Hands-On checkboxes) preserved.

The 9.11 module was the most aggressive — body_words went from 3867 to exactly 5001 (under the 5000 floor → meeting it). Gemini specifically scrutinized this expansion and confirmed the +1134 words are "genuine teaching content (restore testing, network governance, observability contracts, dependency mapping), not padding or restating".

### Codex sandbox limitation persists — manual commits required

Every Codex dispatch reported "Commit was blocked by sandbox permissions: `git add` cannot create `/Users/krisztiankoos/projects/kubedojo/.git/worktrees/<branch>/index.lock` outside writable roots." Memory `feedback_codex_danger_for_git_gh.md` already documents this — workspace-write blocks `.git/worktrees/.../index.lock`. Recovery pattern: Codex writes the file in the worktree, orchestrator manually commits from primary tree (cd into worktree, git add, git commit). Worked 8/8 times this session (verifier MVP, verifier-v2, all 6 fix-pass commits). For Day 2+, consider switching the dispatch mode to `mode="danger"` so Codex can commit directly.

### Codex 2x parallel confirmed under load

Eight concurrent codex dispatches across the session (verifier + 6 fix-passes + verifier-v2). Two were always running simultaneously. No silent failures, no rate-limit cascades. Old memory `feedback_codex_dispatch_sequential.md` is fully superseded — 2x parallel is the operating point.

### Worktree cwd-persistence trap — verifier-v2 nested by accident

When creating `.worktrees/codex-388-verifier-v2`, the bash cwd had drifted into `.worktrees/codex-388-verifier/` from a prior `cd`. `git worktree add .worktrees/codex-388-verifier-v2 ...` resolved relative, creating a nested worktree at `.worktrees/codex-388-verifier/.worktrees/codex-388-verifier-v2`. Codex dispatch then failed with `FileNotFoundError` because the script used the absolute primary-tree path. Fix: always use absolute paths when creating worktrees in long sessions where cwd may have shifted. Memory candidate.

## What's still in flight (next session)

### PR #724 — verifier — awaiting Gemini re-review

Two iterations addressed (kubectl + tier + synonyms). Re-review dispatched to Gemini at session end. Expected outcome: APPROVE — sentinel tiers are correct, tests pass, audit ran clean.

After approve + merge, the audit JSONL `scripts/quality/audit-2026-05-02-v2.jsonl` lands on main and becomes the canonical input for #388 volume planning.

### #388 Day 2: Pilot 8-12 modules

Per Codex's consult — pilot before volume. Pick 8-12 modules across all 4 tracks (Cloud, Certifications, Platform Engineering, Fundamentals) covering different starting word counts (1000, 2500, 4500). For each: dispatch Codex with `module-rewriter-388.md` brief + module-specific topic-coverage bullets, request density gates pass + body_words ≥ 5000, get Gemini cross-family review on each PR before merge. Freeze thresholds based on observed failures. THEN start the 235-module volume run.

### #388 Day 3+: Volume run

Codex 10x window expires 2026-05-17 (15 days). Target: 20-25 modules/day across 2 lanes, batched 3-6 per PR for T1/T2 and 1-2 per PR for T3. All 235 are T3 per the audit, so 1-2 per PR — call it 12 PRs/day max → ~20 days. The window won't quite cover it; either ramp parallelism beyond 2x or expect overflow. Track-level coherence review every 3-4 batches per Codex's consult.

### Carryover from prior handoffs (still open)

- Ch02 line-119 fix from #559 backlog — low priority
- Ch32-Ch37 research-pending under strict-gh audit
- PR #567 review + merge
- PR #558 + #565 — stale-prose cleanup
- Issue #344 — citation-residuals resolver work in worktree
- Google Search Console — waiting on user
- 5.4 fleet-management + 5.5 active-active-multi-site — both `revision_pending: true`, both shallow per assessment; will be picked up in the 235-module #388 sweep

## Cross-thread notes

**ADD:**

- The 235-module #388 audit empirically resolves the tier-distribution question: 100% T3, dominant gate is `body_words_5000`. Plan accordingly — every module is a full rewrite, not a structural patch.
- `scripts/quality/verify_module.py` is now the contract. CI hookable. JSONL audit at `scripts/quality/audit-2026-05-02-v2.jsonl`.
- The 6 fix-passes confirm that 30-45 min per module is realistic for density-only re-fixes (T2-equivalent). Full rewrites (T3) will run longer — budget 60-90 min per module for Day 2+ pilot estimation.
- Section-name variants exist (4 LO conventions, etc.) but it's low-priority cosmetic drift — verifier handles it; learners don't notice. No cleanup needed unless a section-aware tool later wants to skip the synonym table.
- Codex orchestration via `agent_runtime.runner.invoke` + `mode="workspace-write"` requires manual commit recovery. Switch to `mode="danger"` for Day 2 to remove that step.

**DROP / RESOLVE:**

- "TODO: build verify_module.py (Day 1)" — DONE (PR #724)
- "TODO: run verifier across 235 modules" — DONE (audit-2026-05-02-v2.jsonl)
- "TODO: re-fix 6 modules from session 5" — DONE (#725-730 all merged)
- "Codex 2x parallel suspect" — RESOLVED (8 concurrent dispatches without failure)

## Cold-start smoketest (executable)

```bash
# 1. Confirm 6 fix-pass PRs merged
git log --oneline origin/main~7..origin/main | head -7
# expect (newest first):
#   <sha> fix(ml-platforms): density re-pass on module 9.11 bare-metal MLOps (#388 prep) (#730)
#   <sha> fix(ml-platforms): density re-pass on module 9.10 BentoML (#388 prep) (#729)
#   <sha> fix(multi-cluster): density re-pass on module 5.9 VMware Tanzu (#388 prep) (#728)
#   <sha> fix(multi-cluster): density re-pass on module 5.8 OpenStack on K8s (#388 prep) (#727)
#   <sha> fix(multi-cluster): density re-pass on module 5.6 Gardener (#388 prep) (#726)
#   <sha> fix(multi-cluster): density re-pass on module 5.7 multi-cluster-on-prem (#388 prep) (#725)
#   ecbf117b docs(status): handoff 2026-05-01 session 5

# 2. Verifier on main (after PR #724 merges)
ls -la scripts/quality/verify_module.py scripts/quality/test_verify_module.py
ls -la scripts/quality/audit-2026-05-02-v2.jsonl
.venv/bin/python -m pytest scripts/quality/test_verify_module.py -x -v  # 13 passing

# 3. Re-confirm tier distribution
.venv/bin/python scripts/quality/verify_module.py --all-revision-pending --skip-source-check --summary --quiet
# expect: tiers: {"T3": 235}
# expect: top failure_gates body_words_5000=234, sources_min_10=233, density_*=~225-231

# 4. Smoke-check Codex
echo "Reply with exactly OK." | scripts/ab ask-codex \
  --task-id smoke-pre-388-day2 --new-session --from claude --to-model gpt-5.5 -

# 5. Confirm clean tree + worktrees
git status -sb
git worktree list
# expect 4 entries: primary + codex-344 + codex-391 + codex-394 — fix-pass + verifier worktrees gone
```

## Files modified this session

```
scripts/quality/
  verify_module.py             (new, 849 LOC — PR #724)
  test_verify_module.py        (new, 161+ LOC, 13 tests passing — PR #724)
  audit-2026-05-02-v2.jsonl    (new, 235 records — PR #724)

src/content/docs/on-premises/multi-cluster/
  module-5.6-gardener.md                 (re-fix, PR #726 merged)
  module-5.7-multi-cluster-on-prem.md    (re-fix, PR #725 merged)
  module-5.8-openstack-on-kubernetes.md  (re-fix, PR #727 merged)
  module-5.9-vmware-tanzu.md             (re-fix, PR #728 merged)

src/content/docs/platform/toolkits/data-ai-platforms/ml-platforms/
  module-9.10-bentoml.md            (re-fix, PR #729 merged)
  module-9.11-bare-metal-mlops.md   (re-fix, PR #730 merged)

docs/session-state/2026-05-02-1-388-day-1-verifier-and-fix-pass.md  (this file)

STATUS.md  (Latest handoff promotion at session end)
```

## Blockers

(none — Day 2 pilot work ready to start as soon as PR #724 merges)

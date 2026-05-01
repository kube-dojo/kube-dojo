# Session handoff — 2026-05-01 (session 5) — #379 + #385 greenfield shipped, 6/8 fail density audit, #388 prep

> Picks up from `2026-05-01-4-issue-triage-greenfield-prep.md`. This session executed all of #379 Phase A.2 (4 modules) and #385 Phase E.2 (4 modules) as 8 PRs, plus 4 density-fix-pass PRs after the user flagged choppy prose. Codex consulted twice on the #388 architecture; he prescribed verifier-first, pilot-then-volume, and a density-first brief. Audit against Codex's tighter gates shows only 2 of 8 modules from this session actually pass. Next session: build verifier, re-fix the 6 failing modules, then start #388 pilot.

## Decisions and contract changes

### #379 Phase A.2 closed — all 4 greenfield ML platforms modules merged

- 9.8 KServe (#712 → ee7448e5)
- 9.9 Seldon Core (#713 → c598b1e6)
- 9.10 BentoML (#714 → 1e8752f6)
- 9.11 Bare-metal MLOps recipe (#715 → 4ed44e30)

#379 closed.

### #385 Phase E.2 closed — all 4 greenfield on-prem modules merged

- 5.6 Gardener (#716 → fd0b1448)
- 5.7 Multi-cluster on-prem Karmada/Liqo/kube-vip (#717 → 68ad0ac9)
- 5.8 OpenStack on Kubernetes (#718 → cf07b6fd)
- 5.9 VMware Tanzu (#719 → ef497699)

#385 closed.

### Quality discovery — 6 of 8 modules from this session fail Codex's tighter density bar

User flagged 5.7's choppy prose. Audit revealed 4 of 8 modules below the project's 18 wpp threshold. A sentence-fusion fix-pass shipped (PRs #720-723) — improved mean_wpp to 33-37, body words preserved bit-for-bit. But re-audit against Codex's tighter prescription (median_wpp >= 28, mean_wpp >= 30, short_para_rate <= 20%, max_run < 3) shows:

| Module | Verdict | Failed gate |
|---|---|---|
| 9.8 KServe | PASS | — |
| 9.9 Seldon | PASS | — |
| 5.6 Gardener | FAIL | max_run=3 (boundary) |
| 9.10 BentoML | FAIL | max_run=10 |
| 9.11 Bare-metal MLOps | FAIL | short_rate 32%, max_run=9 |
| 5.7 Multi-cluster | FAIL | max_run=19 (worst) |
| 5.8 OpenStack | FAIL | max_run=5 |
| 5.9 VMware Tanzu | FAIL | max_run=15 |

The killer gate is `max_consecutive_short_run`. The fix-pass merged isolated short paragraphs but left clustered runs intact. So the surface metric improved but the failure pattern survived in long stretches. The 6 failing modules need a targeted prose expansion pass — decomposing runs of <18-word paragraphs into flowing prose with topic sentences and elaboration — before they meet the canonical bar.

### Codex consults — 2 architectural reviews

**Consult 1 (bridge msg #3384)** on the proposed 235-module #388 plan:
- wpp >= 20 too low; real floor is median_wpp >= 28, mean_wpp >= 30, short_para_rate <= 20%, no 3+ consecutive short paragraph runs
- body_words >= 0.95 x before is useless for thin originals; need absolute floors (5,000 minimum)
- HTTP 2xx source check insufficient; require primary/vendor docs + relevance assessment
- Tier 1 mechanical patches risk creating fake depth — assume T3 = 45-60% until audit proves otherwise
- 235 PRs will bury review; batch 3-6 per PR for T1/T2, 1-2 for T3
- Cross-module coherence missing — track-level review after each batch
- 4 tiers not 3: T0 (passes — clear flag) / T1 (structural only) / T2 (density only) / T3 (both + thin)
- Do not let Haiku write final content; use it for manifests and labels only
- Salvage manifest = deterministic parser, not LLM extraction
- Verifier = the contract, not the prompt
- PILOT before volume: 8-12 modules across tiers/tracks with cross-family review, freeze thresholds, THEN start the 235-module run
- Highest-leverage Day 1: build deterministic verifier, run across all 235, manually inspect 10 samples, correct tier estimates from real data

**Consult 2 (bridge msg #3386)** asking why Codex's own output violated Codex's prescribed standards:
- Root cause: the brief optimized for coverage and quotas, not density. The "600+ content lines" requirement actively pushed toward short Markdown blocks. Structural quotas put the model into checklist production mode. 8 topic-coverage bullets encouraged section-by-section enumeration.
- Not a high-reasoning fault — high reasoning under heavily structured prompts preserves structure, headings, and short control paragraphs.
- Fix is better prompt constraints + audit gate. Codex's 5 prose-discipline fragments are now canonical at `scripts/prompts/module-rewriter-388.md` (this session) — 5,000-7,000 word target replaces 600+ lines.

### Worktree base must be origin/main strictly (lesson from Seldon contamination)

PR #713 originally shipped contaminated with KServe's 2 commits because the dispatch agent ran "fast-forward to local main HEAD" inside its worktree. Decontamination via reset-hard + cherry-pick + force-push. Subsequent dispatches all used strict origin/main and shipped clean. Memory saved as `feedback_worktree_strict_origin_main.md`.

### Codex 2x parallelism confirmed

Stale memory `feedback_codex_dispatch_sequential.md` was overly pessimistic. User confirmed codex can run 2 dispatches in parallel reliably. The density fix-pass batch ran 2 lanes concurrently (PRs #720-723) with no failures. New operating point: 2x parallel is safe for codex dispatches.

### scripts/ab ask-codex sandbox limitation (worktree creation)

Confirmed via memory `feedback_codex_danger_for_git_gh.md` — `scripts/ab ask-codex` from primary tree fails with sandbox-blocked worktree creation and DNS. Fallback that worked: `codex exec -s danger-full-access -m gpt-5.5 -c model_reasoning_effort=high` from inside the worktree directly.

## What's still in flight (next session)

### Block — #388 Day 1: build verifier + re-fix 6 modules

1. **Build `scripts/quality/verify_module.py`** — codify the audit logic Codex specified. Output JSONL per module with: tier, density stats (mean/median wpp, short_rate, max_run, sentence stats), section presence + order, DYK/Mistakes/quiz counts, hands-on checkbox count, sources count + URL status, protected assets (ASCII/Mermaid/code blocks count), anti-leak grep result, alignment check (each Learning Outcome maps to a section + quiz/lab item). Test on the 4 fix-pass-merged modules + 5.4/5.5 (known-bad). Place at `scripts/quality/verify_module.py`.

2. **Run verifier across all 235 `revision_pending: true` modules**. Output JSONL summary at `scripts/quality/audit-2026-05-02.jsonl`. Manually inspect 10 samples to validate tier classification.

3. **Re-fix the 6 modules from this session** that fail Codex's gates: 5.6, 5.7, 5.8, 5.9, 9.10, 9.11. Use the new brief at `scripts/prompts/module-rewriter-388.md`. 2 lanes parallel. Each fix is targeted at `max_consecutive_short_run` — decompose long runs of <18-word paragraphs into flowing prose with topic sentences and elaboration. Body word count must not drop below the absolute floor (5,000+).

4. **Pilot 8-12 modules from the 235** with cross-family review. Freeze thresholds on observed failures. Codex review on each pilot PR before merge.

5. **Volume run**: 2 lanes, 20-25 modules/day across both lanes, batched 3-6 per PR for T1/T2 and 1-2 per PR for T3. Codex 10x window expires 2026-05-17 (15 days from 2026-05-01); approximately 50 min/day average dispatch time fits.

### Carryover from prior handoffs (still open)

- Ch02 line-119 fix from #559 backlog — low priority
- Ch32-Ch37 research-pending under strict-gh audit
- PR #567 review + merge
- PR #558 + #565 — stale-prose cleanup
- Issue #344 — citation-residuals resolver work in worktree
- Google Search Console — waiting on user
- 5.4 fleet-management + 5.5 active-active-multi-site — both `revision_pending: true`, both shallow per assessment; will be picked up in the 235-module #388 sweep, no separate action needed

## Cross-thread notes

**ADD:**

- 8 greenfield modules merged this session (#379 + #385 closed) but only 2 of 8 (KServe, Seldon) actually pass Codex's full density bar. The 4 fix-pass merges (#720-723) improved mean_wpp but did not eliminate `max_consecutive_short_run`. Next session must re-fix 6 modules.
- `scripts/prompts/module-rewriter-388.md` is now the canonical brief addendum for all #388 dispatches. Layered on top of `module-writer.md`. Codex's 5 prose-discipline fragments verbatim plus 5,000-7,000 word target replacing 600+ lines.
- Codex 2x parallel capacity confirmed for codex dispatches (stale `feedback_codex_dispatch_sequential.md` superseded).
- The user's quality bar is Codex's tighter prescription (median_wpp >= 28, max_run < 3), not the project's older 18-wpp threshold. The verifier built next session must enforce Codex's gates as canonical.
- Build is ~38s for 1,999-2,011 pages (CLAUDE.md already updated this session from stale 1,297 value).

**DROP / RESOLVE:**

- "TODO: KServe dispatch staged, fire next session" — DONE (#712 merged ee7448e5)
- "TODO: KServe brief at `/tmp/kserve_dispatch_brief.md`" — superseded by full execution
- "TODO: greenfield priority order before #388" — executed; #379 + #385 closed; #388 is next phase

## Cold-start smoketest (executable)

```bash
# 1. Confirm 12 issues open + #379 + #385 closed
gh issue list --state open --limit 60 --json number --jq 'length'  # expect 12
gh issue view 379 --json state -q .state                            # expect CLOSED
gh issue view 385 --json state -q .state                            # expect CLOSED

# 2. Confirm main has all 8 + 4 merges
git log --oneline origin/main~14..origin/main | head -16
# expect (newest first):
#   cc80d27e fix(ml-platforms): density fix-pass on module 9.10 BentoML (#388 prep) (#723)
#   1e6d086f fix(on-premises): density fix-pass on module 5.9 vmware-tanzu (#388 prep) (#722)
#   d62c8648 fix(multi-cluster): density fix-pass on module 5.8 OpenStack on Kubernetes (#388 prep) (#721)
#   e4cefc0e fix(on-premises): density fix-pass on module 5.7 multi-cluster-on-prem (#388 prep) (#720)
#   ef497699 feat(multi-cluster): module 5.9 VMware Tanzu (#385) (#719)
#   cf07b6fd feat(multi-cluster): module 5.8 OpenStack on Kubernetes (#385) (#718)
#   68ad0ac9 feat(multi-cluster): module 5.7 multi-cluster on-prem (Karmada + Liqo + kube-vip) (#385) (#717)
#   fd0b1448 feat(multi-cluster): module 5.6 Gardener (#385) (#716)
#   4ed44e30 feat(ml-platforms): module 9.11 bare-metal MLOps recipe (#379) (#715)
#   1e8752f6 feat(ml-platforms): module 9.10 BentoML (#379) (#714)
#   c598b1e6 feat(ml-platforms): module 9.9 Seldon Core (#379) (#713)
#   ee7448e5 feat(ml-platforms): module 9.8 KServe (#379) (#712)

# 3. Confirm canonical brief addendum landed
ls -la scripts/prompts/module-rewriter-388.md  # should exist

# 4. Confirm verifier NOT yet built (Day 1 of next session builds it)
ls scripts/quality/verify_module.py 2>/dev/null  # should NOT exist

# 5. Smoke-check Codex
echo "Reply with exactly OK." | scripts/ab ask-codex \
  --task-id smoke-pre-388-day1 --new-session --from claude --to-model gpt-5.5 -

# 6. Confirm clean tree + worktrees
git status -sb
git worktree list
# expect 4 entries (primary + codex-344 + codex-391 + codex-394 — no greenfield worktrees)
```

## Files modified this session

```
src/content/docs/platform/toolkits/data-ai-platforms/ml-platforms/
  module-9.8-kserve.md            (new, ee7448e5)
  module-9.9-seldon-core.md       (new, c598b1e6)
  module-9.10-bentoml.md          (new, 1e8752f6 + density fix cc80d27e)
  module-9.11-bare-metal-mlops.md (new, 4ed44e30)
  index.md                        (updated for 9.8-9.11)

src/content/docs/on-premises/multi-cluster/
  module-5.6-gardener.md                (new, fd0b1448)
  module-5.7-multi-cluster-on-prem.md   (new, 68ad0ac9 + density fix e4cefc0e)
  module-5.8-openstack-on-kubernetes.md (new, cf07b6fd + density fix d62c8648)
  module-5.9-vmware-tanzu.md            (new, ef497699 + density fix 1e6d086f)
  index.md                              (updated for 5.6-5.9)

src/content/docs/changelog.md (entries for all 8 modules)

CLAUDE.md (page count drift fix: 1,297 → 1,999, earlier this session)

scripts/prompts/module-rewriter-388.md (new — canonical #388 brief addendum)

docs/session-state/2026-05-01-5-greenfield-shipped-388-prep.md (this file)

STATUS.md (Latest handoff promotion)
```

## Blockers

(none — verifier-first plan ready to execute next session)

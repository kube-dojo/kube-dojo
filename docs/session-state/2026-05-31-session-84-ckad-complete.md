# Session 84 — CKAD TRACK 100% (review axis, 24/24 `done`) via 5 waves

**Date:** 2026-05-31 · **Predecessor:** [session 83](2026-05-31-session-83-cka-part5-and-cka-complete.md)

## What happened

Drove the proven review-first loop across the **entire CKAD sub-track** in curriculum order, part0 →
part5. 21 modules taken from `needs_review`/`shipped_unreviewed` → `done` (3 were already done: 0.2,
1.4, 3.1). Board review-axis **342 → 363**. CKAD is now **24/24 `done`**.

Process change vs session 83: **per-wave consolidated PRs** (the session-78 integration-branch pattern)
instead of per-module PRs — one PR per part, cherry-picking the per-module fix commits (each fixer in
its own worktree → race-safe; each commit single-file scoped). 5 PRs total (#1722–#1726) vs 21.

### The 5 waves

| Wave | Part | Modules | PR | Real P1s |
|---|---|---|---|---|
| 1 | part0 + part1 | 0.1, 1.1, 1.2, 1.3 | #1722 | **1.2 had FOUR** (see below); 0.1 dead-URL; 1.3 nslookup |
| 2 | part2-deployment | 2.1, 2.2, 2.3, 2.4 | #1723 | **2.2 Helm `--reuse-values`** |
| 3 | part3-observability | 3.2, 3.3, 3.4, 3.5 | #1724 | none (all P2) |
| 4 | part4-environment | 4.1, 4.2, 4.3*, 4.4, 4.5, 4.6 | #1725 | **4.1 delete-cm**, **4.6 explain-race** |
| 5 | part5-networking | 5.1, 5.2, 5.3 | #1726 | none (all P2) |

\* **4.3-resources reviewed APPROVE 4.7/5 with ZERO findings** (codex ran all 6 lab tasks live —
OOMKilled/exit-137, QoS classes, LimitRange defaults) → finalized **as-is** (no fix, no PR commit;
just the review record + stage flip). First clean module of the whole CKA/CKAD sweep.

### Notable real defects fixed (rubric-green ≠ correct, again)

- **1.2-jobs-cronjobs — NEEDS_CHANGES 3.0/5, FOUR P1s** (codex ran the labs on kind v1.35.0):
  (1) GitLab-2017 + an anonymized war-story stated as fact → reframed to `Hypothetical scenario:`
  (also dodges the incident-dedup gate; GitLab DB incident is better-homed in storage/DR modules);
  (2) `$JOB_COMPLETION_INDEX` used in NonIndexed Jobs (empty on 1.35) → added `completionMode: Indexed`;
  (3) `kubectl logs job/<name>` run before completion → guarded with `kubectl wait --for=condition=complete`;
  (4) every-minute CronJob drill logged `items[0]` (a prior drill's Job) → selects the CronJob-owned Job.
- **2.2-helm P1** — "only replica count changes" was false: `helm upgrade --set` without `--reuse-values`
  resets prior overrides (service.type) to chart defaults → added `--reuse-values` + footgun callout.
- **4.1-configmaps P1** — `kubectl delete pod drillN cm drillN` parses `cm` as a pod name → ConfigMaps
  never deleted → slash notation `pod/drillN cm/drillN` (all 4 drills).
- **4.6-crds P1** — `kubectl explain <cr>.spec` races CRD establishment → `kubectl wait --for
  condition=established` + `until kubectl explain` retry across all CRD explains.
- **0.1** dead CNCF curriculum URL → `CKAD_Curriculum_v1.35.pdf` (verified present); **1.3 / 3.2 / 3.3**
  busybox `nslookup` short-name + `kubectl logs --previous` timing fragility (FQDN + restart-count gates).
- Recurring P2 classes across the track: frontmatter `duration` vs body mismatch; unlinked sibling
  prerequisites; `kubectl explain` GROUP/VERSION two-field format on 1.35 (3.5); `kubectl top node`
  Allocatable-vs-Capacity (3.4); Helm 4 `--dry-run=client` deprecation (2.2).

**~96% NEEDS_CHANGES/APPROVE_WITH_NITS** (only 4.3 clean). Confirms the back-catalog pattern yet again.

### Build verification
Full `npm run build` in PRIMARY after all 5 merges: **2129 pages, 40.07s, Complete!**, 0 errors.

## CURRENT STATE (exact)
- **Board review-axis `done`: 342 → 363** (+21 CKAD). `/api/quality/board` CKAD = 24/24 `done`.
- **CKAD TRACK 100% COMPLETE on the review axis.** Prereqs (44/44) + linux (37/37) + ai + CKA (41/41)
  + CKAD (24/24) all done. **k8s track: CKA + CKAD done; next k8s sub-track = `cks`.**
- Primary main CLEAN at the latest merge, in sync with origin. All session worktrees pruned (primary only).
- No ScheduleWakeup active. No open CKAD PRs.

## IMMEDIATE NEXT STEPS
1. **Next sub-track in curriculum order: `cks`** (then kcna → kcsa → extending → tool certs → cloud 85
   → ai-ml-eng → on-prem → platform). Same review-first loop.
2. **No cks review prompts pre-generated** — generate from `logs/remediation/briefs/session84/gen-review-prompt.sh`
   (generic CKAD/k8s template; just point at `k8s/cks/...` paths — tweak the CKAD-specific paragraph
   to CKS security focus if desired). Finalize via the `finalize-waveN.sh` pattern (copy + edit paths/summaries).
3. Per-wave consolidated PR pattern (this session) is more efficient than per-module — keep it: each
   fixer in its own worktree, cherry-pick single-file commits onto a `ckad-w{N}-integration` branch,
   one PR per part.

## Roster note (this session)
- **cursor `--model auto` = workhorse** — the bulk of reviews + fixes (all clean, in-cluster
  verification, accurate findings, single-file commits). **codex gpt-5.5** = the heavy/cluster-verify
  lane (1.2 four-P1 jobs module, 4.6 CRD explain-race, 5.3 NetworkPolicy + connectivity-test
  determinism, 3.4/3.5/4.3/2.3 reviews); used `draft`-class + `--timeout 3600` for fixes.
- **codex draft fixes consistently exit 1 with the stale-branch advisory** (`remote=missing`) — this is
  NOT a failure; the commit lands cleanly in the worktree. Verified ground-truth every time
  (`git -C <wt> log/status`), then cherry-picked. (Memory: `feedback_dispatch_smart_stale_branch_check_is_advisory`,
  `feedback_codex_sigkill_at_timeout_recover_from_worktree`.) No actual SIGKILL this session.
- 3-in-flight mixed batches (≤2 per OAuth) held the burst limit — zero rate-limit hits across ~24
  reviews + ~21 fixes. gemini-cli not used (was exhausted at session start; didn't retest). agy/deepseek not used.
- PR CI = the de-facto build/link gate for content-only edits (site-health + incident-dedup + CodeQL +
  gemini-3.1-pro cross-family review — all green on every PR).

## Lessons / reaffirmed
- Review-first on already-dense back-catalog keeps surfacing **real** defects — multiple P1s
  (data-shape, runnability, broken cleanup, dead URLs) under rubric-green/T0 modules.
- **Ground-check every fixer diff** + literal-complete sibling-grep briefs: caught nothing-bad this
  session (all fixes landed correct first-pass), but the discipline is why.
- **A clean APPROVE-no-findings module (4.3) just needs a review record + stage flip — no PR.** The
  finalize bridge works without any content change.
- Reusable artifacts this session: `logs/remediation/briefs/session84/gen-review-prompt.sh` (prompt
  generator), `fix-ckad-*.md` (briefs), `finalize-wave{1..5}.sh` (finalize scripts).

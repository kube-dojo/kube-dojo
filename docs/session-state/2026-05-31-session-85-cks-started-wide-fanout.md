# Session 85 — CKS track STARTED with wide parallel fan-out (8/30 done; part0 4/4 + part1 4/5; batches 1+2 merged)

**Date:** 2026-05-31 · **Predecessor:** [session 84](2026-05-31-session-84-ckad-complete.md)

## What happened

After session 84 finished CKAD, the user flagged that the night's run only consumed **61% of the
weekly agent quota** with a next-morning reset — wasted use-it-or-lose-it capacity — and to **fan out
much wider**. Locked that in as memory `feedback_burn_weekly_capacity_before_reset` and pivoted: started
the **CKS (security) track, 30 modules** (22 shipped_unreviewed + 5 needs_review + 3 needs_rewrite,
0 done) with **8+ concurrent dispatches across 4 pools** (cursor ×2, codex ×2, gemini ×2, agy ×2) —
beating the per-OAuth burst limit by spreading across pools, not serializing.

### Reviewed: all of part0 (0.1–0.4) + part1 (1.1–1.3, 1.5). Briefs on disk in `logs/remediation/briefs/session85/`.

| Module | Verdict | Headline finding | Reviewer |
|---|---|---|---|
| 0.1-cks-overview | NC 4.4/5 | Task-4 jsonpath emits container-name only; audit-logging mis-budgeted as quick win; "15-20 tasks"→~17 | cursor |
| 0.2-security-lab | NC 4.1/5 | 8×P2: kube-bench version split, missing audit-proof step, kubectl-run vs SA race, node-checks on wrong host (kind-on-macOS), kubesec amd64-only | cursor |
| 0.3-security-tools | NC 3.5/5 | **P1** kube-bench CIS check IDs wrong for cis-1.12 profile; Falco ConfigMap rule not loaded | codex |
| 0.4-exam-strategy | NC 3.8/5 | **P1** AppArmor lab uses deprecated annotation + only checks annotation not enforcement | codex |
| 1.1-network-policies | NC | **P1** lab targets had no listener + no Services (curl/DNS fail) → nginx+`--expose`; dead Calico URL | cursor |
| 1.2-cis-benchmarks | NC 3/5 | **P1** kube-bench Job lacks control-plane nodeSelector/tolerations → runs on worker → spurious FAILs | gemini |
| 1.3-ingress-security | NC | **P1** ingress-nginx Deployment omits `spec.selector`/template labels + `registry.k8s.sio` typo→ImagePullBackOff | gemini (re-review) |
| 1.5-gui-security | NC 3/5 | **P1** `ingress: []` also drops apiserver-routed `kubectl proxy` (comment wrong) → use `port-forward` | gemini |
| 2.1 / 2.2 | NC | (part2; briefed) 2.1 RBAC Task-2 comment contradicts lab; 2.2 references SAs/pods never created → NotFound | cursor |

### Merged + finalized (8 CKS modules → `done`; board 363→371)
- **PR #1727 (batch 1) MERGED + finalized:** 0.1, 1.1, 1.5.
- **PR #1728 (batch 2) MERGED + finalized:** 0.2, 0.3, 0.4, 1.2, 1.3 (1.3 folded in after codex recovery).
- **part0 = 4/4 done; part1 = 4/5 done** (only 1.4 remains — see below). All verified T0, CI green, worktrees pruned.
- Recovery notes that worked: the untracked `&` 0.2 dispatch DID eventually commit (don't repeat the `&`
  pattern though); codex 1.2 + 1.3 both exited-1 (stale-branch advisory) but had committed cleanly —
  recovered from the worktree. cursor `edit` fixes needed a manual `git add -A && commit`.

## needs_rewrite triage (density-checked the LIVE files — IMPORTANT, differs from CKA/prereqs)
- **1.4-node-metadata = GENUINE rewrite/expansion** — live file is only **1358 body_words** (T3, fails
  4 structure gates). Route to a T0-author expansion (codex/cursor), NOT a light review-fix.
- **5.4-admission-controllers (5116w) + 6.1-audit-logging (5007w) = STALE needs_rewrite** — already T0;
  treat as normal review-fix.

## Roster lessons (this session)
- **agy DROPPED for CKS reviews** — timed out without a verdict on 1.3 AND 2.3 (stream-of-consciousness,
  no compiled review); thin on 1.4. Reviews = **cursor + codex + gemini** only.
- **gemini-3.1-pro is a solid reviewer** (caught real P1s on 1.2/1.5/1.3) BUT: (a) its **line numbers are
  frequently OFF** — always ground-check + correct lines in the brief; (b) it repeatedly raises a FALSE
  P2 "module activities must meet 8+ activities/12+ items density" — that's a **learn-ukrainian
  language-track rubric, NOT applicable to kubedojo** — auto-reject it.
- **cursor `edit` fixes this session did NOT auto-commit** ("ready for `chore(content):` commit when you
  want it") — orchestrator must `git add -A && commit` the worktree. (Differed from CKAD waves; watch for it.)
- **Do NOT dispatch with a shell `&`** — use `run_in_background: true` so the harness tracks completion.
  The untracked 0.2 dispatch is the cautionary example.
- gemini-cli IS reset (was exhausted session 84). codex draft fixes still exit-1 = stale-branch advisory.

## IMMEDIATE NEXT STEPS (next session — keep WIDE per the capacity rule)
**CKS state: 8/30 done. Remaining 22 = 17 shipped_unreviewed + 2 needs_review + 3 needs_rewrite (1.4
genuine; 5.4/6.1 stale).**
1. **Expand 1.4-node-metadata to T0** (genuine rewrite, currently 1358 body_words → ~5000) via
   curriculum-writer (codex/cursor T0 author + cross-family review). This is the only part0/part1 gap.
2. **Review + fix parts 2-6** in curriculum order. **2.1 + 2.2 briefs already written**
   (`logs/remediation/briefs/session85/fix-cks-2.1.md`, `fix-cks-2.2.md`) — fire those fixes first.
   **2.3-api-server-security needs a fresh review** (agy timed out on it). Then 2.4, 2.5, part3 (3.1-3.4),
   part4 (4.1-4.4), part5 (5.1-5.3; 5.4 stale-T0), part6 (6.1 stale-T0, 6.2-6.4). All 30 review prompts
   pre-generated in `logs/remediation/briefs/session85/review-cks-*.md`.
3. **Fan out WIDE** (cursor + codex + gemini, ≤2/OAuth, 6+ concurrent — agy DROPPED); per-wave
   consolidated PRs (cherry-pick single-file commits onto `cks-batchN`). **cursor `edit` may not
   auto-commit → commit the worktree yourself.** Ground-check every verdict (gemini line numbers are
   often off; reject its false "8+ activities/12+ items density" P2).

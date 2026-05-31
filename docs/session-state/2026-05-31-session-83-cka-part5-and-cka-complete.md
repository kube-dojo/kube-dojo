# Session 83 — CKA part5-troubleshooting (5.1–5.7 → done) + 2.6 straggler → CKA TRACK COMPLETE

**Date:** 2026-05-31 · **Predecessor:** [session 82](2026-05-31-session-82-cka-part4-storage.md)

## What happened

### 1. CKA part5-troubleshooting wave — 5.1–5.7 reviewed → fixed → done
Same proven review-first loop (content already T0/dense; this is the cross-family **review** pass
that flips each module to `done`). Reviewers mixed to avoid OAuth burst: **cursor `--model auto`**
(5.1, 5.2, 5.3, 5.5, 5.6) + **codex gpt-5.5** (5.4, 5.7), ≤3 in flight, ≤2 per OAuth. gemini-cli
still exhausted; agy/deepseek not used. **6 of 7 NEEDS_CHANGES; 3 carried REAL P1s.**

| Module | Verdict | Real P1 / key findings | Fixer | PR |
|---|---|---|---|---|
| 5.1-methodology | APPROVE_WITH_NITS 4.4/5 | **Review-record BACKFILL** — was hollow-`done` (COMMITTED, no review record). 4 P2: duration 30→60; Q6 `k top`→full `kubectl`; Part-5 subsection numbering collided with the 5.1 slug (→ descriptive headings + new `## Part 6`); unanchored source | cursor | #1719 |
| 5.2-application-failures | NEEDS_CHANGES 4.1/5 **P1** | **OOM lab `progrium/stress` (Docker schema-v1) rejected by containerd v2.1+ on K8s 1.35 → never OOMKills** → `polinux/stress` + `command:[stress]`; wget→curl; +multi-container Q8; describe/jsonpath primary over flaky `--previous`; portable `sed -i.bak` | cursor | #1714 |
| 5.3-control-plane | NEEDS_CHANGES 4.4/5 **P1** | **etcd snapshot-restore block never stopped the etcd static pod nor pointed `etcd.yaml` at the restored data dir → snapshot silently ignored (data-loss class)** → full correct sequence (stop apiserver+etcd, restore clean dir, sed hostPath, verify etcd health, then apiserver); +certs-renew static-pod restart; `awk NR==1`→`tail -1`; deployment/test cleanup; prereq links | codex (draft) | #1716 |
| 5.4-worker-nodes | NEEDS_CHANGES 4.0/5 | no P1, 5 P2: worker-node ports table split from control-plane ports; `evictionHard` imagefs.inodesFree + MergeDefaultEvictionSettings warning; unguarded `crictl rm`→`xargs -r`; `du`→`sudo du`; "containerd/docker"→configured CRI runtime. **Caught a fixer regression:** dedup dropped sources 10→9 (T3) → added Ports-and-Protocols 10th source (backs the new table) → back to T0 | cursor | #1715 |
| 5.5-networking | APPROVE 4.4/5 + 3 verified P2 | **NetworkPolicy "additive allow" mermaid taught a wrong model** → a connection needs BOTH source egress AND dest ingress (additive union is per-direction); busybox `nslookup` short-name NXDOMAIN→FQDN-first; `kubectl debug --target+--share-processes` | cursor | #1717 |
| 5.6-services | NEEDS_CHANGES 4.5/5 | no P1, 3 P2: EndpointSlice inspection had no command → added `kubectl get endpointslices -l kubernetes.io/service-name` + made it the primary check throughout; `netstat`/`ss` absent from `nginx:1.25`→client `wget` probe; in-cluster NodePort-via-node-IP fails on kind→Task 3 caveat | cursor | #1718 |
| 5.7-logging-monitoring | NEEDS_CHANGES 3.8/5 **2×P1** | **(1) `kubectl logs deployment/<name>` presented as all-replicas but selects one pod → `--all-pods=true`; (2) resource-usage ASCII diagram taught usage>>requests → OOMKilled (wrong)** → split memory-limit→OOMKilled vs CPU-limit→throttled vs requests→scheduling/eviction. P2: `kubectl run --serviceaccount` (not a flag)→`--overrides`; Event-TTL cited | codex | #1720 |

Every fix: literal-complete brief (sibling-grep), ground-checked vs the diff, `## Learner check`
added, verify_module T0, `chore(` prefix. **All 7 PRs merged + finalized to `done`** via
`logs/remediation/briefs/session83/finalize-part5.sh`. CI green on every PR (site-health +
incident-dedup + CodeQL + CI cross-family). Wave worktrees cleaned. Note: 5.1's review prompt was
generated this session (`logs/remediation/briefs/session79/review-cka-5.1-methodology.md`).

### 2. Closed the last CKA straggler — 2.6-scheduling (stale needs_rewrite → done)
After part5, the board showed CKA at 40/41 with `2.6-scheduling` flagged `needs_rewrite` (stage
FAILED). Density-checked the **live** file → already **T0** (rubric 5.0, 5026 words): classic stale
`needs_rewrite` (`feedback_needs_rewrite_often_stale_not_real`), NOT a rewrite. Ran the same loop:
cursor review → NEEDS_CHANGES 4.3/5, no P1, 3 real P2 (Drill 1 ran two same-name pod-creation paths
→ `AlreadyExists`; topology-spread outcome never exercised → added Drill 7; custom `zone` label
inconsistency) → cursor fix → **PR #1721** → finalize.

### 3. Build verification
Full `npm run build` in PRIMARY after the part5 merges: **2129 pages, 46.72s, Complete!**, 0 errors.

## CURRENT STATE (exact)
- **Board review-axis `done`: 335 → 342** (part5 +6 net since 5.1 was already `done`; 2.6 +1).
  (`/api/quality/board` `status`: was done 335 / needs_review 78 / shipped_unreviewed 218 /
  needs_rewrite 176 at session-82 close.)
- **CKA TRACK 100% COMPLETE on the review axis — 41/41 `done`.** (waves 1–6 + part4-storage +
  part5-troubleshooting + 2.6 straggler.)
- Primary main CLEAN, in sync with origin. All session worktrees cleaned.
- No ScheduleWakeup active.

## IMMEDIATE NEXT STEPS
1. **Next track in curriculum order: `ckad`** (then cks → kcna → kcsa → extending → tool certs →
   cloud(85) → ai-ml-eng → on-prem → platform). Same review-first loop.
2. **No CKA review prompts pre-generated for ckad** — generate them from the template
   (`logs/remediation/briefs/session79/review-cka-5.2-application-failures.md` is the canonical form;
   swap the path + section).
3. Finalize via the `finalize-part5.sh` pattern (copy + edit module paths/summaries).

## Roster note (this session)
- **cursor `--model auto` = the workhorse** (Pro+ 3×): 7 reviews + 8 fixes, all clean, in-cluster
  verification, accurate findings. **codex** healthy: 2 reviews + 1 draft-class fix (5.3 etcd), no
  SIGKILL. 3-in-flight mixed batches (≤2 per OAuth) held the burst limit — zero rate-limit hits.
- **gemini-cli still EXHAUSTED** (was due to reset ~22:00 2026-05-31).
- PR CI is the de-facto build/link gate for content-only edits (Site health link check + Incident
  dedup + CodeQL + CI cross-family review all run per PR).

## Lessons / reaffirmed
- Review-first on already-dense back-catalog keeps surfacing **real** defects (~86% NEEDS_CHANGES,
  3 true P1s this wave: etcd-restore data-loss, logs-not-all-pods, OOM-vs-requests). rubric-green ≠
  correct.
- **Ground-check every fixer diff** — caught the 5.4 source-dedup T0→T3 regression before merge and
  restored it with a relevant 10th source (Ports-and-Protocols) rather than reverting the dedup.
- **Hollow `done` is real**: 5.1 was COMMITTED with no review record. Backfilling a genuine review
  (and applying its 4 P2) makes the `done` honest.
- `needs_rewrite` is usually stale (2.6 was already T0) — density-check the LIVE file first.

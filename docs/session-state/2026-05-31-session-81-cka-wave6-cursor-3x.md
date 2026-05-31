# Session 81 — CKA wave 6 (3.6 + 3.7) + Cursor Pro+ 3× roster

**Date:** 2026-05-31 · **Predecessor:** [session 80](2026-05-31-session-80-cka-wave5.md)

## What happened

### 1. User request — agent routing + usage report (Cursor now Pro+ 3×)
Delivered in-chat. 7-day dispatch usage (from `logs/dispatch_responses/smart-<agent>-*` filenames):
codex 57 · cursor 53 · agy 28 · gemini 16 · **deepseek 13 💲** · **hermes 8 💲** · claude 3.
**Decision:** Cursor Pro+ 3× is now the cheapest flat-rate capacity → make it the high-volume
workhorse (bug-fix, cross-family review of codex/claude-authored, edits, **co-primary T0 author**
paired with codex R1). Reserve codex's scarce weekly cap for accuracy-critical work. **Stop
routing to metered deepseek** (move those ~13 to cursor). Subscription-priority:
**cursor(3×) > codex > agy > gemini-cli > claude**; avoid metered hermes/opencode/qwen/deepseek
unless only they fit. Policy saved to memory `feedback_cursor_proplus_3x_roster.md`.

### 2. CKA wave 6 — 3.6-network-policies + 3.7-cni (the endorsed next item)
Proven review-first loop. Both reviewed by **cursor `--model auto`** (in-cluster verified, strong):
- **3.6 network-policies** → NEEDS_CHANGES 4.4/5, no P1, 5×P2. Fixed by **cursor**. PR **#1707**.
  (from-empty-list reveal, node→pod ingress note, `kubernetes.io/metadata.name`, TCP/53 DNS egress, Drill-8 consistency.)
- **3.7 cni** → NEEDS_CHANGES 4.6/5, **one real P1**: module wrongly said nftables is the *default*
  kube-proxy mode in 1.33+ (it's iptables; nftables is GA-but-opt-in; contradicted sibling 3.1 +
  verified live). Fixed by **codex** (draft+gpt-5.5+timeout-3600). PR **#1708**. (P1 + CNI-netns
  diagram ownership + kindnet greps + ConfigMap-first mode detection.)
- Both: verifier T0 `passed: true`, Learner-check verbatim, **build green in primary**, `chore(` prefix.

## CURRENT STATE (exact)
- **PR #1708 (3.7): CI fully green** (7 pass, 1 skip) — ready to rebase-merge.
- **PR #1707 (3.6): 6 pass, "Incident dedup gate" pending** — merge once it goes green.
- Primary: **CLEAN**, in sync with origin.
- **NOT done yet:** neither PR merged; **3.6/3.7 NOT yet finalized to `done`** on the board.
- **Skill-file roster edits were REVERTED from primary and never committed** (commit got cancelled
  mid-batch). The Cursor-3× policy lives in memory only — that's fine for cold-start (orchestrator
  reads memory), but if you want it in the skill files too it's a small redo. Branch
  `chore/roster-cursor-3x` exists locally at base only (no commit, not pushed).
- **No ScheduleWakeup active** (the one I set got cancelled in the errored batch).

## IMMEDIATE NEXT STEPS
1. `gh pr merge 1708 --rebase` (green now); `gh pr merge 1707 --rebase` once dedup gate passes.
2. `git fetch && git pull` primary main.
3. **Finalize 3.6 + 3.7 to `done`** via the `session78/finalize.sh` pattern: append
   `## <ts> — \`REVIEW\` — \`APPROVE\`` (last line) to `.pipeline/reviews/<key__>.md` for each, then
   `.venv/bin/python -m scripts.quality.pipeline reset-stage <slug> COMMITTED`.
   Keys: `k8s__cka__part3-services-networking__module-3.6-network-policies` (slug with `-`), same for 3.7.
4. **Clean worktrees:** `cka36-fix`, `cka37-fix`, `skill-roster` (+ pre-existing `cka-r-32`, `docs79`,
   `review-codex` are from earlier sessions — leave unless stale).
5. **Then CKA part4 (4.1–4.5 storage)** — same loop. Review prompts for the rest of CKA are
   pre-generated at `logs/remediation/briefs/session79/review-cka-*.md`.

## Lessons saved to memory this session
- `feedback_never_read_build_logs` — **NEVER `Read` a build/log file** (astro build = ~5,600 lines /
  ~110K tokens of route-manifest JSON). grep/tail only. No scattergun parallel probe/flush commands.
  *(This was the session's main context-waste cause — user flagged it.)*
- `feedback_cursor_proplus_3x_roster` — the 3× routing shift + the **redirect-banner trap** (the
  `>`-redirected wrapper file holds only the `[smart]` banner; the real verdict/summary is at the
  printed `response_path` / `smart-<agent>-<class>-<id>.txt`) + the **same-worktree race** (never fire
  a 2nd write-dispatch at a worktree with one in flight; check `git -C <wt> log/status` before
  declaring a dispatch dead — an "instant" draft/edit is almost always still running).

## Roster note (this session)
- gemini-cli still EXHAUSTED (resets ~22:00 2026-05-31). cursor `--model auto` proved a reliable,
  accurate reviewer + author this session. codex healthy (use draft+gpt-5.5+timeout-3600 for content fixes).

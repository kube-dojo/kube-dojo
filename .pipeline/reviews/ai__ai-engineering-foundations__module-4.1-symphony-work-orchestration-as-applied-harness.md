## 2026-06-18T00:20:05Z — `REVIEW` — `APPROVE`
**Reviewer:** opus-inline (cross-family, web/source-verified vs upstream SPEC.md) + codex gpt-5.5 R1 → cursor fix → opus re-review. **PR #2022 (#2020).** Author: #1530 capstone. Verdict path: NEEDS_CHANGES → fixed → **APPROVE.**

P1 (fixed, commits 578da3151 + 1729412f7):
1. (L443) Fabricated quote — spec "explicitly states … 'technically just a SPEC.md file'" + false "no required binary". Real openai/symphony SPEC.md never uses that phrase and requires a coding-agent executable (Codex app-server, SPEC.md L143). Corrected.
2. Symphony WORKFLOW.md schema stale vs upstream: `interval_seconds`→`polling.interval_ms`, `polling.max_concurrent_agents`→`agent.max_concurrent_agents`, `kind: simulated`→`linear` (mock adapter noted). Propagated to validate_contract, poller, quiz, Did-You-Know, checklist (0 residual old names).
3. Claude Code hooks misattributed (cited `before_run`/`after_run` — those are Symphony's) → corrected to real events PreToolUse/PostToolUse/UserPromptSubmit/SessionStart/Stop.
4. GitHub ETag/conditional-request atomic-claim — GitHub REST has no conditional requests on POST label endpoints → reframed to optimistic label-claim + read-back reconciliation.
5. Poller capped at 2 but lab asks to observe issue-3 retry → cap raised to 3 so issue-3 is processed; INTERVAL derived from config.

Verified: openai/symphony repo real; hook names + WORKFLOW.md contract ✓. P2: Linear mutation-ID optimistic-concurrency claim softened (codex couldn't fully verify); dropped unverified "Lopopolo" author attribution. Excluded codex over-reach: learner `git worktree add` lab steps.

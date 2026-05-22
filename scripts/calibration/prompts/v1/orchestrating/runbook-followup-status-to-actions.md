Turn this KubeDojo shift hand-off into structured follow-up.

Status update, 07:40:
Overnight calibration wave `2026-05-23-orch-smoke` was not a real wave, but 12 cells were queued anyway after a dry-run flag got dropped in one dispatch wrapper.
Ledger shows 7 completed, 3 stuck `in_flight` for 96 minutes, and 2 never got a result row; I think the missing rows are a silent push failure, but I have not confirmed.
`scripts/dispatch_smart.py --agent codex review` timed out twice on the same code-review cell; the log is `.pipeline/logs/calibration/2026-05-23/orch-smoke-codex-review.log`.
Gemini fact-check workers hit a 429 storm between 02:10 and 02:48, then recovered; no one has checked whether retries duplicated ledger rows.
PR #1459 is waiting on a security-review author response, and the reviewer says they will not re-review until the branch tip changes.
The branch `feat/calibration-orchestrating-fixture-2-schedule-plan` may have pushed, but Slack only has "pushed maybe"; we need remote confirmation before rebasing this fixture.
There is an old worktree `.worktrees/calibration-fixture-2` whose lease says `active`, but its process is gone; not sure if that is the same branch or a stale lease.
I penciled codex/debugging for both the stuck-cell cleanup and the stale worktree/remote-branch triage, but no one confirmed whether cheap haiku can take one; same-family queue pressure matters.
Open thread A: clear the 3 `in_flight` rows without losing evidence.
Open thread B: confirm whether fixture #2 exists remotely before this fixture edits `LANE_FIXTURES`.
Open thread C: unblock PR #1459 security review after the author answers or branch tip changes.
Open thread D: decide whether retry policy for 429 storms should auto-replay or require human approval when more than 5 cells are affected.
Dependency: do not dispatch any wave until A and B are verified; do not request security re-review on C until the author response is visible.

Deliver:
1. Owners: assign each open thread to a model class (codex / sonnet / opus / gemini / claude-haiku / qwen / agy) and lane (debugging / code-review / orchestration / fact-check / summarization / etc.).
2. Next actions: give concrete commands or PR steps, not vague verbs.
3. Verification checks: say exactly how each next action is confirmed, naming the specific artifact or query to inspect.
4. Escalation: which threads warrant policy escalation, and under what specific criteria?
5. Concurrency policy: identify threads that must not run in parallel, and explain why.
6. Cost / time budget: give a short estimate for each thread.

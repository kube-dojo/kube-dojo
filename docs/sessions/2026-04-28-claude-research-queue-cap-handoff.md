# Session handoff — 2026-04-28 — Ch11-14 prose + 14-chapter research wave (cap-cut mid-queue)

Audience: the next Claude session that picks up the AI History book (Epic #394).

This continues `2026-04-28-claude-research-redistribution-handoff.md`. Big result: **15 PRs landed this session** (4 prose + 11 research) before the headless-Claude orchestration tier hit the 5-hour usage limit at Ch36/Ch37. Two empty worktrees were created and cleaned; nothing destructive landed.

## What this session shipped

### Prose phase — Ch11-14 (Codex authored, Claude orchestrated)

| PR | Branch | Cap | Final words | Authored |
|---|---|---:|---:|---|
| #451 | `codex/394-ch11-prose` | 5,100 | 4,685 | Codex (workspace-write; Claude committed on his behalf because workspace-write blocks `.git/worktrees/*/index.lock`) |
| #452 | `codex/394-ch12-prose` | 4,500 | 4,309 | Codex (danger mode; self-commit `ea92542d`) |
| #454 | `codex/394-ch13-prose` | 4,500 | 4,494 | Codex (danger; self-commit `34f06f42`) |
| #455 | `codex/394-ch14-prose` | 4,500 | 4,202 | Codex (danger; self-commit `9e76aa6c`) |

Lesson: **always use `mode="danger"` for codex prose worktrees**, not `workspace-write`. The latter forces Claude to commit on Codex's behalf — extra integration step, extra Claude tokens.

### Research phase — Parts 1, 2, 3, 6 (headless Claude opus-4-7, 11 chapters)

| PR | Slug | Part | Green/Yellow/Red | Range | Supersedes |
|---|---|:-:|:-:|---|---|
| #456 | `ch-01-the-laws-of-thought` | 1 | 27/3/2 | 3,500-4,800 | #425 |
| #459 | `ch-02-the-universal-machine` | 1 | 17/13/0 | 3,600-5,200 | #431 |
| #460 | `ch-03-the-physical-bridge` | 1 | 26/3/0 | 3,000-4,500 | #433 |
| #462 | `ch-04-the-statistical-roots` | 1 | 20/4/0 | 3,100-4,600 | #435 |
| #463 | `ch-05-the-neural-abstraction` | 1 | 12/7/0 | 3,600-5,100 | #436 |
| #466 | `ch-07-the-analog-bottleneck` | 2 | 17/5/4 | 3,700-5,300 | #439 |
| #467 | `ch-06-the-cybernetics-movement` | 2 | 28/7/0 | 3,200-5,000 | #426 |
| #468 | `ch-08-the-stored-program` | 2 | 17/7/0 | 3,500-5,000 | #427 |
| #469 | `ch-09-the-memory-miracle` | 2 | 13/11/1 | 3,100-4,600 | #438 |
| #470 | `ch-10-the-imitation-game` | 2 | 21/8/0 | 3,500-5,000 | #437 |
| #457 | `ch-15-the-gradient-descent-concept` | 3 | 24/5/1 | 3,400-4,900 | (none — fresh) |

Plus 4 Part 6 research contracts:

| PR | Slug | Part | Green/Yellow/Red | Range |
|---|---|:-:|:-:|---|
| #471 | `ch-32-the-darpa-sur-program` | 6 | 17/1/0 | 4,000-5,600 |
| #472 | `ch-33-deep-blue` | 6 | 26/1/0 | 3,300-4,900 |
| #473 | `ch-34-the-accidental-corpus` | 6 | 16/1/0 | 3,700-5,200 |
| #474 | `ch-35-indexing-the-mind` | 6 | 26/7/0 | 3,200-4,300 |

Each Gemini-superseded PR (Ch01-10) has a comment like "Superseded by #N (Claude-authored). Will close after #N merges." None of the original Gemini PRs are closed yet — they'll close as the replacement PRs land.

## What's left in the queue

**14 chapters** still need Claude-owned research contracts (Parts 6 + 7 remainder):

| Ch | Slug | Part | Notes |
|:-:|---|:-:|---|
| 36 | `ch-36-the-multicore-wall` | 6 | (worktree was created and cleaned this session) |
| 37 | `ch-37-distributing-the-compute` | 6 | (same — clean) |
| 38 | `ch-38-the-human-api` | 6 | not started |
| 39 | `ch-39-the-vision-wall` | 6 | not started |
| 40 | `ch-40-data-becomes-infrastructure` | 6 | not started |
| 41 | `ch-41-the-graphics-hack` | 7 | not started |
| 42 | `ch-42-cuda` | 7 | not started |
| 43 | `ch-43-the-imagenet-smash` | 7 | not started |
| 44 | `ch-44-the-latent-space` | 7 | not started |
| 45 | `ch-45-generative-adversarial-networks` | 7 | not started |
| 46 | `ch-46-the-recurrent-bottleneck` | 7 | not started |
| 47 | `ch-47-the-depths-of-vision` | 7 | not started |
| 48 | `ch-48-alphago` | 7 | not started |
| 49 | `ch-49-the-custom-silicon` | 7 | not started |

There are **NO open Gemini PRs to supersede** for Part 6/7 — Gemini didn't draft these in the prior research wave.

## Cold-start function — the next session should run this

```bash
# 1. Where are we on AI History?
curl -s 'http://127.0.0.1:8768/api/briefing/session?compact=1' | head -50
source ~/.bash_secrets && gh pr list --search "is:open author:@me" --json number,title --limit 30

# 2. Are the 15 PRs from this session still open / did they merge?
for pr in 451 452 454 455 456 457 459 460 462 463 466 467 468 469 470 471 472 473 474; do
  gh pr view $pr --json state,mergedAt --jq "\"#$pr: \(.state) merged=\(.mergedAt // \"no\")\""
done

# 3. Is claude-opus-4-7 cap reset? Test with a tiny dispatch.
.venv/bin/python - <<'EOF'
import sys; sys.path.insert(0, "/Users/krisztiankoos/projects/kubedojo/scripts")
from agent_runtime.runner import invoke
try:
    r = invoke("claude", "Reply with 'ok' and nothing else.", mode="read-only", model="claude-opus-4-7", task_id="cap-probe-2026-04-29", entrypoint="consult", hard_timeout=120)
    print("opus-4-7 ok:", r.ok, repr(r.response[:40]))
except Exception as e:
    print("opus-4-7 still capped:", type(e).__name__, str(e)[:200])
EOF

# 4. If cap reset: resume the queue
.venv/bin/python scripts/dispatch_chapter_research.py 36 --slug ch-36-the-multicore-wall
# (then 37, 38, ... through 49 in sequence; one in flight is fine, two is the soft limit)
```

## Wrapper script reference

`scripts/dispatch_chapter_research.py` does the full setup-and-fire dance:
- Creates `.worktrees/claude-394-chNN-research` off main on `claude/394-chNN-research`.
- Optionally stages prior-session scratch files into the worktree root (`--stage <path>`, repeatable).
- Optionally references a Gemini PR to supersede in the prompt (`--supersede-pr <N>`).
- Maps Ch number → Part number automatically (1-5: P1, 6-10: P2, 11-16: P3, 17-23: P4, 24-31: P5, 32-40: P6, 41-49: P7, 50-58: P8, 59-68: P9).
- Fires `agent_runtime.runner.invoke` with `agent="claude"`, `model="claude-opus-4-7"`, `mode="workspace-write"`, `entrypoint="delegate"`, `hard_timeout=3600`.
- Foreground execution; caller wraps in Bash `run_in_background: true` so the harness fires a completion notification.

CLI:
```
.venv/bin/python scripts/dispatch_chapter_research.py 36 \
  --slug ch-36-the-multicore-wall
```

## Concurrency / backpressure rules learned this session

- **Two headless Claude opus-4-7 dispatches in parallel was fine for the first ~10 chapters**, then we hit the 5-hour usage limit. Each dispatch took 3-15 minutes wall.
- **Codex prose drafts ran sequentially** per `feedback_codex_dispatch_sequential.md`. Each took 1-3 minutes wall.
- **Monitor was useful for early-warning** but the filter needed tightening. The `b1q0l37sx` definition (now stopped) is in the bash log — start with the tighter filter:
  ```
  grep --line-buffered -E 'RateLimit|"status":429|"status":503|ECONNREFUSED|Traceback|killed|"OOM"|"stop_reason":"max_tokens"|"is_error":true.*"context_length"|"subtype":"error"|"subtype":"success"'
  ```
- **Bash `run_in_background: true` on the dispatch wrapper** is enough for completion notification. Monitor adds value only for early failure detection during long runs.

## Open question for the human

Most of the queue is paused because of the cap. Three options I surfaced and one new one:

1. **Pause until cap resets** (probably the next 5-hour boundary). Resume Ch36-49 then.
2. **Reroute remaining 14 chapters to Codex** (gpt-5.5). Codex has the same shell tooling and discipline; per `feedback_claude_weekly_cred_limit.md` cap-rerouting is sanctioned. Tradeoff: overrides the 2026-04-28 role split (Parts 1/2/6/7 = Claude). Codex is also already busy with prose drafts and is the Part 4/5/8 author.
3. **Switch to `claude-sonnet-4-6`** for the remaining contracts. Separate quota; sonnet is high-quality but slightly less than opus on synthesis-heavy contract building. Quick to try — would just be `model="claude-sonnet-4-6"` in `dispatch_chapter_research.py::fire_dispatch`.
4. **Cross-family verdict pass on the 15 PRs landed this session, while waiting.** Each chapter needs both a Codex anchor-verification and a Gemini gap-audit (Gemini lane-disciplined per `feedback_gemini_hallucinates_anchors.md` — no URLs cited). 15 chapters × 2 reviewers ≈ 30 dispatches. Codex sequential, Gemini sequential; total wall ~3-6 hours but no Claude-cap exposure. Task #4 in the task list covers Ch15 specifically; the rest needs new tasks.

Recommendation: do Option 4 (verdict passes) while waiting for the cap reset, then do Option 1 (resume the queue). Option 4 is high-value, low-token-cost-on-Claude work that the next session can do in parallel with the Claude cap.

## Pending action items at handoff

1. **Cross-family verdict pass on Ch01-10 + Ch15 + Ch32-35** (15 PRs). Each needs Codex review + Gemini gap-audit before drafting can begin. See `docs/research/ai-history/TEAM_WORKFLOW.md` § "Prose-Readiness Review" for the verdict template.
2. **Resume research queue Ch36-49** (14 chapters) after cap reset, using `scripts/dispatch_chapter_research.py`.
3. **Cross-family prose review on Ch11-14 prose** (PRs #451, #452, #454, #455). Codex authored; reviewer must be Claude or Gemini. Gemini gap-audit-of-prose pattern works (lane-disciplined).
4. **Once Parts 1+2 contracts (Ch01-10) clear verdicts**, dispatch **Gemini → Claude expansion** prose for those chapters (per Part 1+2 ownership: Gemini drafts, Claude expands).
5. **Close Gemini superseded PRs** (#425, #426, #427, #431, #433, #435, #436, #437, #438, #439) once their replacements (#456, #467, #468, #459, #460, #462, #463, #466, #469, #470 respectively) merge.

## State at handoff — git tree

- Primary branch: `main` (clean except 7 untracked from prior session, none mine).
- Worktrees with uncommitted state: none. (Two new claude-394-research worktrees and one new codex-394-prose worktree's worth of branches still exist on disk; cleanup-merged will prune them when their PRs land.)
- Monitor stopped (`b1q0l37sx`).
- All 19 PRs from this session are open and waiting on review/merge.

## Memories used this session

`feedback_dispatch_to_headless_claude.md` (the heart of the strategy — user-suggested mid-session), `reference_agent_runtime_dispatch_pattern.md` (worktree + invoke recipe), `feedback_overnight_autonomous_codex_chain.md` (cap-window protocol), `feedback_codex_dispatch_sequential.md`, `feedback_claude_weekly_cred_limit.md` (relevant when cap was hit), `feedback_gemini_hallucinates_anchors.md` (sets the role split this work executes), `feedback_team_over_solo_for_book.md` (use the team), `project_ai_history_research_split_2026-04-28.md` (the policy this work executes).

No new memories saved this session — the patterns were already well-recorded.

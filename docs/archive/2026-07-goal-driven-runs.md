> **ARCHIVED 2026-07-07 (s196; lu-parity — lu archived its twin the same day, lu#4704).**
> Dormant: no `/goal` run in recent sessions, yet this ~7KB rule loaded into EVERY
> session's context. The `/goal` grammar below is intact for revival — to revive, move
> this file back to `.claude/rules/goal-driven-runs.md` and restore the references in
> `agents_extensions/claude/skills/curriculum-orchestrator/SKILL.md` +
> `agents_extensions/claude/agents/infra-orchestrator.md`.

# `/goal` Run Vocabulary for Completion-Condition-Driven Orchestration

## 1. What `/goal` is (≤6 lines)

`/goal` is a slash command in Claude Code v2.1.139+ that sets a completion condition and keeps the loop running until the condition is met or an abort condition is emitted.
It runs in interactive mode, `-p` mode, and Remote Control.
Codex CLI also exposes `/goal` (experimental, `features.goals = true`) but has no documented `-p` non-interactive handle.
For unattended KubeDojo runs, the canonical driver is `claude -p`.
A `/goal` session has one active goal at a time.

## 2. Critical mechanics the rule reader must internalize

- Evaluator is a Haiku-class small model.
- Goal met is judged from the transcript only; the evaluator does not run shell commands or read files.
- One goal per session; setting a new goal replaces the previous one.
- Goal persists across `--resume`/`--continue` (turn counter resets, condition stays active).
- There is no `maxTurns` config key; all termination logic must be in the goal text.
- No JSON/IPC transport is used for the overlay panel; elapsed/turns/tokens are visible to humans only.
- **Pre-2.1.143 footgun (now fixed)**: the evaluator could fire while a background shell or delegated subagent was still running, judging completion on stale transcript state. Fixed in Claude Code 2.1.143 — the evaluator now waits for background shells and delegated subagents to finish before reading the transcript. On older CLI versions this risk remains; emit `GOAL_STATUS` only AFTER pasting evidence from the same turn.

## 3. The status-line convention (THE LOAD-BEARING PART)

Every turn in a `/goal` run must print exactly one of these literal status lines as the final line of the turn:

```text
GOAL_STATUS turn=<N>/<MAX> blocked=<X>/<MAX_BLOCKED> no_progress=<Y>/<MAX_NO_PROGRESS> <key>=<value> [<key>=<value> ...]
GOAL_DONE reason="<short reason>" <key>=<value> [<key>=<value> ...]
GOAL_ABORT reason="<short reason>" last_cmd="<…>" last_output="<…>" next_action="<…>"
```

Rules:
- The evaluator checks for literal `GOAL_DONE` and `GOAL_ABORT`; never emit either without the literal token.
- `turn`, `blocked`, and `no_progress` counters MUST be printed as integers on every `GOAL_STATUS` line.
- `last_cmd`, `last_output`, and `next_action` MUST appear on `GOAL_ABORT` lines.
- Keys after the reason field are run-specific (`queue_head`, `module_key`, `readiness_pct`, `batch_count`, etc.) and are used as deterministic evidence.
- One worked example per status type:
  - `GOAL_STATUS turn=4/30 blocked=0/3 no_progress=0/3 queue_head=module-001`.
  - `GOAL_DONE reason="actions.next empty" queue_head=module-011 readiness_pct=82`.
  - `GOAL_ABORT reason="blocked limit reached" last_cmd="python scripts/inspect.py" last_output="timeout" next_action="run /goal clear then /goal Retry"`.

## 4. The three canonical goal templates

#### Template 1 — Queue drainer (overnight autonomous codex chain)

```text
/goal Drain pipeline_v2 queue: each turn, dispatch codex to the head
of /api/pipeline/leases and print the new queue head from
/api/briefing/session?compact=1. Final line of each turn MUST be:
  GOAL_STATUS turn=N/30 blocked=X/3 no_progress=Y/3 queue_head=<module_key>
Emit GOAL_DONE reason="actions.next empty" when /api/briefing/session
returns no actions.next. Emit GOAL_ABORT after blocked=3 or
no_progress=3 with last_cmd, last_output, queue_head, next_action.
```

#### Template 2 — Track readiness target

```text
/goal Get <track>/<section> readiness ≥<pct>%: each turn dispatch a
fix for the lowest-quality module in /api/tracks/readiness and print
new cleared/in-flight counts. Final line of each turn MUST be:
  GOAL_STATUS turn=N/25 blocked=X/3 no_progress=Y/3 readiness=<pct>%
Emit GOAL_DONE reason="readiness ≥<target>%" when target hit.
Emit GOAL_ABORT after blocked=3 or no_progress=3 with last_cmd,
last_output, current_module, next_action.
```

#### Template 3 — Verifier gate (#388 batch)

```text
/goal #388 batch: dispatch codex per module on briefing.actions.next,
run scripts/quality/verify_module.py for density gates (median_wpp≥28, mean_wpp≥30,
short-para-rate≤20%), paste the verifier output verbatim. Final line
of each turn MUST be:
  GOAL_STATUS turn=N/40 blocked=X/3 no_progress=Y/3 module=<key> verifier=<pass|fail>
Emit GOAL_DONE reason="batch empty" when actions.next has no #388
modules. Emit GOAL_ABORT after 3 consecutive verifier failures with
last_cmd, last_output, module, next_action.
```

## 5. Dispatch ownership (anti-fabrication clauses)

- Per `feedback_dispatch_codex_for_code_changes.md`, `/goal` orchestration is claude-only. Do not inline-write code, content, or prose.
- Every per-turn dispatch must go through `scripts/dispatch_smart.py` or `scripts/ab`.
- No raw Agent-tool subagents in a `/goal` turn. Use dispatch wrappers only.
- Per `feedback_deterministic_over_hallucination.md`, all numeric values in `GOAL_STATUS`, `GOAL_DONE`, and `GOAL_ABORT` must come from command/API output pasted in the same turn.
- Never emit `GOAL_DONE` without a predicate that is true in the same pasted evidence chunk (for example, briefing JSON shows `actions.next: []`).

## 6. `/goal` vs ScheduleWakeup + `/loop` — when to use which

| Use `/goal` when … | Use `ScheduleWakeup` + `/loop` when … |
|---|---|
| Measurable done/abort predicate exists. | Control plane is time/cadence driven. |
| Bounded batch draining (queue/readiness/verifier). | Polling external state (PR review queue, CI status). |
| One session, one CLI invocation. | Multi-session periodic check-ins are needed. |
| Loop terminates on goal-met or N turns. | Loop terminates on user signal or ScheduleWakeup omission. |

Cross-reference: `feedback_overnight_autonomous_codex_chain.md` (autonomous-mode protocol still applies; `/goal` is the handle, memory is the policy).

## 7. Phase composition

- One goal per session.
- Run phases in sequence with separate `claude -p "/goal …"` invocations.
- Do not use `/goal clear` between phases in unattended runs; this is interactive semantics and can be ambiguous for unattended chains.

## 8. Invocation cheat sheet

```bash
# Autonomous (unattended) — Phase 1
claude -p "/goal …" --output-format text

# Interactive (operator-supervised)
/goal …
/goal                # status check
/goal clear          # cancel
```

## 9. Anti-patterns

- Plain-English termination clauses like “until done” or “for a while” — evaluator cannot infer completion from prose.
- Narrating counters in prose (for example, “we’ve been blocked twice”) instead of integer status-line counters.
- Claiming `GOAL_DONE` without quoting predicate output in the same turn.
- Using Codex `/goal` for unattended runs (no `-p` handle today).
- Stacking multiple goals in one session (one-goal limit).

## 10. References

- `.claude/rules/decision-card.md` — multi-agent deliberation pattern.
- `feedback_overnight_autonomous_codex_chain.md` (memory) — autonomous-mode policy.
- `feedback_deterministic_over_hallucination.md` (memory) — deterministic-fact rule.
- `feedback_dispatch_codex_for_code_changes.md` (memory) — orchestrate-only rule.
- `scripts/dispatch_smart.py` — task-class dispatch wrapper.
- `scripts/ab` — agent bridge CLI.

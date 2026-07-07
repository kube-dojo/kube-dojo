---
name: cold-start
description: KubeDojo agent session orientation. Use at the start of every fresh session or when picking up a GitHub issue. Triggers on "cold start", "orient", "session start", "issue-driven".
---

# Cold-start Skill

Deterministic orientation for KubeDojo coding agents: **issue in → API orient → minimal file reads → work**.

Full ritual: [`scripts/prompts/cold-start.md`](../../../scripts/prompts/cold-start.md)

## When to Use

- First call on a fresh agent session
- Picking up a GitHub issue (#N)
- After a long break when briefing may be stale

## Steps

1. **Read parent task verbatim** — `gh issue view N --repo kube-dojo/kube-dojo.github.io`
2. **Run cold-start** — `KUBEDOJO_ISSUE=N bash scripts/cold-start.sh`
3. **Claim if assigned** — `gh issue comment N --body "Claiming — worktree .worktrees/<name>"`
4. **Worktree only** — never commit on primary `main`
5. **Handoff on demand** — read `docs/session-state/*` only when orient/briefing leave a narrative gap

## Script output sections

Parse the labeled blocks from stdout:

- `kubedojo:orient` — **start here** for "what to do now" (primary + up to 3 alternatives)
- `kubedojo:briefing` — full compact snapshot (`actions`, `top_modules`, blockers)
- `kubedojo:session` — latest handoff path (do not read the handoff file unless needed)
- `kubedojo:pending-decisions` — blocking Decision Cards in `docs/decisions/pending/`

Optional: `bash scripts/cold-start.sh --manifest` for route discovery via `/api/state/manifest`.

## API-down

Script exits **0** with `kubedojo:fallback` (STATUS excerpt) + `kubedojo:handoff-path`. Continue with local files; do not treat API failure as a hard stop.

## Do NOT cold-start when

The dispatch brief explicitly forbids shell scripts (e.g. headless content rewrites in worktrees where `services-up` is unnecessary).

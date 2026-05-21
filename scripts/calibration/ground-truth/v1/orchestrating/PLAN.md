# Orchestrating — fixture expansion plan

## Current state

- `multi-task-routing-brief.yaml` — routing-brief fixture that assigns a Python bug to Codex/debugging, security review to Claude/code-review, module handoff to a cheap summarizer, and fact-checking to a Google/fact-check path.

## Target

- Target count: 3 fixtures.
- Current count: 1 fixture.
- Add 2 fixtures so orchestration is measured across routing, scheduling, and follow-up execution planning.
- Keep answers judgeable by requiring explicit task boundaries, model-family choices, dependencies, and cost/risk notes.

## Variety dimensions

- Routing brief: keep the existing multi-task routing fixture as the baseline.
- Schedule plan: add a fixture that asks for sequencing several dependent work items under reviewer, CI, or rate-limit constraints.
- Runbook follow-up: add a fixture where the model must convert a status update into owners, next actions, checks, and escalation points.
- Include at least one fixture where same-family serialization or cross-family review policy is a deciding constraint.
- Include at least one fixture where the cheapest acceptable route is preferred only after quality gates are protected.

## Acceptance criteria per fixture

- Passing answers route each subtask to the expected model class or lane and state key dependencies.
- Strong answers score `judge_score>=7`, include cost-aware sequencing, and avoid parallelism that violates stated constraints.
- Runbook-style fixtures must end with concrete follow-up actions and verification checkpoints, not a generic plan.

## Open questions

- Should orchestration ground truth prescribe exact model families, or score acceptable model-class ranges?
- How should the rubric handle new available models without rewriting old fixtures?
- Who reviews scheduling assumptions when fixture timing, rate limits, or team policy changes?

## Refs

- #1413
- Memory: `feedback_single_fixture_v1_calibration.md`

# Architecting — fixture expansion plan

## Current state

- `kubedojo-review-override-rfc.yaml` — RFC-design task for `KUBEDOJO_REVIEW_OVERRIDE`, covering env-var format, validation, Hermes invocation, flow integration, telemetry, rollback, and failure modes.

## Target

- Target count: 3 fixtures.
- Current count: 1 fixture.
- Add 2 fixtures so this lane can compare architectural judgment across more than one scenario.
- Keep fixtures small enough for repeatable calibration while preserving enough context to force tradeoff reasoning.

## Variety dimensions

- RFC writeup: keep the existing review-override RFC as the long-form architecture fixture.
- Decision card: add a compact ADR-style fixture that asks for a recommendation between two or three viable designs.
- Capacity planning: add a sizing or throughput fixture that requires assumptions, bottleneck identification, and failure-budget thinking.
- Include at least one fixture where rollback and observability are first-class acceptance points.
- Include at least one fixture where the best answer must reject an over-broad design and scope the rollout.

## Acceptance criteria per fixture

- Passing answers identify the core design constraints, risks, rollback path, and integration points named in the fixture.
- Strong answers score `judge_score>=7` on the lane rubric and avoid invented infrastructure or unsupported product claims.
- For any fixture with deterministic checks, `pytest_exit=0` or the equivalent verifier pass should be required before judge scoring is treated as sufficient.

## Open questions

- Should architecting reuse one lane-level rubric, or should the RFC, decision-card, and capacity-planning fixtures each have a short fixture-specific rubric?
- What source should ground truth use for capacity numbers: synthetic constraints, project telemetry, or an archived production-like trace?
- Who reviews the final expected-answer notes for architecture fixtures before they become calibration anchors?

## Refs

- #1413
- Memory: `feedback_single_fixture_v1_calibration.md`

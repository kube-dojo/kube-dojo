# Refactoring — fixture expansion plan

## Current state

- `check-site-health-refactor.yaml` — refactoring task from `scripts/check_site_health.py`, focused on reducing repeated counter logic and shared global state while preserving frontmatter error and warning behavior.

## Target

- Target count: 3 fixtures.
- Current count: 1 fixture.
- Add 2 fixtures so refactoring quality is tested beyond one Python script cleanup.
- Keep all fixtures behavior-preserving, with explicit before/after checks wherever possible.

## Variety dimensions

- LOC reduction: keep the existing check-site-health fixture as a small reduction and duplication-removal case.
- Behavior-preserved API change: add a fixture where internal structure or function signatures change but public behavior and callers must stay compatible.
- Test extraction: add a fixture where repeated assertions or integration-heavy tests should be factored into clearer helpers without weakening coverage.
- Include one fixture where the best refactor is intentionally modest and large rewrites should lose points.
- Include one fixture with measurable complexity or duplication reduction targets.

## Acceptance criteria per fixture

- Passing answers preserve configured behavior terms and pass any provided test or lint command.
- Strong answers reduce real duplication or complexity, avoid unrelated rewrites, and reach `judge_score>=7`.
- Refactors must not weaken assertions, skip tests, or replace precise behavior with broad compatibility shims.

## Open questions

- Should refactoring fixtures use LOC reduction as a scored metric, or only as supporting evidence?
- How should the harness detect behavior preservation when a fixture does not have complete tests?
- Who reviews refactor outputs for over-engineering versus useful abstraction?

## Refs

- #1413
- Memory: `feedback_single_fixture_v1_calibration.md`

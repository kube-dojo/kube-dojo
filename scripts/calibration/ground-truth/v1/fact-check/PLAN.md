# Fact Check — fixture expansion plan

## Current state

- `k8s-1-35-claims.yaml` — Kubernetes 1.35 claim-verification fixture with three verified claims, two false claims, and a minimum of three citations.

## Target

- Target count: 5 fixtures.
- Current count: 1 fixture.
- Add 4 fixtures covering positive and negative cases across Kubernetes, AWS, security, certification blueprints, and multi-sentence claims.
- Require source-backed verdicts rather than model-memory answers.
- Methodology: use bundled source excerpts for reproducibility, with pinned Kubernetes 1.35, AWS, and IETF documentation snapshots rather than live web lookup.

## Variety dimensions

- Kubernetes claims: keep the existing 1.35 fixture and add at least one negative case that is plausible but false.
- AWS claims: add positive and negative cloud-service behavior claims, using official AWS documentation as the preferred source.
- Security claims: add claims where wording precision matters, such as default behavior, supported controls, or risk boundaries.
- Certification blueprints: add claims tied to current exam or curriculum blueprint language.
- Multi-sentence: add one fixture where the answer must split a paragraph into independently verifiable subclaims.

## Acceptance criteria per fixture

- Passing answers assign the expected verdict for each claim and include the minimum configured citation count.
- Strong answers use primary sources, quote sparingly, explain false claims precisely, and reach `judge_score>=7`.
- Negative cases must be marked false or unsupported when evidence is absent; guessing from plausibility should fail the fixture.

## Open questions

- How should the rubric distinguish `FALSE`, `UNSUPPORTED`, and `MISLEADING` across different claim families?
- Who refreshes source links when Kubernetes, AWS, security guidance, or certification blueprints change?

## Refs

- #1413
- Memory: `feedback_single_fixture_v1_calibration.md`

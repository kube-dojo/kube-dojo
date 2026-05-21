# Content Review — fixture expansion plan

## Current state

- `flawed-module-rubric-review.yaml` — deliberately flawed Kubernetes RBAC module review with planted issues including a hallucinated kubectl flag, missing IPA tags, heading errors, broken citation, Bloom mismatch, missing diagram, duplicate H1, and banned wording.

## Target

- Target count: 3 fixtures.
- Current count: 1 fixture.
- Add 2 fixtures so review quality is tested across PR-level, module-level, and security-focused content review.
- Keep planted flaws concrete enough that reviewers can distinguish rubric violations from stylistic preferences.
- PR-review fixtures use structured JSON output matching the `_lib_pr_check.py` result shape already used by content-merge hooks.

## Variety dimensions

- PR review: add a fixture that reviews a content PR diff and must separate blocking issues from nice-to-have edits.
- Module review: keep the existing flawed-module fixture and add another module-level review with different pedagogy and structure failures.
- Security review: add a security-sensitive content fixture where inaccurate commands, unsafe defaults, or missing warnings are central.
- Include one fixture focused on citations and source fidelity rather than prose polish.
- Include one fixture where the correct answer must preserve good content and avoid rewriting the whole module.

## Acceptance criteria per fixture

- Passing answers identify the configured planted flaws and do not claim unrelated hallucination terms as findings.
- Strong answers prioritize blockers, connect each issue to the rubric, and provide actionable fixes; target `judge_score>=7`.
- Security review fixtures must catch unsafe or false guidance and avoid weakening the evidence standard for security claims.

## Open questions

- Should content-review scoring use planted-flaw recall only, or combine recall with severity calibration and review tone?
- Who reviews the ground-truth flaw list when content has subjective pedagogy concerns?

## Refs

- #1413
- Memory: `feedback_single_fixture_v1_calibration.md`

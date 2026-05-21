# Code Review — fixture expansion plan

## Current state

- `k8s-controller-leader-election.yaml` — Go Kubernetes controller review with six planted findings around context propagation, loop capture, secret logging, nil dereference, goroutine cancellation, and optimistic concurrency.
- `pr-1333-security-yaml.yaml` — GitHub Actions/security-YAML review for zizmor strict mode, reusable-action scan scope, Dependabot cooldown, and unpinned install behavior.

## Target

- Target count: 5 fixtures.
- Current count: 2 fixtures.
- Add 3 fixtures so the lane covers the full review surface from correctness through security and maintainability.
- Keep planted findings explicit, with tight hallucination terms so models are rewarded for finding real issues instead of generic review noise.

## Variety dimensions

- Bugfix archetype: cover a small diff that fixes one bug but introduces a subtle behavioral regression.
- Refactor archetype: cover a readability or structure change where the reviewer must preserve behavior and catch an accidental contract change.
- Security archetype: keep `pr-1333-security-yaml.yaml` as one security-oriented fixture and add another only if it exercises a different threat model.
- Feature archetype: use the Go leader-election fixture as a feature implementation review with concurrency and Kubernetes semantics.
- Include one fixture with tests changed in the diff, so reviewers must check whether the tests actually protect the intended behavior.

## Acceptance criteria per fixture

- Passing answers identify the expected planted findings by alias, with no severe hallucination term present.
- Strong answers find most high-impact issues and explain why they matter; target `judge_score>=7` or fixture-specific finding recall above the configured threshold.
- Security fixtures must separate exploitable risks from low-confidence speculation and must not invent unrelated classes such as SQL injection or XSS.

## Open questions

- Should all code-review fixtures use the same finding-recall scorer, or should security fixtures have severity weighting?
- How should partially correct findings be normalized when a model describes the bug accurately without using any configured alias?
- Who signs off on the planted findings: original author, independent reviewer, or methodology working group?

## Refs

- #1413
- Memory: `feedback_single_fixture_v1_calibration.md`

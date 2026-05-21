# Code Writing — fixture expansion plan

## Current state

- `parse-dependabot-cooldown.yaml` — Python implementation task for parsing Dependabot `cooldown.default-days` from YAML, with eight pytest cases covering nested/inline mappings, missing values, and invalid shapes.

## Target

- Target count: 5 fixtures.
- Current count: 1 fixture.
- Add 4 fixtures, one each for Node/TypeScript, Java, Rust, and Go.
- Keep each fixture runnable in isolation with deterministic tests and no network dependency.

## Variety dimensions

- Python: keep the existing Dependabot cooldown parser as the Python fixture.
- Node/TypeScript: add a typed parser or transform with edge cases around optional fields and invalid input.
- Java: add a small class or utility where exception behavior, immutability, or collection handling matters.
- Rust: add a parser or validator that exercises `Result`, ownership-friendly design, and precise error handling.
- Go: add a package-level function with table-driven tests, nil/zero-value behavior, and explicit error returns.

## Acceptance criteria per fixture

- Passing requires the fixture test command to complete successfully, normally `pytest_exit=0`, `npm test` pass, `mvn test` or Gradle pass, `cargo test` pass, or `go test ./...` pass as appropriate.
- Strong answers keep the implementation minimal, deterministic, and idiomatic for the target language while preserving all specified edge-case behavior.
- If judge scoring is used, test pass remains the hard gate and `judge_score>=7` is an additional quality signal, not a substitute for failing tests.

## Open questions

- Should each language fixture include lint or formatter checks, or should calibration rely only on tests plus judge scoring?
- Do we allow third-party dependencies when they are idiomatic for the language, or require standard-library-only solutions for comparability?
- Who owns runtime setup validation for Java, Rust, Go, and Node/TypeScript fixtures on local and CI machines?

## Refs

- #1413
- Memory: `feedback_single_fixture_v1_calibration.md`

# Summarization — fixture expansion plan

## Current state

- `session-34-handoff.yaml` — 180-220 word session handoff summary requiring six specific milestones and banning hallucinations about calibration PRs, blockers, and translation-lane status.

## Target

- Target count: 3 fixtures.
- Current count: 1 fixture.
- Add 2 fixtures so summarization is measured across session, PR, and incident contexts.
- Keep each fixture constrained by required mentions, banned hallucinations, and an explicit length or structure target.

## Variety dimensions

- Session handoff: keep the existing session-34 handoff fixture.
- PR descriptor: add a fixture that summarizes a PR diff into user-facing title, summary, tests, risks, and follow-up notes.
- Incident timeline: add a fixture that condenses logs or status updates into chronology, impact, root cause, mitigation, and remaining risk.
- Include one fixture where chronological ordering matters more than prose style.
- Include one fixture where omitting uncertainty should be penalized.

## Acceptance criteria per fixture

- Passing answers satisfy the length or structure constraint, include required mentions, and avoid banned hallucinations.
- Strong answers score `judge_score>=7`, preserve sequence and status accurately, and separate facts from inferred next steps.
- PR and incident fixtures must not invent test results, merge status, owners, or root causes absent from the source.

## Open questions

- Should summarization use one rubric across all contexts, or separate rubrics for handoffs, PRs, and incidents?
- How should scoring balance compression, required mentions, chronology, and uncertainty handling?
- Who approves banned hallucination lists for each fixture before calibration runs?

## Refs

- #1413
- Memory: `feedback_single_fixture_v1_calibration.md`

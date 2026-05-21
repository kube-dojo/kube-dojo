# MCP Use — fixture expansion plan

## Current state

- `define-the-word-in-uk.yaml` — Ukrainian RAG tool-selection fixture for translating `cloud`, verifying the canonical modern Ukrainian form, checking Russicism risk, and citing a source through the expected MCP tool chain.

## Target

- Target count: 5 fixtures.
- Current count: 1 fixture.
- Add 4 fixtures covering simple lookup, chained tool use, error recovery, Ukrainian-specific RAG, and tool-selection accuracy.
- Keep each fixture explicit about expected tools, forbidden tools, required parameters, and stop conditions.
- Fixture format: execution traces for the learn-ukrainian RAG MCP server, matching #1404's direction to wire that server into calibration.
- Each trace records ordered MCP calls, parameters, normalized tool responses, stop conditions, and expected final answer fields so scoring can compare actual behavior without relying on free-form call plans.

## Variety dimensions

- Single-tool query: add a fixture where exactly one MCP call is sufficient and extra calls signal overuse.
- Multi-tool chain: keep `define-the-word-in-uk.yaml` as the Ukrainian chain fixture and add another chain in a different domain if available.
- Error recovery: add a fixture where the first tool result is empty, ambiguous, or malformed and the model must choose the recovery path.
- Ukrainian-specific RAG: keep canonical-form and Russicism checks central for at least one fixture.
- Tool selection accuracy: add a fixture where plausible but nonexistent tools are tempting and must be avoided.

## Acceptance criteria per fixture

- Passing answers select the expected tool or tool chain, include required parameters, and avoid forbidden tools.
- Strong answers explain ordering and stop conditions, handle tool errors explicitly, and reach `judge_score>=7` when LLM judging is configured.
- Models must not invent MCP tools or execute when the task only asks for a plan.

## Open questions

- How should scoring handle semantically equivalent tool names across different MCP server versions?
- Who maintains Ukrainian RAG fixture expectations as dictionaries, source corpora, or MCP surfaces change?

## Refs

- #1413
- Memory: `feedback_single_fixture_v1_calibration.md`

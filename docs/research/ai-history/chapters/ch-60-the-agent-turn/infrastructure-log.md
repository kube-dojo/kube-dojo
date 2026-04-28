# Infrastructure Log: Chapter 60 - The Agent Turn

## Systems To Track

- Retrieval stack: embeddings, vector databases, chunking, ranking, reranking, context injection.
- Search stack: query generation, browsing, citation selection, source verification.
- Tool stack: schemas, function calling, API permissions, structured outputs, execution sandboxes.
- Agent stack: planning loop, memory, tool router, task queue, observation/action transcript.

## Metrics To Verify

- Retrieval benchmark or task settings from primary papers.
- Tool-use benchmark definitions and measured limits.
- Cost/latency implications of multi-call agent loops.
- Evaluation failures: stale retrieval, wrong citation, bad tool arguments, loop failures.

## Boundary

This chapter is about architectural interface shift. The serving-cost consequences belong primarily in Chapter 63, Inference Economics.

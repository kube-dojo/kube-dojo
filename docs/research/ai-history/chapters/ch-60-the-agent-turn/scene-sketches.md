# Scene Sketches: Chapter 60 - The Agent Turn

## Scene 1: The Closed Chat Window
- **Action:** The model answers fluently but has no direct access to a private knowledge base, current search result, calculator, or database.
- **Guardrail:** Do not invent a product failure anecdote.

## Scene 2: Retrieval As Memory
- **Action:** Documents are chunked, embedded, indexed, retrieved, and inserted into context.
- **Guardrail:** Retrieval provides evidence candidates, not truth.

## Scene 3: Search Before Answering
- **Action:** A model searches or browses, reads snippets/pages, and constructs an answer.
- **Guardrail:** Keep browser/search claims tied to verified systems.

## Scene 4: The API Call
- **Action:** The model selects a tool/function, passes structured arguments, and receives a result.
- **Guardrail:** Tool choice is not the same as reliable planning.

## Scene 5: The Agent Demo
- **Action:** Early agent frameworks chain model calls into loops that look autonomous.
- **Guardrail:** The close must emphasize brittleness, cost, and evaluation gaps.

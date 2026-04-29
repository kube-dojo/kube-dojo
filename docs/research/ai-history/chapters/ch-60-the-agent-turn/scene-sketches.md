# Scene Sketches: Chapter 60 - The Agent Turn

## Scene 1: The Closed Chat Window
- **Action:** The model answers fluently but has no direct access to a private knowledge base, current search result, calculator, or database.
- **Evidence Anchor:** OpenAI plugins page, Overview section: out-of-the-box language models emit text; another process is needed to follow instructions or access current/personal/specific information.
- **Guardrail:** Do not invent a product failure anecdote.

## Scene 2: Retrieval As Memory
- **Action:** Documents are chunked, embedded, indexed, retrieved, and inserted into context.
- **Evidence Anchor:** Lewis et al. RAG p.1 abstract and Section 2: pretrained parametric memory plus dense Wikipedia index as non-parametric memory.
- **Guardrail:** Retrieval provides evidence candidates, not truth.

## Scene 3: Search Before Answering
- **Action:** A model searches or browses, reads snippets/pages, and constructs an answer.
- **Evidence Anchor:** WebGPT p.1/p.3 and OpenAI WebGPT page intro/Evaluating factual accuracy/Risks sections: search, link following, references, evaluation difficulty, unreliable-source/basic-error caveats.
- **Guardrail:** Keep browser/search claims tied to verified systems.

## Scene 4: Reasoning Before Acting
- **Action:** Chain-of-thought prompting makes intermediate natural-language reasoning steps part of the prompt-and-output pattern before tools enter the loop.
- **Evidence Anchor:** Wei et al. Chain-of-Thought paper p.1 abstract and Section 2/page 2: chain of thought as intermediate reasoning steps; decomposition, debugging window, and few-shot elicitation in sufficiently large models.
- **Guardrail:** Visible reasoning is a useful interface and debugging hook, not guaranteed access to the model's internal computation or proof of reliable planning.

## Scene 5: The API Call
- **Action:** The model selects a tool/function, passes structured arguments, and receives a result.
- **Evidence Anchor:** ReAct p.1/p.3 for reason/action/observation; Toolformer p.1/p.2 for learned API calls; OpenAI function-calling page Function Calling section for JSON function arguments and tool-output risk.
- **Guardrail:** Tool choice is not the same as reliable planning.

## Scene 6: The Agent Demo
- **Action:** Early agent frameworks chain model calls into loops that look autonomous.
- **Evidence Anchor:** LangChain Oct 2022 README commit on composability and computation/knowledge, LangChain v0.0.1 tag for later chains/data-augmented-generation/agents framing, and AutoGPT v0.1.0 README on chaining LLM "thoughts," internet access, memory, file storage, and "NEXT COMMAND" authorization.
- **Guardrail:** The close must emphasize brittleness, cost, and evaluation gaps.

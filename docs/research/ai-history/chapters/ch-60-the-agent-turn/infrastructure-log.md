# Infrastructure Log: Chapter 60 - The Agent Turn

## Systems To Track In Prose

- **Retrieval stack:** corpus preparation, passage splitting, embeddings or dense retrieval, index lookup, top-k document selection, context injection, citation discipline. RAG paper uses a dense vector index of Wikipedia, not a commercial vector database story.
- **Search stack:** query generation, browser/search action space, link following, scrolling, quoting, reference collection, and the human burden of checking whether a cited source supports the answer.
- **Tool stack:** tool schemas, function definitions, JSON arguments, external API execution, database queries, calculators, translation systems, calendars, and user confirmation for real-world actions.
- **Agent stack:** thought/action/observation transcript, memory, task loop, tool router, permissions, loop termination, cost/latency amplification, and failure recovery.

## Verified Technical Anchors

- RAG: parametric memory plus non-parametric memory; dense Wikipedia index; RAG-Sequence and RAG-Token variants.
- WebGPT: text browser actions; Bing search API; reference collection; human preference evaluation; warnings about unreliable sources and basic errors.
- ReAct: interleaved reasoning and acting; Wikipedia API; HotpotQA/FEVER/ALFWorld/WebShop.
- Toolformer: self-supervised API-call insertion; calculator, Q&A, search, translation, and calendar tools.
- OpenAI plugins: browser, code interpreter, retrieval plugin, third-party services, prompt-injection/action-risk warnings.
- Function calling: developer-provided function descriptions and JSON arguments for external tools/APIs.
- LangChain/AutoGPT: practical packaging of composability, chains, data-augmented generation, agents, internet access, memory, and action authorization. Keep the LangChain chronology split between the October 2022 composability README and the July 2023 v0.0.1 taxonomy.

## Failure Modes To Preserve

- Retrieval returns plausible but wrong or stale evidence.
- Citations create authority even when the answer remains wrong.
- Tool output can carry prompt-injection instructions or untrusted data.
- Function arguments can be syntactically structured but semantically wrong.
- Agent loops can burn calls, repeat mistakes, or need human authorization.
- More calls mean more latency and cost; detailed economics belongs in Ch63.

## Boundary

This chapter is about architectural interface shift. The serving-cost consequences
belong primarily in Chapter 63, Inference Economics.

# Open Questions: Chapter 60 - The Agent Turn

## Resolved In This Contract

- **First broad public "agent" moment:** Use AutoGPT v0.1.0 only as an early visible demo of agent loops, not as a claim of firstness or reliable autonomy.
- **Vector databases:** Keep them inside the RAG/retrieval infrastructure scene. The verified 2020 RAG anchor is a dense Wikipedia index, not a commercial-vector-database narrative.
- **LangChain/LlamaIndex detail:** LangChain gets a short framework subsection, but the chronology must be careful: the October 2022 README supports composability and combining LLMs with computation/knowledge, while the v0.0.1 tag that directly names chains, data-augmented generation, and agents resolves to a July 2023 commit. LlamaIndex remains Yellow context unless a historical README snapshot is added.
- **Tool-use brittleness:** Use WebGPT's own caveats, OpenAI plugin/function-calling safety warnings, and AutoGPT's user-authorization/cost signals. Do not fabricate failure anecdotes.

## Remaining Review Questions

- **Gemini gap/capacity audit:** Confirm that 4,500-5,600 words is ambitious but not bloated, and that Ch60 does not steal Ch63 inference economics or Ch66 benchmark-politics material.
- **Claude source-fidelity review:** Source-fidelity review approved. Follow-up notes were applied by splitting LangChain chronology and removing brittle OpenAI live-page line references.
- **Optional OpenAI page archiving:** Official OpenAI pages were verified through browser-rendered source, but `curl` sees SPA shells. If a prose reviewer needs reproducible line anchors, add Wayback/text snapshots; otherwise cite page title/date/section rather than line numbers.
- **Optional LlamaIndex hardening:** If prose wants more than one sentence on LlamaIndex, pin a historical README/docs snapshot; otherwise keep it contextual and Yellow.
- **Optional benchmark details:** Add exact ReAct/Toolformer numbers only if prose genuinely needs them; current contract can make the architectural point without score tables.

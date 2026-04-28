# Brief: Chapter 60 - The Agent Turn

## Thesis
ChatGPT made language models feel conversational, but the next architectural turn made them operational: retrieval, search, tool use, function calling, and agent frameworks connected models to external memory and actions. The chapter should show the bridge from "answer in a chat window" to "retrieve, plan, call tools, and execute workflows" without pretending early agents were reliable autonomous workers.

## Scope
- IN SCOPE: retrieval-augmented generation (RAG), vector databases, WebGPT/search-assisted answering, ReAct-style reasoning/action loops, Toolformer/function calling, LangChain/LlamaIndex-style orchestration, AutoGPT-style agent excitement, and the reliability limits of early tool-using systems.
- OUT OF SCOPE: full humanoid robotics, long-horizon autonomous employment replacement claims, and product-by-product agent marketing after the first wave.

## Required Scenes
1. **The Chatbot Boundary:** A pure chatbot answers from weights and context; it cannot reliably know private, current, or tool-specific facts without an external channel.
2. **Retrieval As Memory:** RAG/vector search turns documents into callable context, shifting the bottleneck from model parameters to indexing, chunking, ranking, and citation discipline.
3. **Search As Grounding:** WebGPT/search-assisted systems show the model reading before answering, but also expose evaluation and browsing reliability questions.
4. **Tools As Hands:** Function calling and Toolformer/ReAct-style loops turn model text into API calls, calculations, database queries, and actions.
5. **Agent Hype And Limits:** AutoGPT-style demos make autonomy legible, but early systems remain brittle, expensive, and evaluation-poor.

## Prose Capacity Plan

Target range: 4,500-5,500 words after source verification.

- 600-800 words: bridge from Product Shock to the limits of chat-only systems.
- 900-1,100 words: RAG/vector search and the memory/citation problem.
- 800-1,000 words: search-assisted answering and source-grounding evaluation.
- 1,000-1,200 words: tools, function calling, ReAct/Toolformer, and orchestration frameworks.
- 700-900 words: agent hype, failure modes, and transition to scale/serving economics.

## Guardrails

- Do not claim early agents were reliable autonomous workers.
- Do not treat RAG as a hallucination cure; it changes the failure surface.
- Do not use product demos as proof of broad capability.
- Do not invent benchmark results or adoption numbers.

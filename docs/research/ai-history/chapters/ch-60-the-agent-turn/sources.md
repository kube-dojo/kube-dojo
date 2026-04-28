# Sources: Chapter 60 - The Agent Turn

## Research Status

Contract is `capacity_plan_anchored` as of 2026-04-28. Sources below were
verified directly through arXiv PDFs, OpenAI official pages, GitHub API metadata,
and raw GitHub repository snapshots. Gemini must still gap-audit the scope and
word cap before prose drafting.

## Primary Source Spine

| Source | Use | Verification |
|---|---|---|
| Patrick Lewis et al., "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks," arXiv:2005.11401 / NeurIPS 2020. PDF: https://arxiv.org/pdf/2005.11401 | RAG as parametric plus non-parametric memory; dense Wikipedia index; retriever/generator architecture. | Green: PDF downloaded 2026-04-28. Abstract/page 1 defines RAG as combining a seq2seq parametric memory with a dense vector index of Wikipedia. Section 2/page 3 defines RAG-Sequence and RAG-Token; Section 4/page 5 notes the Wikipedia dump/index setup. |
| Reiichiro Nakano et al., "WebGPT: Browser-assisted question-answering with human feedback," arXiv:2112.09332. PDF: https://arxiv.org/pdf/2112.09332. OpenAI page: https://openai.com/index/webgpt/ | Search-assisted answering, references, browser action space, human-feedback evaluation, and reliability caveats. | Green: PDF downloaded and OpenAI page opened through browser-rendered source 2026-04-28. PDF abstract/page 1 says the model searches/navigates the web and collects references; Section 2/page 3 defines browser actions. OpenAI page intro/Evaluating factual accuracy/Risks sections discuss search commands, source citation, evaluation difficulty, basic errors, and web-access risks. |
| Shunyu Yao et al., "ReAct: Synergizing Reasoning and Acting in Language Models," arXiv:2210.03629. PDF: https://arxiv.org/pdf/2210.03629 | Interleaved reasoning/action loops and environment observations; Wikipedia API, ALFWorld, and WebShop tasks. | Green: PDF downloaded 2026-04-28. Abstract/page 1 says ReAct generates reasoning traces and task-specific actions in an interleaved manner, interacts with a Wikipedia API, and evaluates on HotpotQA, FEVER, ALFWorld, and WebShop. Section 1/page 3 describes reasoning to act and acting to reason. |
| Timo Schick et al., "Toolformer: Language Models Can Teach Themselves to Use Tools," arXiv:2302.04761. PDF: https://arxiv.org/pdf/2302.04761 | Tool-use learning via API calls; calculator, Q&A, search, translation, and calendar tools. | Green: PDF downloaded 2026-04-28. Abstract/page 1 says Toolformer learns when and how to call APIs using only a few demonstrations per API and includes calculator, Q&A, search, translation, and calendar tools. Section 2/page 2 defines sample, execute, filter, and interleave API-call steps. |
| OpenAI, "ChatGPT plugins," March 23, 2023. URL: https://openai.com/index/chatgpt-plugins/ | Productization of tools: browser, code interpreter, retrieval plugin, third-party services, and safety risks. | Green: official OpenAI page opened through browser-rendered source 2026-04-28. Overview and Safety sections frame plugins as tools for up-to-date information, computation, third-party services, and actions, and discuss prompt injection, harmful/unintended actions, safeguards, and evals. Note: `curl` returns an SPA shell, so cite page title/date/sections rather than brittle live line numbers. |
| OpenAI, "Function calling and other API updates," June 13, 2023. URL: https://openai.com/index/function-calling-and-other-api-updates/ | Structured tool interface: model emits JSON arguments for developer-described functions. | Green: official OpenAI page opened through browser-rendered source 2026-04-28. Function Calling section describes developers providing function definitions to GPT-4/GPT-3.5 Turbo and the model outputting JSON arguments for external tools, APIs, and database queries; later safety note warns about untrusted tool output and real-world actions. Note: `curl` returns an SPA shell, so cite page title/date/sections rather than brittle live line numbers. |
| LangChain repository metadata plus historical README snapshots. API: https://api.github.com/repos/langchain-ai/langchain. Oct 2022 README: https://raw.githubusercontent.com/langchain-ai/langchain/21b10ffb13/README.md. v0.0.1 README: https://raw.githubusercontent.com/langchain-ai/langchain/v0.0.1/README.md | Developer orchestration layer: composability first, later chains/data-augmented-generation/agents taxonomy. | Green/Yellow: GitHub API opened 2026-04-28 confirms repository creation timestamp 2022-10-17. Commit `21b10ffb13` (2022-10-25) says isolated LLM calls are often insufficient and power comes from combining LLMs with computation or knowledge; examples include self-ask-with-search and LLM Math. The v0.0.1 tag points to a July 2023 commit and can support later chains/data-augmented-generation/agents framing, not the October 2022 timeline. Use for framework pattern, not adoption magnitude. |
| LlamaIndex repository metadata. API: https://api.github.com/repos/run-llama/llama_index | Parallel data-framework pattern around documents and agents. | Yellow: GitHub API opened 2026-04-28 confirms repository creation timestamp 2022-11-02 and current description as a document agent/OCR platform. Use only as context unless a historical README snapshot is later pinned. |
| AutoGPT v0.1.0 README and repository metadata. Snapshot: https://raw.githubusercontent.com/Significant-Gravitas/AutoGPT/v0.1.0/README.md. API: https://api.github.com/repos/Significant-Gravitas/AutoGPT | Early public "agent" demo: GPT-4 loop, internet search, memory, file storage, and explicit authorization/cost limits. | Green/Yellow: v0.1.0 README opened 2026-04-28. It describes Auto-GPT as an experimental GPT-4 application that chains LLM "thoughts" and includes internet access, memory, and file storage; Usage says the user must type "NEXT COMMAND" after each action. GitHub API confirms repository creation 2023-03-16. Do not use current star count as historical adoption evidence. |

## Scene-Level Claim Table

| Claim | Scene | Primary Anchor | Independent Confirmation | Status | Notes |
|---|---|---|---|---|---|
| RAG combined a pretrained seq2seq parametric memory with non-parametric memory. | Retrieval As Memory | Lewis et al. p.1 abstract | Paper Section 1 | Green | Useful explanation hook: weights plus external index. |
| RAG's non-parametric memory was a dense vector index of Wikipedia accessed by a neural retriever. | Retrieval As Memory | Lewis et al. p.1 abstract | Section 2 / DPR retriever | Green | Avoid saying "vector database" for the 2020 paper unless framed as later infrastructure. |
| RAG's non-parametric memory could be replaced to update model knowledge. | Retrieval As Memory | Lewis et al. p.2 introduction | Architecture description | Green | Do not oversell as real-time freshness. |
| Retrieval can reduce hallucination pressure but does not make the system truthful by itself. | Retrieval As Memory | Lewis et al. p.1 intro on hallucination plus WebGPT caveats | OpenAI WebGPT page, Evaluating factual accuracy and Risks sections | Green | Phrase as "changes the failure surface." |
| WebGPT used a text-based browser that could search, follow links, scroll, and quote references. | Search Before Answering | WebGPT PDF p.1 and p.3 | OpenAI WebGPT page, intro section | Green | This is search-assisted answering, not general web autonomy. |
| WebGPT required reference collection to make human evaluation of factual accuracy easier. | Search Before Answering | WebGPT PDF p.1 | OpenAI WebGPT page, Evaluating factual accuracy section | Green | Good bridge from retrieval to evaluation. |
| WebGPT's best model was preferred over human demonstrations 56% of the time on ELI5 in the paper's setup. | Search Before Answering | WebGPT PDF p.1 | OpenAI WebGPT page, ELI5 results section | Green | Keep benchmark context narrow; do not generalize to all QA. |
| OpenAI itself warned that cited answers can still make basic errors or use unreliable sources. | Search Before Answering | OpenAI WebGPT page, TruthfulQA/Evaluating factual accuracy/Risks sections | Paper discussion | Green | Essential honesty guardrail. |
| ReAct interleaved reasoning traces and task-specific actions. | Tools As Hands | ReAct PDF p.1 abstract | Section 1 p.3 | Green | Use as conceptual hinge: reason, act, observe. |
| ReAct interacted with a Wikipedia API for QA/fact-verification tasks. | Tools As Hands | ReAct PDF p.1 abstract | Section 1 p.3 | Green | Keep API simple; do not call it a full browser. |
| ReAct was evaluated on HotpotQA, FEVER, ALFWorld, and WebShop. | Tools As Hands | ReAct PDF p.1 abstract | Section 1 p.3 | Green | Do not invent exact scores unless added later. |
| Toolformer learned to call APIs using self-supervised filtering of helpful calls. | Tools As Hands | Toolformer PDF p.1 abstract and Section 2 p.2 | Figure 2 / method | Green | Strong for "tools as model-learned interface." |
| Toolformer included calculator, Q&A, search, translation, and calendar tools. | Tools As Hands | Toolformer PDF p.1 abstract | Figure 1 | Green | Use concrete list sparingly. |
| ChatGPT plugins gave ChatGPT access to current information, computation, third-party services, and constrained actions. | Tools As Product | OpenAI plugins page, Overview section | OpenAI function-calling page, Function Calling section | Green | Product bridge from papers to platform. |
| OpenAI hosted browser and code-interpreter plugins and open-sourced a retrieval plugin. | Tools As Product | OpenAI plugins page, Overview/Retrieval sections | GitHub retrieval-plugin metadata | Green | Good scene anchor for "eyes, ears, hands." |
| OpenAI warned plugins introduced prompt injection and harmful/unintended action risks. | Tools As Product | OpenAI plugins page, Safety section | Function-calling page, tool-output safety note | Green | This is the safety boundary. |
| Function calling let developers describe functions and receive JSON arguments for external tools/APIs. | Tools As Product | OpenAI function-calling page, Function Calling section | Examples on same page | Green | This is interface design, not autonomy. |
| LangChain packaged composability around LLMs plus computation/knowledge in 2022, with later 2023 README framing around chains, data-augmented generation, and agents. | Agent Demo | LangChain Oct 2022 README commit plus v0.0.1 tag | GitHub metadata | Green/Yellow | Use as framework context, not adoption claim. |
| LlamaIndex represents the adjacent data/document framework pattern. | Agent Demo | GitHub metadata | Needs historical README snapshot | Yellow | Optional sentence only. |
| AutoGPT v0.1.0 framed itself as an experimental autonomous GPT-4 application with internet access, memory, file storage, and user authorization after actions. | Agent Demo | AutoGPT v0.1.0 README | GitHub repository metadata | Green/Yellow | Do not turn this into proof of reliable autonomy. |

## Conflict Notes

- Do not cite secondary hype articles as primary evidence for capability.
- Do not treat "agent" as a single stable technical definition across papers,
  platforms, and open-source frameworks.
- Do not claim RAG solves hallucination. WebGPT and plugins both show that
  external channels add new failure modes: source quality, citation quality,
  prompt injection, permissions, and action safety.
- Do not import serving-cost analysis from Ch63 except as a final handoff.
- Do not import benchmark-politics analysis from Ch66; WebGPT/ReAct/Toolformer
  benchmark details are local technical evidence, not the whole benchmark-war
  story.

## Anchor Worklist For Prose

- Use RAG p.1 abstract and Section 2 for the retrieval-memory explanation.
- Use WebGPT PDF and official page sections for source-citation benefits and risks.
- Use ReAct p.1/p.3 for interleaved reasoning/action, not for mature autonomy.
- Use Toolformer p.1/p.2 for API-call learning.
- Use OpenAI plugins and function-calling official page sections for product
  platformization and safety guardrails; avoid brittle live line numbers.
- Use AutoGPT v0.1.0 README only as a visible early demo of agent loops.

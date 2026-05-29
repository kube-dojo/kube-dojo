---
title: "LlamaIndex"
slug: ai-ml-engineering/frameworks-agents/module-1.4-llamaindex
sidebar:
  order: 505
---

> **Complexity**: `[COMPLEX]`
>
> **Time to Complete**: 5-6 hours
>
> **Prerequisites**: RAG fundamentals, embeddings, LangChain basics, and the context engineering concepts in [AI Engineering Foundations](/ai/ai-engineering-foundations/)

---

## What You'll Be Able to Do

- **Design** a LlamaIndex RAG architecture by separating ingestion, indexing, retrieval, synthesis, and orchestration responsibilities.
- **Compare** Documents, Nodes, index types, query engines, and chat engines when choosing the right data interface for an LLM application.
- **Implement** current LlamaIndex Python imports using `llama_index.core` plus integration packages instead of pre-0.10 monolithic imports.
- **Diagnose** retrieval failures caused by weak chunking, missing metadata, stale storage, or a mismatch between query intent and index structure.
- **Evaluate** whether a LlamaIndex system is production-ready across persistence, observability, evaluation, privacy, and agent integration boundaries.

## Why This Module Matters

At the end of a release week, a support lead watches a new assistant answer a policy question with total confidence and total wrongness. The model is not lazy, the prompt is not obviously broken, and the engineering team can reproduce the failure only when the question depends on a narrow paragraph buried in a private handbook. The raw model knows how to write, but it does not know which internal document should be trusted.

That is the moment when "use RAG" stops being a slogan and becomes an engineering problem. The team needs reliable ingestion, careful chunking, traceable metadata, an index that matches the question style, a query path that can filter and rerank evidence, and storage that survives deployment restarts. Without those pieces, retrieval becomes a decorative prelude to hallucination rather than a control mechanism for factual answers.

LlamaIndex exists for that exact layer of the stack. It is not merely a wrapper around an LLM call, and it is not only a vector database client. It is a data framework for LLM applications: a set of abstractions for turning messy source material into queryable context, then feeding that context into a model in a controlled way. LangGraph, and much of LangChain's agent layer, answers "what happens next in this workflow?"; LlamaIndex answers "what evidence should the model see, and why this context?"

This module teaches LlamaIndex as an architectural tool, not as a five-line demo. You will learn the vocabulary that makes LlamaIndex systems debuggable: Documents, Nodes, node parsers, indexes, retrievers, node postprocessors, response synthesizers, query engines, chat engines, storage contexts, and evaluation loops. The goal is not to memorize every class. The goal is to know where evidence enters the system, how it changes shape, and where a bad answer can be traced back to a bad data decision.

## The Boundary: Data Framework, Not Magic Orchestrator

The easiest way to misunderstand LlamaIndex is to compare it to a broad orchestration framework and ask which one "wins." That framing misses the point. Most serious LLM applications contain at least two concerns: deciding what work should happen next, and deciding what private or external knowledge should be placed in front of the model. LlamaIndex specializes in the second concern, while orchestration tools usually specialize in workflow state, tool routing, retries, and multi-step control flow.

Think of the application as a newsroom. The orchestrator is the editor assigning the story, deciding whether a fact-checker or reporter should act next, and approving the final draft. LlamaIndex is the research desk that maintains the archive, tags source material, retrieves the right clippings, and hands the editor a concise evidence packet. A newsroom can survive with a simple editor for a small story, and it can survive with a simple archive for a tiny beat, but it fails under pressure when the two responsibilities are blurred.

That boundary matters because RAG failures are rarely solved by adding more agent steps. If the assistant cannot find the refund exception paragraph, a better loop will only loop around missing evidence. If a summarization index is used for precise legal lookup, the model may receive a fluent overview when it needs exact wording. If all chunks lose their source metadata, the answer may sound correct but become impossible to audit. LlamaIndex gives names and extension points to those data-layer decisions.

In the current Python package layout, LlamaIndex is also intentionally split across namespaced packages. Core framework objects come from `llama_index.core`, while model, embedding, reader, vector store, and reranker integrations live in separate packages such as `llama-index-llms-openai`, `llama-index-embeddings-openai`, or `llama-index-readers-file`. That package boundary is a useful mental model: core abstractions are stable enough to design around, while integrations are chosen to match your model provider, storage backend, and data sources.

The first design question is therefore not "Should we use LlamaIndex or LangChain?" The better question is "Which part of the application is primarily about data access, and which part is primarily about control flow?" A documentation assistant that answers questions over a private handbook can be mostly LlamaIndex with a thin web service around it. A procurement agent that reads policy, calls vendor APIs, requests human approval, and opens tickets might use LlamaIndex for the policy retrieval layer and a workflow framework for the approval process.

The pipeline anatomy below is the simplest way to see the responsibility split. Raw content enters on the left, becomes a normalized LlamaIndex data model, is organized into one or more index structures, and is then queried through retrieval and synthesis components. The LLM is important, but it is near the end of the path rather than the only meaningful component.

```text
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Source Systems  │ --> │ Documents       │ --> │ Nodes           │
│ PDFs, wikis,    │     │ text + metadata │     │ chunks + links  │
│ APIs, tickets   │     │ source records  │     │ retrieval units │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        v
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Answer + Trace  │ <-- │ Query Pipeline  │ <-- │ Indexes         │
│ response, cited │     │ retrieve, rank, │     │ vector, summary,│
│ source nodes    │     │ synthesize      │     │ tree, keyword   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

There is a useful connection here to the context engineering spine of this curriculum. In [Context Engineering Fundamentals](/ai/ai-engineering-foundations/module-2.1-context-fundamentals/), context is treated as an engineered input rather than a pile of text appended to a prompt. LlamaIndex provides concrete Python objects for that idea. Instead of manually concatenating whatever a search endpoint returns, you can model how context is loaded, split, filtered, reordered, synthesized, persisted, and measured.

**Active learning prompt:** Before moving on, choose one application you have seen or built and draw a boundary line between orchestration work and data-framework work. If the system asks follow-up questions, calls APIs, or waits for human approval, mark that as orchestration. If the system loads documents, chunks them, searches them, reranks them, or cites them, mark that as LlamaIndex-shaped work. The exercise will make the rest of the module easier because every abstraction will have a place in the stack.

A common beginner mistake is to treat LlamaIndex as "the vector index library." Vector retrieval is the most common path, but it is only one index shape. LlamaIndex also exposes list-style summary indexes, tree indexes, keyword table indexes, property graph indexes, SQL query engines, document stores, vector stores, response synthesizers, retrievers, routers, node parsers, and callback hooks. You do not need all of them at once. You do need to know that LlamaIndex is broader than embedding text and calling nearest-neighbor search.

The second common mistake is to expect LlamaIndex to remove architectural judgment. It gives you strong defaults, but it does not know whether your support policy should be chunked by heading, sentence, paragraph, table row, or semantic boundary. It cannot infer whether old policy versions should remain searchable for audit questions or be hidden from current customer answers. It cannot decide whether a model should answer from a summary when exact clauses are required. Those are product and reliability decisions expressed through LlamaIndex components.

You reach for LlamaIndex when the hard part of the application is connecting an LLM to private, heterogeneous, or evolving data. You might skip it when the model only needs a single prompt, a small static context string, or a direct tool call. You might combine it with LangChain or LangGraph when the data layer is only one step inside a larger workflow. Good architecture is not framework loyalty; it is a clean boundary between context retrieval and action orchestration.

## Documents and Nodes: The Ingestion Contract

LlamaIndex begins by turning source material into a consistent data model. A `Document` is a container for source content and metadata. It might represent a text file, a PDF extraction result, a wiki page, an API response, a database row, or a manually constructed string during a prototype. A `Node` is the smaller retrieval unit derived from one or more documents. Most RAG quality work happens in the gap between those two objects.

The distinction is not cosmetic. Source systems usually store information in human authoring units: files, pages, records, tickets, sections, or documents. Retrieval systems need smaller machine units that fit model context windows and embedding models. If a forty-page handbook becomes one giant retrieval object, the model may receive too much irrelevant text. If the same handbook is split every few words, the retrieved chunks may lose the nearby explanation that gives a sentence meaning.

Documents preserve provenance. Nodes preserve retrievability. A strong ingestion design carries source metadata from the document into every node so that answers can later say which handbook, policy version, customer tier, timestamp, or product line supplied the evidence. When metadata is missing, retrieval may still appear to work in a demo, but production debugging becomes guesswork. A support assistant that cannot explain whether it used the current policy or last quarter's policy is not ready for real customers.

The ingestion flow below is deliberately plain. It is the part of the system many teams rush through because it feels like preprocessing. In practice, it is where later answer quality is either protected or damaged. The node parser is the point where you decide how source documents become chunks, and that decision controls what the retriever can possibly find.

```text
┌────────────────────┐
│ Raw source          │  refund-policy.md, handbook.pdf, ticket export
└─────────┬──────────┘
          │ reader or connector
          v
┌────────────────────┐
│ Document            │  text plus metadata such as product, date, owner
└─────────┬──────────┘
          │ node parser / splitter
          v
┌────────────────────┐
│ Nodes               │  chunks, metadata, ids, relationships
└─────────┬──────────┘
          │ index constructor
          v
┌────────────────────┐
│ Index               │  retrieval structure used by query engines
└────────────────────┘
```

Here is a complete, runnable Python example that builds Documents manually, parses them into Nodes, and then creates a vector index using mock models. The mock LLM and mock embedding model are useful for learning because the code exercises current LlamaIndex APIs without requiring an API key or network call. In a production application, you would replace those mocks with provider integrations such as OpenAI, Ollama, Hugging Face, or another supported backend.

> **Setup:** Run `pip install llama-index-core` before trying the Python examples. The `MockLLM` and `MockEmbedding` classes used here need no provider API keys.

```python
from llama_index.core import Document, MockEmbedding, Settings, VectorStoreIndex
from llama_index.core.llms import MockLLM
from llama_index.core.node_parser import SentenceSplitter

Settings.llm = MockLLM(max_tokens=128)
Settings.embed_model = MockEmbedding(embed_dim=8)

documents = [
    Document(
        text=(
            "Refunds for annual plans require manager approval. "
            "Customers may receive a prorated credit when cancellation happens "
            "within the first thirty days of renewal."
        ),
        metadata={"source": "support-handbook", "section": "refunds", "version": "2026-05"},
    ),
    Document(
        text=(
            "Security incidents must be acknowledged within one business hour. "
            "Customer-facing updates should use the approved incident template."
        ),
        metadata={"source": "support-handbook", "section": "security", "version": "2026-05"},
    ),
]

splitter = SentenceSplitter(chunk_size=128, chunk_overlap=20)
nodes = splitter.get_nodes_from_documents(documents)

index = VectorStoreIndex(nodes)
retriever = index.as_retriever(similarity_top_k=2)
results = retriever.retrieve("Can an annual-plan customer get a refund after renewal?")

for result in results:
    print(result.node.metadata)
    print(result.node.get_content())
```

Notice the sequence in that example. The `Document` objects carry metadata before splitting begins. The `SentenceSplitter` then creates nodes from those documents, and each node inherits the metadata needed for later filtering and citation. The `VectorStoreIndex` receives nodes rather than raw strings, which means retrieval can return content and provenance together. That provenance is how a serious application explains itself during review.

The same shape works when files come from disk. `SimpleDirectoryReader` is the beginner-friendly file reader in the current package layout, and it is imported from `llama_index.core`. The next example creates a tiny directory, writes two source files, reads them as Documents, and prints file metadata. It is intentionally small, but it shows the ingestion contract that remains true when the directory contains many files.

```python
from pathlib import Path

from llama_index.core import SimpleDirectoryReader

data_dir = Path("llamaindex_demo_docs")
data_dir.mkdir(exist_ok=True)

(data_dir / "refunds.txt").write_text(
    "Refund exceptions require a support manager note and the renewal date.",
    encoding="utf-8",
)
(data_dir / "security.txt").write_text(
    "Security incidents require customer updates through the approved template.",
    encoding="utf-8",
)

documents = SimpleDirectoryReader(
    input_files=[str(data_dir / "refunds.txt"), str(data_dir / "security.txt")]
).load_data()

for document in documents:
    print(document.metadata.get("file_name"), len(document.text))
```

One practical gotcha: `SimpleDirectoryReader` defaults to `exclude_hidden=True`, and that check applies to every path segment rather than only the file name, so a dot-directory anywhere in the absolute path, such as a `.worktrees` checkout, can hide every file; pass explicit `input_files`, or `exclude_hidden=False`, when that can happen.

The worked design decision is chunk size. Suppose a policy page contains short, self-contained paragraphs. A sentence-aware splitter with moderate overlap is likely safer than a fixed character splitter because it avoids cutting a rule in half. Suppose a developer guide contains long code blocks, headings, and tables. A markdown-aware or code-aware parser may preserve structure better than sentence splitting. Suppose a support ticket export contains one ticket per row. A row-level Document with metadata for ticket id, date, product, and severity may be more useful than a giant concatenated export.

Chunk overlap is a compromise rather than a magic number. Overlap helps when meaning crosses a boundary, but it also duplicates content in storage and increases the chance that near-identical chunks crowd out diverse evidence. Larger chunks preserve context but can dilute embeddings with unrelated topics. Smaller chunks improve precise retrieval but can strip a sentence of the section heading that explains it. The right choice depends on the questions the application must answer, not on a universal recipe.

Metadata deserves the same design attention as text. Source name is only the beginning. A practical system may need metadata for product, tenant, region, jurisdiction, document owner, effective date, expiration date, confidentiality label, language, canonical URL, heading path, and version. Some of those fields support filtering before retrieval. Others support answer citation after retrieval. Others support compliance review when a customer disputes an answer.

**Active learning prompt:** Take a document you know well, such as an onboarding guide or runbook, and identify three metadata fields that would matter during retrieval. Then identify one field that should never be shown to the model because it is sensitive, noisy, or operationally irrelevant. This separates retrieval metadata from prompt context, which is a core production habit.

The most important debugging question in ingestion is "Could the correct answer survive the transformation from source to node?" If the answer depends on a table header that was dropped by a PDF parser, retrieval cannot recover it. If the answer depends on a heading that was not copied into chunk metadata, a single paragraph may look ambiguous. If the answer depends on a policy date that was left outside metadata, the retriever may surface both old and new rules with equal confidence.

Good LlamaIndex design therefore treats ingestion as a contract. A Document promises that source text and source metadata have been captured. A Node promises that a retrievable unit has enough local context and provenance to be useful. An index promises that those nodes are organized for a specific query style. When any promise is weak, the model at the end of the pipeline inherits the weakness and makes it sound fluent.

## Indexes: Choosing the Shape of Memory

An index is a data structure for retrieving context. That sounds abstract until you compare it with familiar memory systems. A library catalog, a book index, a table of contents, a search engine, and a legal digest all organize knowledge differently because they answer different kinds of questions. LlamaIndex gives you several index shapes so you can align the retrieval structure with the user's task rather than forcing every question through vector similarity.

The most common index is `VectorStoreIndex`. It converts node text into embeddings and retrieves nodes whose vectors are close to the query vector. This is powerful for semantic search because the user does not need to use the same words as the document. "Can I get money back after renewal?" can retrieve a chunk about "prorated credit after cancellation" if the embedding model places those ideas near each other.

A vector index is not automatically the best answer for every job. If the user asks for a global summary of every quarterly report, a list-style summary index can be more natural because the system should consider many nodes rather than the top few similar chunks. If the user asks broad hierarchical questions, a tree index may help organize information through summaries. If the user asks exact term questions, a keyword table index can be useful because semantic similarity may blur names, codes, or identifiers.

The practical choice is less about which class looks modern and more about what failure mode you can tolerate. Vector retrieval may miss a precise keyword when the embedding model does not understand a domain-specific code. Summary-style retrieval may spend more tokens and smooth over details. Tree retrieval may depend heavily on summary quality. Keyword retrieval may miss paraphrases. Choosing an index is choosing which kind of mistake you will monitor.

| Index type | Best fit | Strength | Watch for |
|---|---|---|---|
| `VectorStoreIndex` | Semantic search, question answering, support docs, knowledge bases | Finds related meaning even when wording differs | Can miss exact identifiers or retrieve semantically similar but policy-wrong chunks |
| `SummaryIndex` | Summarization across many documents or when most nodes should be considered | Simple mental model and useful for broad synthesis | Can be expensive or noisy when the corpus is large and the question is narrow |
| `TreeIndex` | Hierarchical corpora and broad questions that benefit from summary layers | Provides an organized path through nested summaries | Summary errors can become retrieval errors at higher levels of the tree |
| `KeywordTableIndex` | Exact terms, named concepts, controlled vocabularies, codes | Makes lexical matches explicit and inspectable | Misses paraphrases and may depend on keyword extraction quality |

Here is a compact example showing the current import style for several index types. The code uses the same small document set so you can focus on what changes: the index class, not the source data. In real applications, you should not build every index blindly; you would build the one or two that match the query patterns your product actually supports.

```python
from llama_index.core import (
    Document,
    KeywordTableIndex,
    MockEmbedding,
    Settings,
    SummaryIndex,
    TreeIndex,
    VectorStoreIndex,
)
from llama_index.core.llms import MockLLM

Settings.llm = MockLLM(max_tokens=128)
Settings.embed_model = MockEmbedding(embed_dim=8)

documents = [
    Document(text="Annual plan refunds require approval and a renewal date check."),
    Document(text="Security incident updates must use the approved customer template."),
    Document(text="Enterprise customers can request a data export through support."),
]

vector_index = VectorStoreIndex.from_documents(documents)
summary_index = SummaryIndex.from_documents(documents)
tree_index = TreeIndex.from_documents(documents)
keyword_index = KeywordTableIndex.from_documents(documents)

print(type(vector_index).__name__)
print(type(summary_index).__name__)
print(type(tree_index).__name__)
print(type(keyword_index).__name__)
```

The worked example is a product policy assistant. The team has three query classes. Support agents ask narrow questions about current refund rules. Managers ask for summaries of what changed across the policy set. Compliance reviewers ask whether a specific named clause appears anywhere. A single index can answer all three weakly, but three query classes suggest at least two retrieval strategies: vector search for support questions, summary-oriented retrieval for change summaries, and keyword retrieval for named clauses.

The key design move is to start from query behavior rather than data volume. A small corpus can need multiple indexes when question types differ sharply. A large corpus can use one vector index if the product only supports narrow semantic lookup. The corpus size influences performance and storage choices, but the user's task determines the retrieval shape. That is why production RAG design begins with sample questions and expected evidence, not with a database logo.

For the support-agent query, the vector index might retrieve the two or three most semantically relevant nodes and pass them to a response synthesizer. For the manager summary query, the system might use a summary index or a query engine configured to cover more nodes. For the compliance reviewer, a keyword index or hybrid retrieval path might ensure exact clause names are not lost. This is also where an orchestrator can route between LlamaIndex tools without owning the data logic itself.

The similar problem for you is a developer documentation assistant. Users ask "How do I configure OAuth?", "What changed in the authentication guide this month?", and "Where is the `JWT_REFRESH_GRACE_SECONDS` setting documented?" The first query is semantic. The second is summary and version-aware. The third is exact. If you choose only vector search, identify what you will do to protect the exact setting lookup. If you choose multiple indexes, identify how the router knows which one to use.

Another index decision is where vectors live. LlamaIndex can use an in-memory vector store for learning and local prototypes, but production systems usually need a persistent vector backend such as Postgres with vector extensions, Qdrant, Pinecone, Weaviate, Milvus, OpenSearch, or another integration. The index abstraction lets the rest of the query pipeline look similar while storage changes underneath. That abstraction is useful, but it does not remove operational concerns like backups, tenancy, filtering semantics, and reindexing.

Index design should also include deletion and update behavior. A RAG application over policies is not append-only. Documents expire, clauses change, versions fork by region, and old drafts must stop influencing current answers. If node ids are unstable, updates may create duplicates instead of replacing stale chunks. If metadata does not include version and effective date, filters cannot separate current from historical context. The cost of fixing this later is high because users may already distrust the assistant.

The mature way to evaluate an index is to maintain a small set of representative questions with expected source nodes. Before changing chunking, embedding models, metadata filters, or vector backends, run those questions and inspect whether the same evidence appears. The answer text matters, but retrieval evidence matters first. If the right node never reaches the synthesizer, no amount of prompt polishing can guarantee the right answer.

## Query Pipeline: Retrieve, Rerank, Synthesize

The query pipeline is where LlamaIndex turns an index into an application-facing interface. A retriever selects candidate nodes. Optional node postprocessors filter, reorder, enrich, or redact those nodes. A response synthesizer asks the LLM to produce an answer from the selected evidence. A query engine packages those steps behind a `query()` method, while a chat engine adds conversational memory and turn handling for multi-turn interactions.

That sequence is worth memorizing because it gives you a debugging map. If the answer is wrong, first ask whether the retriever found the right nodes. If it found them but ranked them too low, inspect postprocessing or top-k settings. If the right nodes reached the synthesizer but the answer still misrepresented them, inspect the response mode, prompt templates, and model behavior. Without this map, every failure looks like "the LLM hallucinated," which is too vague to fix.

```mermaid
flowchart LR
    User[User question] --> Engine[Query engine]
    Engine --> Retriever[Retriever]
    Retriever --> Candidates[Candidate nodes]
    Candidates --> Post[Node postprocessors]
    Post --> Evidence[Filtered and ordered evidence]
    Evidence --> Synth[Response synthesizer]
    Synth --> Answer[Answer plus source nodes]
```

A query engine is best for stateless or lightly stateful question answering: one user question, one retrieval pass, one synthesized answer. A chat engine is best when the interface itself is conversational and prior turns should affect the next retrieval or response. The difference matters because chat history is not the same as retrieved knowledge. A chat engine can remember that the user is asking about the enterprise plan, but the refund rule should still come from the indexed policy source.

The next example builds a query engine explicitly from a retriever, a similarity postprocessor, and a compact response synthesizer. It uses mock models for runnability, so the generated prose is not the interesting part. The interesting part is the component boundary: retriever first, postprocessor second, synthesizer third. That boundary lets you test retrieval separately from generation.

```python
from llama_index.core import Document, MockEmbedding, Settings, VectorStoreIndex, get_response_synthesizer
from llama_index.core.llms import MockLLM
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.core.query_engine import RetrieverQueryEngine

Settings.llm = MockLLM(max_tokens=128)
Settings.embed_model = MockEmbedding(embed_dim=8)

documents = [
    Document(text="Refunds for annual renewals require manager approval."),
    Document(text="Security incidents require customer updates within one business hour."),
    Document(text="Data exports are available to enterprise customers through support."),
]

index = VectorStoreIndex.from_documents(documents)
retriever = index.as_retriever(similarity_top_k=3)

response_synthesizer = get_response_synthesizer(response_mode="compact")
query_engine = RetrieverQueryEngine.from_args(
    retriever=retriever,
    response_synthesizer=response_synthesizer,
    node_postprocessors=[SimilarityPostprocessor(similarity_cutoff=0.1)],
)

response = query_engine.query("What approval is needed for annual renewal refunds?")
print(response)
```

To compare the application-facing interfaces, run this immediately after the previous example while `index` and the mock `Settings` are still defined. The query engine treats each call as a single-shot question, while the chat engine keeps conversational memory so the second turn can depend on the first turn's topic.

```python
query_engine = index.as_query_engine()
chat_engine = index.as_chat_engine(chat_mode="context")

print(query_engine.query("Who approves annual renewal refunds?"))
print(chat_engine.chat("We are discussing annual renewal refunds."))
print(chat_engine.chat("Who approves them?"))
```

Node postprocessors are not decorative. They are the last controlled step before evidence enters the model context. A similarity cutoff can remove weak matches. A reranker can reorder candidates with a stronger but more expensive model. A metadata replacement postprocessor can retrieve small sentence nodes but pass a wider sentence window to the LLM. A privacy postprocessor can redact sensitive entities before synthesis. These steps are where retrieval quality and context budget meet.

Response synthesis is also a design choice. A compact response mode may combine evidence efficiently. A refine-style response can process chunks sequentially and revise the answer as it sees more context. A tree-style response can summarize intermediate groups before producing a final answer. Those modes make different trade-offs around latency, cost, faithfulness, and ability to handle many nodes. The right choice depends on whether the user expects a precise answer, a broad summary, or a structured extraction.

There is a subtle but important difference between retrieval evaluation and response evaluation. Retrieval evaluation asks whether the right evidence appeared in the candidate set, often with metrics such as recall at k or manual source-node inspection. Response evaluation asks whether the final answer was faithful, complete, and useful given the evidence. A system can have good retrieval and poor synthesis, or poor retrieval hidden by a lucky model guess. You need both views.

Source nodes are one of the most valuable debugging affordances in LlamaIndex. When a query engine returns an answer, inspect the nodes that were used to produce it. A product manager may care about answer wording, but an engineer should care about the path from user query to source node. If the answer cites the wrong document, the issue may be chunking, metadata filters, embedding model behavior, or query transformation. If it cites the right document but ignores a key sentence, the issue may be synthesis.

Query engines should usually be wrapped by application-specific policies. For example, a customer-facing assistant may refuse to answer if no source node clears a similarity threshold, or it may state that the indexed handbook does not contain enough evidence. An internal assistant may show low-confidence evidence to a human operator but avoid sending it to customers. LlamaIndex gives you the components, but your product determines what "safe enough to answer" means.

This connects directly to [Retrieval, Tools, and Memory Boundaries](/ai/ai-engineering-foundations/module-2.3-retrieval-tools-and-memory-boundaries/). Retrieved context is not memory just because it appears in the prompt, and a tool result is not trustworthy just because a framework returned it. The query pipeline should preserve the boundary between candidate evidence, selected evidence, synthesized answer, and any downstream action. That boundary prevents a weak retrieval result from silently becoming a business decision.

When you debug a LlamaIndex answer, resist the urge to start by rewriting the final prompt. First print the retrieved nodes. Then print their metadata. Then lower or raise `similarity_top_k` and see whether the expected source appears. Then test a postprocessor or reranker. Then adjust synthesis. This order follows the data path and keeps the model from becoming a mysterious final box where all errors are blamed.

## Storage and Persistence: Keeping the Index Alive

Prototypes often build an index in memory every time a notebook runs. Production systems cannot treat indexing as a temporary variable. Ingesting documents may be expensive, embedding calls may cost money, and users expect the same policy corpus to be available after a service restart. LlamaIndex models persistence through storage components and a `StorageContext`, which coordinates document stores, index stores, vector stores, and related backing systems.

The simplest persistence path is local disk. You build an index, call `index.storage_context.persist()`, then later recreate a storage context and load the index. This is not the final production architecture for every team, but it teaches the persistence boundary clearly. The index is not only Python object state; it has serialized backing data that can be reloaded.

```python
from pathlib import Path

from llama_index.core import (
    Document,
    MockEmbedding,
    Settings,
    StorageContext,
    VectorStoreIndex,
    load_index_from_storage,
)
from llama_index.core.llms import MockLLM

Settings.llm = MockLLM(max_tokens=128)
Settings.embed_model = MockEmbedding(embed_dim=8)

documents = [
    Document(text="Annual renewal refunds require manager approval."),
    Document(text="Enterprise data exports are handled through support."),
]

index = VectorStoreIndex.from_documents(documents)
persist_dir = Path("llamaindex_storage")
index.storage_context.persist(persist_dir=str(persist_dir))

storage_context = StorageContext.from_defaults(persist_dir=str(persist_dir))
reloaded_index = load_index_from_storage(storage_context)

query_engine = reloaded_index.as_query_engine()
print(query_engine.query("Who handles data exports?"))
```

Local persistence also reveals an important operational question: what exactly is being persisted? In a simple local setup, LlamaIndex can persist local stores under a directory. In a remote vector store setup, the vector database may persist vectors independently, while the document store and index store still need compatible configuration. If you later move from local storage to a managed vector database, do not assume every piece of state moved with it. Recreate the storage context deliberately.

Multiple indexes can share a storage directory when index ids are managed carefully. That is useful for applications that maintain separate indexes for policies, runbooks, release notes, and incident reports. It also creates a naming and lifecycle problem. If index ids are casual strings typed into notebooks, a deployment can load the wrong index or fail when a second index appears. Production persistence needs naming conventions, migration notes, and tests that load the intended index from a clean process.

Persistence is not only about saving bytes. It is also about freshness. A stale index is worse than no index when users believe it reflects current policy. Teams should define how source changes trigger reindexing, whether updates are incremental or full, how deletions propagate, how long old versions remain queryable, and whether answers should expose the data freshness timestamp. A RAG assistant over changing documents should be able to say which corpus version it used.

The storage boundary is also where tenant isolation becomes concrete. If one customer's documents share a vector collection with another customer's documents, metadata filters and access controls must be tested aggressively. If filters are applied only after retrieval, forbidden nodes may still influence ranking or intermediate processing depending on the backend and query path. A safer design enforces tenant boundaries at the storage or collection level when regulatory or contractual isolation matters.

There is a useful anti-pattern called "index by deployment." It happens when every application deploy rebuilds a new index from whatever files happen to be available at that moment. The team has no stable corpus version, no repeatable source snapshot, and no way to compare retrieval results before and after a code change. Better systems separate content ingestion from application deploys. The app loads a named, tested index version and rolls forward only after retrieval checks pass.

Backups and disaster recovery deserve the same treatment as any other data system. If embeddings are expensive to recreate, back up vector stores and document stores. If source documents can be reloaded cheaply but embedding costs are high, document the rebuild path and expected time. If compliance requires answer auditability, preserve the source node text and metadata used for important answers. LlamaIndex gives you storage hooks, but durability remains an operations responsibility.

## Production Concerns: Evaluation, Observability, and Agents

A LlamaIndex application becomes production-ready when the team can explain its answers, measure retrieval quality, observe failures, update data safely, and integrate with broader workflows without blurring boundaries. A demo that answers three questions correctly in a notebook is useful learning evidence, but it is not operational evidence. Production readiness begins when the system is boring enough to test repeatedly.

Evaluation should start with a small golden set of questions and expected evidence. For each question, record the source document, the node or section that should be retrieved, and the answer behavior that would be acceptable. Run the set after changing chunking, metadata filters, embedding models, rerankers, response modes, or vector stores. This is the same habit used in conventional search engineering: measure the retrieval layer before celebrating the generated answer.

Observability should show the query path. At minimum, capture the user query, retrieval parameters, returned node ids, source metadata, similarity scores when available, postprocessor decisions, response mode, model name, latency, token usage, and final answer. Sensitive content may need hashing or redaction, but the trace should still tell an engineer where the system failed. "The assistant was wrong" is an incident report; "the retriever returned only expired policy nodes because the effective-date filter was missing" is a fixable diagnosis.

Privacy and security should be designed before connectors multiply. Readers can pull from local files, cloud stores, APIs, wikis, databases, and specialized systems. Every connector expands the trust boundary. Decide which sources are allowed, which metadata is safe to expose, how secrets are loaded, whether documents contain personal data, and whether retrieved nodes can be sent to a third-party model. RAG can reduce hallucination risk while increasing data exposure risk if retrieval is not governed.

Agents make LlamaIndex more useful and more dangerous. A LlamaIndex query engine can be exposed as a tool to an agent, letting the agent ask the knowledge base before taking action. That is often the right architecture: LlamaIndex remains the evidence tool, while the agent framework handles planning and action. The danger appears when the agent treats any retrieved text as permission to act. Retrieval is evidence, not authority. Business rules still need explicit validation.

One practical production pattern is to expose several LlamaIndex tools with narrow names and descriptions. For example, an agent might have `search_current_policy`, `summarize_release_notes`, and `lookup_incident_runbook` rather than one vague `ask_documents` tool. Narrow tools make routing easier, logs clearer, and failures easier to diagnose. Under the hood, each tool may use a different index, retriever configuration, metadata filter, or response synthesizer.

Another practical pattern is human-in-the-loop escalation based on evidence quality. If retrieval returns no nodes above a threshold, the system should not pretend to know. If retrieved nodes conflict across versions, the system can ask a human reviewer or present both sources with dates. If a user asks for regulated advice, the application can require a human-approved answer template. LlamaIndex helps surface evidence; your application policy decides whether evidence is sufficient.

Production teams should also watch cost. Indexing cost includes loading, parsing, embedding, storing, and updating data. Query cost includes embedding the query, retrieving candidates, reranking, synthesizing, and tracing. A response mode that is acceptable for a nightly analyst summary may be too slow for an interactive support chat. A reranker that improves quality may still be reserved for high-value or low-confidence queries. Cost controls are part of system design rather than afterthought accounting.

The final production concern is maintainability. LlamaIndex has many extension points, and that is powerful, but a system with custom readers, custom node parsers, custom retrievers, custom postprocessors, and custom prompt templates needs tests and documentation. Keep the first version boring. Prefer explicit metadata, source-node inspection, small golden datasets, and simple storage. Add advanced retrieval only when a measured failure justifies it.

The durable mental model is simple: LlamaIndex is the evidence preparation and retrieval layer for LLM applications. It does not absolve you from designing source governance, retrieval evaluation, answer policy, or workflow orchestration. It gives you the right seams to implement those responsibilities deliberately. When the system fails, those seams let you inspect where the answer stopped being grounded.

## Did You Know?

- **LlamaIndex uses namespaced Python packages**: The current ecosystem separates core abstractions from integrations, so modern examples import framework objects from `llama_index.core` and install provider-specific packages as needed.
- **Nodes are first-class retrieval units**: A Node can store text, metadata, relationships, and identifiers, which makes it more than a plain string chunk.
- **Response synthesis is configurable**: Query engines can use different synthesis modes, which changes how retrieved nodes are combined into an answer.
- **Directory readers filter hidden path segments by default**: `SimpleDirectoryReader` can treat dot-prefixed directories in the absolute path as hidden, so explicit file lists are safer in generated examples and worktree checkouts.

## Common Mistakes

| Mistake | Why It Hurts | Better Approach |
|---|---|---|
| Treating LlamaIndex as only a vector database wrapper | The team misses node parsing, metadata, postprocessing, synthesis, storage, and evaluation extension points | Model the full ingestion-to-answer pipeline and decide which component owns each decision |
| Using old top-level `llama_index` imports | Pre-0.10 examples can fail or hide the current package boundary between core and integrations | Use `from llama_index.core import ...` for core objects and install integration packages explicitly |
| Chunking before understanding user questions | The correct answer may be split away from headings, dates, tables, or nearby caveats | Design chunking against representative questions and inspect whether expected source nodes survive |
| Dropping metadata during ingestion | Retrieval may work in a demo but answers cannot be filtered, cited, audited, or debugged | Attach source, version, date, tenant, product, and access metadata before nodes are created |
| Choosing `VectorStoreIndex` for every query style | Semantic search can be weak for exact identifiers, broad summaries, or hierarchical exploration | Match index type and retrieval strategy to semantic lookup, summarization, exact terms, or routing needs |
| Debugging only the final LLM answer | The model gets blamed for failures caused by missing evidence or bad ranking | Print retrieved nodes, metadata, scores, postprocessor output, and synthesis configuration first |
| Rebuilding indexes casually on every deploy | Corpus versions drift and retrieval changes become impossible to reproduce | Separate ingestion from deployment, name index versions, and run retrieval checks before rollout |
| Exposing one vague document tool to agents | Agents may route poorly and logs become difficult to interpret | Create narrow LlamaIndex-backed tools with clear names, descriptions, filters, and evidence policies |

## Quiz

<details>
<summary>1. Your team wants an assistant that answers employee handbook questions, opens HR tickets, and asks managers for approval. Where should LlamaIndex sit in that architecture?</summary>

LlamaIndex should own the handbook ingestion, chunking, indexing, retrieval, and answer synthesis over policy evidence. The ticket creation and manager approval steps belong to an orchestration layer or application workflow because they involve stateful actions and human coordination. A clean design exposes LlamaIndex as a policy evidence tool rather than making it responsible for the whole business process.

</details>

<details>
<summary>2. A refund policy answer is wrong, and the final prompt looks reasonable. What should you inspect before rewriting the prompt?</summary>

Inspect the retrieved nodes, their metadata, similarity scores if available, and any node postprocessor output. If the correct policy node never reached the response synthesizer, prompt rewriting will only hide the real retrieval failure. The likely causes are chunking, stale indexes, weak metadata filters, top-k settings, embedding behavior, or an index type that does not match the query.

</details>

<details>
<summary>3. A developer copied an old tutorial that imports `VectorStoreIndex` from the top-level `llama_index` package. Why is that risky in a current codebase?</summary>

Current LlamaIndex examples use the namespaced package layout, with core objects imported from `llama_index.core` and optional integrations installed separately. Old monolithic imports may fail, pull in unexpected dependencies, or teach the wrong architecture. The safer current style is `from llama_index.core import VectorStoreIndex, SimpleDirectoryReader` plus explicit provider packages for LLMs, embeddings, readers, vector stores, and rerankers.

</details>

<details>
<summary>4. A compliance reviewer asks for the exact location of a named clause, but semantic vector search keeps returning related summaries. What design change would you evaluate?</summary>

Evaluate keyword or hybrid retrieval, stronger metadata filters, and chunking that preserves heading paths and clause identifiers. A vector index is strong for paraphrased semantic lookup, but exact named clauses often need lexical signals. The final design might route exact identifier queries to a keyword table index or a hybrid retriever while leaving ordinary policy questions on vector retrieval.

</details>

<details>
<summary>5. A chat assistant remembers that the user is asking about enterprise plans. Does that mean it can skip retrieval on the next policy question?</summary>

No. Chat memory can preserve conversational context, but policy evidence should still come from the indexed source of record. The chat engine may use prior turns to shape the next query, such as adding "enterprise plan" to the retrieval intent, but the answer should remain grounded in retrieved nodes. Conversation history is not a substitute for authoritative data.

</details>

<details>
<summary>6. After a deploy, answers cite last month's policy even though the source file changed. Which persistence and freshness checks matter?</summary>

Check whether ingestion actually re-ran, whether the old nodes were deleted or replaced, whether index ids point to the intended stored index, whether metadata includes effective dates, and whether the application loaded the correct storage context. A stale persisted index can survive a code deploy, so content versioning and retrieval checks must be part of rollout.

</details>

<details>
<summary>7. An agent has one tool named `ask_documents`, backed by a large mixed corpus. It often asks the wrong source. How would you redesign the LlamaIndex boundary?</summary>

Split the vague tool into narrower LlamaIndex-backed tools with clear descriptions, such as `search_current_policy`, `lookup_incident_runbook`, and `summarize_release_notes`. Each tool can use its own index, metadata filters, retriever settings, and response policy. The agent then routes by task intent while LlamaIndex keeps evidence retrieval specialized and inspectable.

</details>

## Hands-On Exercise

This is a design-and-reading exercise rather than a cluster lab. Choose a realistic knowledge assistant, such as an internal policy assistant, release-note explainer, support handbook assistant, or developer documentation search tool. Your job is to write a short architecture note that explains how LlamaIndex would turn source material into grounded answers, where it would stop, and what another orchestration layer would own.

Start from five representative user questions before choosing components. Include at least one narrow lookup question, one broad summary question, one exact identifier question, and one question that should be refused or escalated because the evidence is weak. Then sketch the ingestion path, metadata fields, index choice, query pipeline, persistence strategy, and evaluation checks. The result should be specific enough that another engineer could implement a first prototype without guessing your retrieval intent.

- [ ] **Design** a LlamaIndex RAG architecture that separates ingestion, indexing, retrieval, synthesis, and orchestration responsibilities.
- [ ] **Compare** Documents, Nodes, index types, query engines, and chat engines for the chosen assistant.
- [ ] **Implement** a small import plan using current `llama_index.core` imports plus any needed integration packages.
- [ ] **Diagnose** two likely retrieval failures caused by chunking, metadata, stale storage, or mismatched index structure.
- [ ] **Evaluate** production readiness with persistence, observability, retrieval evaluation, privacy, and agent-tool boundaries.

## Sources

- [LlamaIndex Installation and Setup](https://developers.llamaindex.ai/python/framework/getting_started/installation/)
- [LlamaIndex SimpleDirectoryReader](https://developers.llamaindex.ai/python/framework/module_guides/loading/simpledirectoryreader/)
- [LlamaIndex Documents and Nodes](https://developers.llamaindex.ai/python/framework/module_guides/loading/documents_and_nodes/)
- [LlamaIndex Node Parser Usage Pattern](https://developers.llamaindex.ai/python/framework/module_guides/loading/node_parsers/)
- [LlamaIndex Indexing](https://developers.llamaindex.ai/python/framework/module_guides/indexing/)
- [LlamaIndex How Each Index Works](https://developers.llamaindex.ai/python/framework/module_guides/indexing/index_guide/)
- [LlamaIndex VectorStoreIndex Guide](https://developers.llamaindex.ai/python/framework/module_guides/indexing/vector_store_index/)
- [LlamaIndex Querying](https://developers.llamaindex.ai/python/framework/module_guides/querying/)
- [LlamaIndex Node Postprocessor Guide](https://developers.llamaindex.ai/python/framework/module_guides/querying/node_postprocessors/)
- [LlamaIndex Response Synthesizer Guide](https://developers.llamaindex.ai/python/framework/module_guides/querying/response_synthesizers/)
- [LlamaIndex Persisting and Loading Data](https://developers.llamaindex.ai/python/framework/module_guides/storing/save_load/)
- [LlamaIndex Settings Guide](https://developers.llamaindex.ai/python/framework/module_guides/supporting_modules/settings/)

## Next Module

Next: [Building AI Agents](/ai-ml-engineering/frameworks-agents/module-1.5-building-ai-agents/)

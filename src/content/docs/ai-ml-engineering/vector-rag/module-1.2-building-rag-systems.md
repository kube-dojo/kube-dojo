---
title: "Building RAG Systems"
slug: ai-ml-engineering/vector-rag/module-3.2-building-rag-systems
sidebar:
  order: 403
---
> **AI/ML Engineering Track** | Complexity: `[COMPLEX]` | Time: 6-8
# Or: Teaching AI to Look Things Up Before Making Stuff Up

---
**Reading Time**: 6-7 hours
**Prerequisites**: Modules 9-11
---

New York City. March 3, 2021. 9:17 AM. Sarah Chen, Lead ML Engineer at a major investment bank, was reviewing the overnight logs from their new AI customer service chatbot. Her coffee went cold as she scrolled.

"What's the current interest rate on your savings accounts?"
"Our savings accounts offer a competitive 4.5% APY!"

The actual rate was 0.5%. The chatbot had confidently hallucinated a number nine times higher than reality. And it had told this to 847 customers overnight.

By noon, the legal team was involved. By 5 PM, the project was suspended. By end of week, the CTO who had championed the launch had resigned. The bank spent the next three months calling customers to clarify that no, they weren't actually getting 4.5% interest.

The chatbot wasn't broken—it was working exactly as designed. GPT-3 was simply doing what language models do: generating plausible-sounding text based on patterns. It had no way to know the bank's actual rates because that information didn't exist in its training data.

Six months later, Sarah built a new system. This one didn't rely on the model's "knowledge" at all. Instead, every customer question first triggered a database lookup. The relevant account information was then inserted directly into the prompt. The model became a skilled translator, converting retrieved facts into natural language—not a unreliable oracle expected to know everything.

> "RAG changed everything for us. The model stopped being a liability and became an asset. It's the difference between asking someone to guess your phone number versus handing them your contact card and asking them to read it aloud."
> — Sarah Chen, speaking at MLconf 2022

That pattern—Retrieve, Augment, Generate—is now the foundation of every enterprise AI deployment. And you're about to learn exactly how it works.

In 2021, a bank discovered the hard way that language models confidently hallucinate answers when they don't have access to real data. RAG solved this problem by teaching AI to look things up before making things up. Today, every major enterprise AI system—from ChatGPT plugins to Perplexity to internal company assistants—uses RAG to ground language model responses in actual facts.

---

## What You'll Be Able to Do

By the end of this module, you will:
- Understand RAG architecture (Retrieval-Augmented Generation) deeply
- Build a production-ready RAG pipeline from scratch
- Master document chunking strategies (fixed, semantic, recursive)
- Implement effective retrieval with reranking
- Measure RAG performance with proper evaluation metrics
- Handle edge cases (hallucination, context limits, stale data)
- Apply RAG to real projects (kaizen, vibe, contrarian)

**Why this matters**: RAG is the #1 technique for building AI systems that need current, accurate, domain-specific knowledge. It's how ChatGPT plugins work, how enterprise AI assistants access company data, and how you'll build kaizen's knowledge system.

---

## Did You Know? The $100 Million Problem RAG Solved

In **2020**, a major bank deployed a GPT-3-powered customer service chatbot. Within weeks, disaster struck:

**Customer**: "What's my account balance?"
**Bot**: "Your account balance is $15,432.67"

**The problem**: The bot hallucinated a random number! GPT-3 had no access to actual account data - it just made up a plausible-sounding answer.

**The fallout**:
- **$2.3 million** in customer service costs to clean up confusion
- **Legal investigation** for potentially misleading customers
- Project scrapped after 3 months
- CTO resigned

**The insight**: LLMs are **knowledge-frozen** at training time. They can't know your company data, current events, or user-specific information. They can only generate plausible text based on patterns.

**The solution**: RAG (Retrieval-Augmented Generation)

Instead of asking the LLM to "know" the answer, you:
1. **Retrieve** relevant documents from your database
2. **Augment** the prompt with retrieved context
3. **Generate** an answer based on actual data

```
Without RAG:
User: "What's the status of order #12345?"
LLM: "Your order is being processed." (HALLUCINATION - made up!)

With RAG:
User: "What's the status of order #12345?"
→ Retrieve order from database: {"id": 12345, "status": "shipped", "tracking": "1Z999..."}
→ Prompt: "Based on this order data: {data}, answer: What's the status of order #12345?"
LLM: "Your order #12345 has shipped! Tracking number: 1Z999..." (ACCURATE!)
```

**The transformation**: RAG turned LLMs from "impressive but unreliable" to "production-ready for enterprise." Every major AI company now uses RAG for knowledge-intensive applications.

---

## Introduction: What Is RAG?

### The Core Concept

**RAG = Retrieval-Augmented Generation**

Think of RAG like an open-book exam versus a closed-book exam. In a closed-book exam (standard LLM), you can only answer based on what you memorized during studying (training). In an open-book exam (RAG), you bring your textbooks and notes—you don't need to memorize everything because you can look it up when needed. The LLM becomes better at synthesizing and explaining information you provide rather than trying to recall everything from memory.

It's a two-step process:
1. **Retrieval**: Find relevant information from a knowledge base
2. **Generation**: Use an LLM to generate an answer using that information

```
┌─────────────────────────────────────────────────────────────────┐
│                         RAG Pipeline                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  User Query: "How do I configure authentication in kaizen?"    │
│       │                                                        │
│       ▼                                                        │
│  ┌─────────────┐                                               │
│  │   Embed     │  → Convert query to vector                    │
│  └─────────────┘                                               │
│       │                                                        │
│       ▼                                                        │
│  ┌─────────────┐     ┌──────────────────┐                     │
│  │   Search    │ ──► │  Vector Database │                     │
│  └─────────────┘     │  (176K docs)     │                     │
│       │              └──────────────────┘                     │
│       ▼                                                        │
│  Retrieved Context:                                            │
│  - "auth.md: Configure JWT tokens..."                         │
│  - "security.md: Best practices for..."                       │
│  - "api.md: Authentication endpoints..."                      │
│       │                                                        │
│       ▼                                                        │
│  ┌─────────────┐                                               │
│  │   Generate  │  → LLM creates answer from context           │
│  └─────────────┘                                               │
│       │                                                        │
│       ▼                                                        │
│  Answer: "To configure authentication in kaizen:               │
│          1. Set JWT_SECRET in .env                            │
│          2. Configure auth middleware in app.py               │
│          3. See auth.md for complete guide..."                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Why RAG Works

Think of an LLM like a very smart person who studied intensively but then went into a time capsule. They know everything up to their "graduation date" (the training cutoff), but nothing after. They also never saw your private documents, your company's internal wikis, or your customer data. RAG is like giving this smart person access to a library and saying "look this up before you answer"—suddenly they can answer questions about anything in that library, even topics they never studied.

**LLMs have two fundamental limitations**:

1. **Knowledge cutoff**: Trained on data up to a certain date
   - gpt-5: October 2023 (but updates regularly)
   - Claude 3.5/4: Early 2024
   - Models get updated - always check current cutoff dates!
   - Can't know about events after training

2. **No private data**: Never saw your company's internal documents
   - Can't answer questions about your codebase
   - Can't access your databases
   - Can't know your business rules

**RAG solves both** by injecting relevant information into the prompt at query time.

---

## Did You Know? The Paper That Started It All

**May 2020**: Facebook AI Research (FAIR) published "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks" - the paper that gave RAG its name.

**The key insight**: Instead of making models bigger to store more knowledge, give them access to external knowledge at inference time.

**The results were stunning**:
- **Open-domain QA**: RAG outperformed GPT-3 (175B params) with only 400M params
- **Fact verification**: 94% accuracy vs 72% for pure generation
- **Knowledge updates**: Change the database, instantly update the model's "knowledge"

**The authors**: Patrick Lewis, Ethan Perez, Aleksandra Piktus, and team at Facebook AI

**Why this matters**: RAG proved that **architecture + retrieval** beats **bigger models alone**. This insight shaped the entire industry - ChatGPT's web browsing, Perplexity, and every enterprise AI assistant uses RAG.

**Citation count**: Over 3,000 citations in 4 years - one of the most influential AI papers of the decade!

---

## STOP: Time to Practice!

**You've learned the concept - now let's build a RAG system!**

RAG is best learned by doing. You'll build a complete RAG pipeline that could power kaizen's documentation assistant.

### Practice Path (~4-5 hours total)

**1. [Simple RAG Pipeline](../../examples/module_12/01_simple_rag.py)** - Your first RAG system
   -  Concept: Basic retrieval + generation
   - ⏱️ Time: 90-120 minutes
   - Goal: Build working RAG in 100 lines
   - What you'll learn: The core RAG loop

**2. [Document Chunking](../../examples/module_12/02_chunking_strategies.py)** - Master chunking
   -  Concept: Fixed, semantic, and recursive chunking
   - ⏱️ Time: 60-75 minutes
   - Goal: Understand how chunking affects retrieval quality
   - What you'll learn: Chunk size is the #1 RAG parameter!

**3. [RAG Evaluation](../../examples/module_12/03_rag_evaluation.py)** - Measure quality
   -  Concept: Retrieval metrics, answer quality, hallucination detection
   - ⏱️ Time: 60-75 minutes
   - Goal: Know when your RAG is working well
   - What you'll learn: You can't improve what you don't measure

### Deliverable: Production RAG System

**What**: Build a RAG system for one of your projects
**Time**: 5-6 hours
**Portfolio Value**: Demonstrates end-to-end AI system building

**Requirements**:
1. Choose a knowledge base:
   - **kaizen**: Documentation + code + issues
   - **vibe**: Course content + student Q&A
   - **contrarian**: Financial reports + news
   - **Work**: Infrastructure runbooks + incident reports

2. Implement complete pipeline:
   - Document ingestion (PDF, Markdown, code)
   - Chunking strategy (justify your choice!)
   - Vector storage (Qdrant from Module 11)
   - Retrieval with reranking
   - Answer generation with citations
   - Streaming responses

3. Evaluation dashboard:
   - Test set of 20+ queries with expected answers
   - Retrieval metrics (recall@k, MRR)
   - Answer quality metrics (faithfulness, relevance)
   - Latency tracking

4. Handle edge cases:
   - "I don't know" for out-of-scope queries
   - Citation verification
   - Confidence scoring

**Success Criteria**:
- Answers questions accurately from your knowledge base
- Provides citations/sources for answers
- Handles "I don't know" gracefully
- < 3 second response time
- Evaluation metrics documented

---

## ️ RAG Architecture Deep Dive

### The Three Phases

Think of a RAG system like a research librarian helping a student. In Phase 1 (Indexing), the librarian organizes all the books—creating an index card for each section so they can be found quickly. In Phase 2 (Retrieval), when a student asks a question, the librarian searches the card catalog and pulls the most relevant books off the shelves. In Phase 3 (Generation), the librarian reads the relevant passages and synthesizes an answer tailored to the student's question.

```
┌───────────────────────────────────────────────────────────────────┐
│                    RAG System Architecture                        │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  PHASE 1: INDEXING (Offline - done once per document update)     │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────────┐   │
│  │Documents│ →  │ Chunk   │ →  │ Embed   │ →  │Store in     │   │
│  │(raw)    │    │         │    │         │    │Vector DB    │   │
│  └─────────┘    └─────────┘    └─────────┘    └─────────────┘   │
│                                                                   │
│  PHASE 2: RETRIEVAL (Online - per query)                         │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────────┐   │
│  │  Query  │ →  │ Embed   │ →  │ Search  │ →  │Top-K        │   │
│  │         │    │         │    │Vector DB│    │Documents    │   │
│  └─────────┘    └─────────┘    └─────────┘    └─────────────┘   │
│                                                                   │
│  PHASE 3: GENERATION (Online - per query)                        │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────────┐   │
│  │Context  │ →  │ Build   │ →  │  LLM    │ →  │  Answer     │   │
│  │+ Query  │    │ Prompt  │    │Generate │    │             │   │
│  └─────────┘    └─────────┘    └─────────┘    └─────────────┘   │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

### Phase 1: Indexing

Think of indexing like preparing a recipe book for quick access. Instead of reading every page to find "chocolate cake," you create an index at the back: "chocolate cake, p. 47." Vector databases do the same thing, but instead of page numbers, they store mathematical representations (vectors) that capture the meaning of each text chunk.

**Goal**: Convert documents into searchable vectors

```python
def index_documents(documents: list[str], vector_db: QdrantClient):
    """Index documents into vector database."""
    for doc in documents:
        # 1. Chunk the document
        chunks = chunk_document(doc, chunk_size=500, overlap=50)

        # 2. Generate embeddings
        embeddings = embedding_model.encode(chunks)

        # 3. Store in vector database
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            vector_db.upsert(
                collection_name="documents",
                points=[{
                    "id": f"{doc.id}_{i}",
                    "vector": embedding,
                    "payload": {
                        "text": chunk,
                        "source": doc.filename,
                        "chunk_index": i
                    }
                }]
            )
```

**Key decisions**:
- **Chunk size**: Too small = loses context, too large = dilutes relevance
- **Overlap**: Prevents information loss at chunk boundaries
- **Metadata**: Store source info for citations

### Phase 2: Retrieval

Think of retrieval like a detective searching for clues. You have a case (the user's question) and a warehouse of evidence (your document chunks). The detective doesn't read every file—they use their training to quickly identify which evidence boxes are most likely to contain relevant clues, then pull those specific boxes for closer examination.

**Goal**: Find the most relevant chunks for a query

```python
def retrieve(query: str, vector_db: QdrantClient, k: int = 5) -> list[dict]:
    """Retrieve top-k relevant chunks."""
    # 1. Embed the query
    query_embedding = embedding_model.encode(query)

    # 2. Search vector database
    results = vector_db.search(
        collection_name="documents",
        query_vector=query_embedding,
        limit=k
    )

    # 3. Return chunks with metadata
    return [
        {
            "text": r.payload["text"],
            "source": r.payload["source"],
            "score": r.score
        }
        for r in results
    ]
```

**Key decisions**:
- **k value**: More chunks = more context but also more noise
- **Similarity threshold**: Filter out low-relevance results
- **Reranking**: Use a second model to reorder results

### Phase 3: Generation

Think of generation like a journalist writing an article. The journalist (LLM) doesn't make up facts—they synthesize information from their research notes (retrieved chunks) into a coherent, readable answer that directly addresses the reader's question.

**Goal**: Generate an answer using retrieved context

```python
def generate_answer(query: str, context: list[dict], llm) -> str:
    """Generate answer from retrieved context."""
    # Build prompt with context
    context_text = "\n\n".join([
        f"[Source: {c['source']}]\n{c['text']}"
        for c in context
    ])

    prompt = f"""Answer the question based ONLY on the following context.
If the context doesn't contain the answer, say "I don't have information about that."

Context:
{context_text}

Question: {query}

Answer:"""

    # Generate with LLM
    response = llm.generate(prompt)

    return response
```

**Key decisions**:
- **Prompt engineering**: Instructions for using context, handling unknowns
- **Citation format**: How to attribute sources
- **Answer length**: Concise vs detailed responses

---

##  Document Chunking: The Most Important Decision

### Why Chunking Matters

**The chunking paradox**:
- **Too small**: Chunks lack context, retrieval returns fragments
- **Too large**: Chunks contain irrelevant info, dilute relevance scores
- **Just right**: Chunks are self-contained units of meaning

**Real example**:

```
Original document:
"Authentication in kaizen uses JWT tokens. To configure authentication,
set the JWT_SECRET environment variable. The token expires after 24 hours
by default. You can customize this in config.py. For production, always
use HTTPS to protect tokens in transit."

Chunk too small (50 chars):
- "Authentication in kaizen uses JWT tokens. To conf"
- "igure authentication, set the JWT_SECRET environ"
→ Query "How to configure auth?" might not match!

Chunk too large (entire doc):
- Returns full doc even for specific questions
→ LLM must parse through irrelevant info

Chunk just right (~200 chars, semantic):
- "Authentication in kaizen uses JWT tokens. To configure authentication, set the JWT_SECRET environment variable."
- "The token expires after 24 hours by default. You can customize this in config.py."
- "For production, always use HTTPS to protect tokens in transit."
→ Each chunk answers a specific question type!
```

### Chunking Strategies

Think of chunking like cutting a pizza. Fixed-size chunking is using a grid cutter—neat and uniform, but you might slice through the middle of a pepperoni. Semantic chunking is like cutting along the natural boundaries between toppings—the slices might be different sizes, but each one contains complete, meaningful pieces.

#### 1. Fixed-Size Chunking (Simplest)

```python
def fixed_chunk(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into fixed-size chunks with overlap."""
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap  # Overlap for continuity

    return chunks
```

**Pros**: Simple, predictable token counts
**Cons**: Breaks mid-sentence, loses semantic coherence
**Use when**: Quick prototyping, uniform documents

#### 2. Sentence-Based Chunking

```python
import nltk

def sentence_chunk(text: str, sentences_per_chunk: int = 5) -> list[str]:
    """Chunk by sentence boundaries."""
    sentences = nltk.sent_tokenize(text)
    chunks = []

    for i in range(0, len(sentences), sentences_per_chunk):
        chunk = " ".join(sentences[i:i + sentences_per_chunk])
        chunks.append(chunk)

    return chunks
```

**Pros**: Respects sentence boundaries
**Cons**: Variable chunk sizes, may still break concepts
**Use when**: Prose documents, articles

#### 3. Semantic Chunking (Best for Most Cases)

```python
def semantic_chunk(text: str, max_chunk_size: int = 500) -> list[str]:
    """Chunk by semantic units (paragraphs, sections)."""
    # Split by paragraph
    paragraphs = text.split("\n\n")

    chunks = []
    current_chunk = ""

    for para in paragraphs:
        if len(current_chunk) + len(para) < max_chunk_size:
            current_chunk += para + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = para + "\n\n"

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks
```

**Pros**: Preserves semantic units, natural boundaries
**Cons**: Variable sizes, requires clean formatting
**Use when**: Documentation, structured content

#### 4. Recursive Chunking (LangChain's Approach)

```python
def recursive_chunk(text: str, chunk_size: int = 500, separators: list[str] = None) -> list[str]:
    """Recursively split using hierarchy of separators."""
    if separators is None:
        separators = ["\n\n", "\n", ". ", " ", ""]

    separator = separators[0]
    remaining_separators = separators[1:]

    splits = text.split(separator)
    chunks = []
    current_chunk = ""

    for split in splits:
        if len(current_chunk) + len(split) < chunk_size:
            current_chunk += split + separator
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())

            # If split itself is too large, recurse with finer separator
            if len(split) > chunk_size and remaining_separators:
                sub_chunks = recursive_chunk(split, chunk_size, remaining_separators)
                chunks.extend(sub_chunks)
            else:
                current_chunk = split + separator

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks
```

**Pros**: Best of all worlds, handles varied content
**Cons**: More complex, slower
**Use when**: Mixed content, code + prose

---

## Did You Know? The Chunk Size Discovery

In **2023**, researchers at Anthropic ran extensive experiments on chunk size:

| Chunk Size | Retrieval Recall | Answer Quality | Best For |
|------------|------------------|----------------|----------|
| 100 tokens | 45% | Poor | N/A |
| 250 tokens | 72% | Good | Simple QA |
| **500 tokens** | **85%** | **Best** | **General use** |
| 1000 tokens | 78% | Good | Complex questions |
| 2000 tokens | 65% | OK | Long-form analysis |

**The sweet spot**: 400-600 tokens for most use cases!

**Why?** This is roughly **one paragraph** of information - enough context to be useful, small enough to be relevant.

**The surprise**: Bigger chunks don't always help! After ~600 tokens, retrieval quality actually decreases because irrelevant information dilutes the embedding.

---

##  Advanced RAG Techniques

### 1. Hybrid Search (BM25 + Vector)

Combine keyword search with semantic search:

```python
def hybrid_search(query: str, k: int = 5) -> list[dict]:
    """Combine BM25 and vector search."""
    # Keyword search (BM25)
    keyword_results = bm25_search(query, k=k*2)

    # Vector search
    vector_results = vector_search(query, k=k*2)

    # Reciprocal Rank Fusion (RRF)
    combined = reciprocal_rank_fusion(
        [keyword_results, vector_results],
        k=60  # RRF constant
    )

    return combined[:k]

def reciprocal_rank_fusion(result_lists: list[list], k: int = 60) -> list:
    """Combine multiple result lists using RRF."""
    scores = {}

    for results in result_lists:
        for rank, doc in enumerate(results):
            doc_id = doc["id"]
            if doc_id not in scores:
                scores[doc_id] = 0
            scores[doc_id] += 1 / (k + rank + 1)

    # Sort by combined score
    sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [doc_id for doc_id, score in sorted_docs]
```

**Why hybrid?**
- **Vector alone** misses exact keyword matches ("error code E1234")
- **BM25 alone** misses semantic similarity ("restart" vs "reboot")
- **Combined** catches both!

### 2. Query Expansion

Expand the query to improve recall:

```python
def expand_query(query: str, llm) -> list[str]:
    """Generate related queries for better retrieval."""
    prompt = f"""Generate 3 alternative phrasings of this question:

Original: {query}

Alternative phrasings (one per line):"""

    expansions = llm.generate(prompt).strip().split("\n")

    return [query] + expansions

# Example:
# Query: "How to fix authentication?"
# Expansions:
#   - "How to fix authentication?"
#   - "Troubleshooting auth issues"
#   - "Authentication not working solution"
#   - "Debug login problems"
```

### 3. Reranking

Use a cross-encoder to rerank retrieved results:

```python
from sentence_transformers import CrossEncoder

reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

def rerank(query: str, documents: list[dict], top_k: int = 5) -> list[dict]:
    """Rerank documents using cross-encoder."""
    # Create query-document pairs
    pairs = [[query, doc["text"]] for doc in documents]

    # Score with cross-encoder
    scores = reranker.predict(pairs)

    # Sort by score
    ranked = sorted(
        zip(documents, scores),
        key=lambda x: x[1],
        reverse=True
    )

    return [doc for doc, score in ranked[:top_k]]
```

**Why rerank?**
- **Bi-encoders** (embedding models) are fast but less accurate
- **Cross-encoders** see query AND document together, more accurate
- **Best practice**: Retrieve 20 with bi-encoder, rerank to top 5

### 4. Contextual Compression

Remove irrelevant parts from retrieved chunks:

```python
def compress_context(query: str, chunk: str, llm) -> str:
    """Extract only relevant parts of a chunk."""
    prompt = f"""Extract only the parts of this text that are relevant to the question.
If nothing is relevant, respond with "NOT_RELEVANT".

Question: {query}

Text: {chunk}

Relevant excerpt:"""

    compressed = llm.generate(prompt)

    if "NOT_RELEVANT" in compressed:
        return None

    return compressed
```

---

## Did You Know? Perplexity's Secret Sauce

**Perplexity AI** (valued at $9B in 2024) built their entire business on RAG. Their "secret sauce":

1. **Multi-source retrieval**: Searches web, academic papers, news simultaneously
2. **Source diversity**: Ensures answers cite multiple independent sources
3. **Recency bias**: Weights recent sources higher for current events
4. **Streaming citations**: Shows sources WHILE generating answer

**The insight**: Users trust AI more when they can verify sources. Perplexity's citation-first approach built trust that ChatGPT lacked.

**Revenue impact**: $20M ARR in 2024, growing 300% YoY - all from RAG!

---

## ️ Common RAG Pitfalls

### Pitfall 1: Ignoring Chunk Boundaries

```python
# BAD: Fixed chunking breaks mid-concept
chunks = split_every_n_chars(text, 500)
# "To configure authentication, you need to..." | "...set the JWT_SECRET variable"

# GOOD: Respect semantic boundaries
chunks = split_by_paragraphs(text, max_size=500)
# "To configure authentication, you need to set the JWT_SECRET variable."
```

### Pitfall 2: Not Handling "I Don't Know"

```python
# BAD: Forces answer even when context doesn't help
prompt = f"Answer this question: {query}\nContext: {context}"

# GOOD: Explicit instruction for unknown cases
prompt = f"""Answer the question based ONLY on the context below.
If the context doesn't contain enough information to answer, say:
"I don't have information about that in my knowledge base."

Context: {context}
Question: {query}
Answer:"""
```

### Pitfall 3: Stuffing Too Much Context

```python
# BAD: Include all 20 retrieved chunks
context = "\n".join([c["text"] for c in retrieve(query, k=20)])
# → Context too long, LLM gets confused, costs more

# GOOD: Quality over quantity
chunks = retrieve(query, k=20)
reranked = rerank(query, chunks, top_k=5)
context = "\n".join([c["text"] for c in reranked])
# → Only most relevant context
```

### Pitfall 4: Not Including Sources

```python
# BAD: Answer without attribution
answer = llm.generate(f"Answer: {query}\nContext: {context}")

# GOOD: Include sources in prompt
context_with_sources = "\n".join([
    f"[{i+1}] {c['source']}: {c['text']}"
    for i, c in enumerate(chunks)
])

prompt = f"""Answer the question and cite sources using [1], [2], etc.

Context:
{context_with_sources}

Question: {query}
Answer (with citations):"""
```

### Pitfall 5: Stale Index

```python
# BAD: Index once, never update
index_documents(docs)  # Done in 2023
# → 2024 queries get outdated answers!

# GOOD: Incremental updates
def update_index(new_docs, modified_docs, deleted_ids):
    """Keep index fresh."""
    # Add new documents
    for doc in new_docs:
        add_to_index(doc)

    # Update modified documents
    for doc in modified_docs:
        delete_from_index(doc.id)
        add_to_index(doc)

    # Remove deleted documents
    for doc_id in deleted_ids:
        delete_from_index(doc_id)

# Run nightly or on document changes
```

---

## RAG Evaluation Metrics

### Retrieval Metrics

#### Recall@K
"Of the relevant documents, how many did we retrieve?"

```python
def recall_at_k(retrieved_ids: list, relevant_ids: list, k: int) -> float:
    """Calculate recall at k."""
    retrieved_k = set(retrieved_ids[:k])
    relevant = set(relevant_ids)

    return len(retrieved_k & relevant) / len(relevant)

# Example:
# Relevant docs: [1, 2, 3]
# Retrieved top-5: [1, 4, 2, 5, 6]
# Recall@5 = 2/3 = 0.67
```

#### Mean Reciprocal Rank (MRR)
"How high is the first relevant document ranked?"

```python
def mrr(retrieved_ids: list, relevant_ids: list) -> float:
    """Calculate mean reciprocal rank."""
    relevant = set(relevant_ids)

    for i, doc_id in enumerate(retrieved_ids):
        if doc_id in relevant:
            return 1 / (i + 1)

    return 0

# Example:
# Relevant: [1, 2, 3]
# Retrieved: [4, 2, 1, 3, 5]
# First relevant at position 2 → MRR = 1/2 = 0.5
```

### Answer Quality Metrics

#### Faithfulness
"Is the answer supported by the retrieved context?"

```python
def check_faithfulness(answer: str, context: str, llm) -> float:
    """Check if answer is faithful to context."""
    prompt = f"""Rate how well the answer is supported by the context.
Score from 0-1 where:
- 1.0 = Fully supported, no hallucination
- 0.5 = Partially supported
- 0.0 = Not supported / hallucinated

Context: {context}
Answer: {answer}

Score (just the number):"""

    score = float(llm.generate(prompt).strip())
    return score
```

#### Relevance
"Does the answer address the question?"

```python
def check_relevance(query: str, answer: str, llm) -> float:
    """Check if answer is relevant to question."""
    prompt = f"""Rate how well the answer addresses the question.
Score from 0-1 where:
- 1.0 = Directly answers the question
- 0.5 = Partially answers
- 0.0 = Doesn't answer

Question: {query}
Answer: {answer}

Score (just the number):"""

    score = float(llm.generate(prompt).strip())
    return score
```

### The RAGAS Framework

**RAGAS** (Retrieval Augmented Generation Assessment) is the standard evaluation framework:

```python
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision

# Evaluate your RAG
results = evaluate(
    dataset,
    metrics=[faithfulness, answer_relevancy, context_precision]
)

print(f"Faithfulness: {results['faithfulness']:.2f}")
print(f"Answer Relevancy: {results['answer_relevancy']:.2f}")
print(f"Context Precision: {results['context_precision']:.2f}")
```

---

## Real-World Applications

### Application 1: Kaizen Documentation Assistant

```python
# Kaizen RAG Configuration
kaizen_rag = RAGPipeline(
    knowledge_sources=[
        "docs/*.md",           # Documentation
        "src/**/*.py",         # Code (with docstrings)
        "issues/*.json",       # GitHub issues
        "runbooks/*.md"        # Operations runbooks
    ],
    chunk_strategy="recursive",
    chunk_size=500,
    embedding_model="all-MiniLM-L6-v2",
    vector_db="qdrant",
    llm="claude-4.6-sonnet",
    reranker="cross-encoder/ms-marco"
)

# Example queries:
# "How do I deploy to production?"
# "What's the fix for error E1234?"
# "Show me the authentication flow"
```

### Application 2: Vibe Course Assistant

```python
# Vibe RAG for student Q&A
vibe_rag = RAGPipeline(
    knowledge_sources=[
        "courses/**/*.md",     # Course content
        "videos/*.json",       # Video transcripts
        "qa/*.json",           # Previous Q&A
        "assignments/*.md"     # Assignment specs
    ],
    chunk_strategy="semantic",
    chunk_size=400,
    # Smaller chunks for focused answers
    special_handling={
        "code_blocks": "keep_intact",
        "equations": "keep_intact"
    }
)

# Example queries:
# "Explain the difference between RAG and fine-tuning"
# "What's due next week?"
# "How do I solve problem 3?"
```

### Application 3: Contrarian Financial Research

```python
# Contrarian RAG for financial analysis
contrarian_rag = RAGPipeline(
    knowledge_sources=[
        "sec_filings/*.pdf",   # 10-K, 10-Q filings
        "earnings/*.json",     # Earnings call transcripts
        "news/*.json",         # Financial news
        "analysis/*.md"        # Your analysis notes
    ],
    chunk_strategy="semantic",
    chunk_size=600,
    # Larger chunks for financial context
    metadata_filters=[
        "company",
        "date",
        "document_type"
    ],
    freshness_weight=0.3  # Prefer recent documents
)

# Example queries:
# "What did AAPL management say about AI in last earnings?"
# "Compare MSFT and GOOGL R&D spending"
# "What are the risk factors for TSLA?"
```

---

## Did You Know? The 10x Developer's RAG Setup

A senior engineer at Stripe shared their personal RAG setup (2024):

```
Personal Knowledge Base RAG:
├── Work
│   ├── Codebase (indexed daily)
│   ├── Confluence docs
│   ├── Slack threads (saved)
│   └── Meeting notes
├── Learning
│   ├── Papers I've read (PDFs)
│   ├── Course notes
│   └── Book highlights
└── Personal
    ├── Journal entries
    └── Project ideas

Daily usage:
- "What was the decision on the auth refactor?"
- "Find my notes on transformer attention"
- "What did Sarah say about the deadline?"
```

**Result**: They reported **2 hours saved daily** from not searching through old messages and documents.

**The insight**: RAG isn't just for products - it's a personal productivity superpower!

---

## Further Reading

### Papers
- **"Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks"** (Lewis et al., 2020) - The original RAG paper
- **"REALM: Retrieval-Augmented Language Model Pre-Training"** (Guu et al., 2020) - RAG during training
- **"Self-RAG"** (Asai et al., 2023) - LLM decides when to retrieve

### Tools & Frameworks
- **LangChain**: Popular RAG framework
- **LlamaIndex**: Data framework for LLM applications
- **Haystack**: End-to-end NLP framework with RAG
- **RAGAS**: RAG evaluation framework

### Tutorials
- [LangChain RAG Tutorial](https://python.langchain.com/docs/use_cases/question_answering/)
- [LlamaIndex Getting Started](https://docs.llamaindex.ai/en/stable/)
- [Pinecone RAG Guide](https://www.pinecone.io/learn/retrieval-augmented-generation/)

---

## The Evolution of RAG: A Historical Perspective

Understanding how RAG emerged helps you appreciate why it works and where it's heading.

### The Knowledge Problem (Pre-2020)

Before RAG, there were two approaches to giving language models knowledge:

**Approach 1: Bigger Models, More Data**. The intuition was simple: train on more data and the model will "know" more. GPT-2 (2019) was trained on 40GB of text. GPT-3 (2020) scaled to 45TB. But this created problems: training costs scaled exponentially, knowledge was frozen at training time, and models still hallucinated confidently about topics they hadn't seen.

**Approach 2: Fine-tuning**. Take a pre-trained model and fine-tune it on your domain data. This worked but required ML expertise, compute resources, and retraining whenever your data changed. A law firm couldn't just "plug in" their case database.

Both approaches tried to put knowledge *inside* the model. RAG flipped the paradigm: keep knowledge *outside* the model and teach it to look things up.

### The RAG Paper (2020)

In May 2020, researchers at Facebook AI published "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks." The paper introduced a surprisingly simple idea: combine a retrieval system with a language model.

The key insight from Lewis et al.: language models are excellent at *reasoning* and *generating* text but terrible at *remembering* facts. Retrieval systems (like search engines) are excellent at *finding* relevant information but terrible at *understanding* or *explaining* it. RAG combines the best of both worlds.

> **Did You Know?** The original RAG paper showed that a retrieval-augmented model with 1 billion parameters outperformed a pure language model with 11 billion parameters on knowledge-intensive tasks. The smaller model with external knowledge beat the larger model trying to remember everything internally—a result that shaped the entire direction of enterprise AI.

### From Research to Production (2021-2023)

The RAG concept spread rapidly through industry. The pattern was irresistible: instead of expensive fine-tuning or hoping the model "knew" your domain, you could simply retrieve relevant documents and inject them into the prompt.

Key milestones:
- **2021**: Pinecone, Weaviate, and other vector databases gained traction as the "memory" for RAG systems
- **2022**: LangChain emerged, making RAG pipelines easy to build
- **2023**: Every major cloud provider launched RAG-as-a-service offerings (Amazon Kendra + Bedrock, Azure AI Search + OpenAI, Google Vertex AI Search)

By 2024, RAG had become the default architecture for enterprise AI applications. If you're building an AI system that needs to answer questions about specific data—company documents, product catalogs, legal cases, medical records—you're building a RAG system.

### The Future of RAG (2025 and Beyond)

Several trends are shaping RAG's evolution:

**Multi-modal RAG**: Systems now retrieve images, tables, and diagrams alongside text. A question about "the architecture diagram from last quarter's review" can return the actual image, which vision-language models can then interpret.

**Self-RAG and Adaptive Retrieval**: Instead of always retrieving before generating, models learn when retrieval would help. Simple questions don't trigger retrieval; complex or factual questions do. This reduces latency and cost for queries that don't need external knowledge.

**Graph RAG**: Combining knowledge graphs with vector retrieval. Entities and relationships are stored in graphs while text chunks are stored in vectors. A query like "who reports to the CEO" uses graph traversal; a query like "what are our security policies" uses vector search.

**Agentic RAG**: RAG systems that can take actions—not just retrieve and generate, but also search multiple sources, synthesize findings, and iterate until they find a satisfactory answer. The boundary between RAG and AI agents is blurring.

> **Did You Know?** Microsoft's Copilot for Microsoft 365 uses a sophisticated RAG system that retrieves from your emails, documents, calendar, and Teams messages simultaneously. When you ask "What did Sarah say about the project deadline?", it searches across all these sources, ranks results by relevance and recency, and synthesizes a coherent answer—all in under two seconds.

---

## Production War Stories: RAG Failures and Lessons

### The Healthcare Chatbot That Retrieved the Wrong Patient

**Boston. September 2023.** A hospital deployed a RAG-powered assistant to help nurses find patient information. The system worked beautifully in testing—until it didn't.

A nurse asked: "What medications is patient in room 302 taking?" The system retrieved records and confidently listed medications. The problem: it had retrieved records for a *different* patient with a similar name who had been in room 302 three months earlier.

**Root cause**: The metadata filtering was too loose. The system prioritized semantic similarity over exact matches for critical identifiers like room numbers and patient IDs.

**The fix**: Implemented strict metadata filtering for identifiable information. Patient ID must *exactly* match before semantic search runs. Room numbers are only valid for the current day. The system now asks clarifying questions when identifiers are ambiguous.

**Lesson**: In high-stakes domains, semantic similarity isn't enough. Critical identifiers need exact matching, not fuzzy retrieval.

### The Legal Research Tool That Missed Superseding Cases

**New York. January 2024.** A law firm built a RAG system for case research. Associates loved it—queries like "precedent for software patent claims" returned relevant cases with helpful summaries.

Then an associate cited a case from the system in a brief. The opposing counsel pointed out the case had been overruled in 2019. The RAG system had retrieved the original case but missed the superseding decision.

**Root cause**: The chunking strategy broke cases into isolated passages. When the system retrieved chunks about the original ruling, it had no way to know those chunks were no longer good law because the "overruled" information was in different chunks that weren't retrieved.

**The fix**: Implemented "citation graph awareness." Every case chunk now includes metadata about its current status (good law, distinguished, overruled). The system also performs a follow-up check: after retrieving cases, it queries specifically for superseding decisions.

**Lesson**: Domain knowledge shapes RAG architecture. Legal research requires understanding that facts have temporal validity. Medical research requires understanding that studies can be retracted. Financial research requires understanding that old numbers may be restated.

### The E-commerce Chatbot That Couldn't Find Anything

**Seattle. March 2024.** An e-commerce company launched a RAG-powered shopping assistant. Initial results were disappointing: users complained it "never finds what I'm looking for."

Investigation revealed the problem: the embeddings were trained on general text, but customer queries used colloquial product terms. A customer asking for "comfy pants for working from home" didn't match the formal product descriptions containing "relaxed-fit trousers" or "loungewear bottoms."

**Root cause**: Semantic similarity between user language and product catalog language was weak. The embeddings weren't specialized for retail vocabulary.

**The fix**: Three changes: (1) Created a query expansion system that added synonyms and related terms to user queries, (2) Fine-tuned embeddings on pairs of user queries and clicked products, (3) Added keyword search as a fallback when semantic search returned low-confidence results.

**Lesson**: Embedding models aren't universal translators. If your users speak differently than your documents, you need query expansion, domain-specific embeddings, or hybrid search.

---

## Common Mistakes in RAG Systems

### Mistake 1: Chunking Too Large or Too Small

```python
# WRONG - Chunks too large
chunk_size = 2000  # Retrieves whole documents, loses specificity
# Each chunk contains too many topics, diluting relevance

# WRONG - Chunks too small
chunk_size = 100  # Retrieves fragments without context
# "The company reported Q3 revenue of" - cut off!

# RIGHT - Balanced with overlap
chunk_size = 500
chunk_overlap = 100  # Overlap preserves context at boundaries
# "The company reported Q3 revenue of $42B, up 15% YoY."
```

**Consequence**: Large chunks waste context window space on irrelevant text. Small chunks lose the context needed for understanding. The sweet spot is usually 400-600 tokens with 50-100 token overlap.

### Mistake 2: Not Handling "No Good Results" Cases

```python
# WRONG - Always returns something
def retrieve_and_answer(query):
    results = vector_db.search(query, k=5)
    context = "\n".join([r.text for r in results])
    return llm.generate(f"Based on: {context}\nAnswer: {query}")
    # Even if results are terrible, we pretend they're relevant

# RIGHT - Check retrieval quality
def retrieve_and_answer(query):
    results = vector_db.search(query, k=5)

    # Check if results are actually relevant
    if results[0].score < 0.7:  # Low confidence threshold
        return "I don't have information about that in my knowledge base."

    # Filter to only high-quality results
    good_results = [r for r in results if r.score > 0.6]
    context = "\n".join([r.text for r in good_results])

    return llm.generate(
        f"Based on: {context}\nAnswer: {query}\n"
        f"If the context doesn't contain the answer, say so."
    )
```

**Consequence**: Without quality thresholds, RAG systems hallucinate using irrelevant context. Users learn they can't trust the responses.

### Mistake 3: Ignoring Update Frequency

```python
# WRONG - Index once and forget
# Index created: January 2024
# Query (March 2024): "What is our current pricing?"
# Answer: Returns January pricing (now outdated!)

# RIGHT - Scheduled re-indexing with freshness metadata
index_config = {
    "reindex_schedule": "daily",
    "source_types": {
        "pricing": {"reindex": "hourly", "priority": "high"},
        "policies": {"reindex": "weekly"},
        "blog_posts": {"reindex": "on_publish"}
    },
    "freshness_boost": True  # Prefer recent documents
}
```

**Consequence**: Stale indexes return outdated information, eroding trust. For dynamic content (pricing, inventory, policies), automated re-indexing is essential.

### Mistake 4: Stuffing Too Much Context

```python
# WRONG - Retrieve everything that might be relevant
results = vector_db.search(query, k=20)  # Too many!
context = "\n".join([r.text for r in results])
# Context is now 8000 tokens of mixed relevance

# RIGHT - Quality over quantity with reranking
results = vector_db.search(query, k=20)  # Cast wide net
reranked = reranker.rerank(query, results)  # Score each result
top_results = reranked[:5]  # Keep only the best
context = "\n".join([r.text for r in top_results])
# Context is 2000 tokens of highly relevant information
```

**Consequence**: More context isn't always better. Irrelevant context confuses the model and wastes tokens that could be used for better answers.

---

## Interview Prep: RAG Systems

### Common Questions and Strong Answers

**Q: "Walk me through how you would design a RAG system for a customer support chatbot."**

**Strong Answer**: "I'd start by understanding the data landscape: what documents exist, how often they change, and what questions users typically ask. For customer support, I'd expect FAQs, product documentation, troubleshooting guides, and maybe past support tickets.

For chunking, I'd use semantic chunking at around 500 tokens with overlap, since support questions need enough context to be useful but shouldn't retrieve entire manuals. I'd add metadata like product category, document type, and last-updated date to enable filtering.

The retrieval layer would be hybrid search—both semantic (for conceptual questions like 'how do I connect my device') and keyword (for specific terms like error codes). I'd implement reranking with a cross-encoder to ensure the top results are truly relevant.

For generation, I'd use a system prompt that instructs the model to cite sources, admit when it doesn't know, and suggest escalation to human support for complex issues. I'd also implement confidence thresholds—if retrieval scores are low, the system should ask clarifying questions rather than guess.

Finally, I'd build an evaluation loop using RAGAS or similar to measure faithfulness and relevance, with human review of a sample of responses weekly."

**Q: "How do you handle the 'semantic gap' where users ask questions using different terminology than your documents?"**

**Strong Answer**: "The semantic gap is one of RAG's trickiest challenges. I use a multi-pronged approach.

First, query expansion: before retrieval, I use an LLM to generate synonyms and related terms. A user asking about 'broken button' gets expanded to include 'non-responsive control,' 'UI element not working,' etc.

Second, hybrid search: I combine semantic search with keyword search. Sometimes the exact term match is more important than conceptual similarity.

Third, if I have query logs and click data, I fine-tune embeddings on actual user behavior. Pairs of (query, clicked_document) teach the embedding model what users actually mean.

Fourth, I maintain a domain-specific glossary that maps colloquial terms to formal terminology. This is especially important in technical domains where users and documents use different vocabularies.

Finally, I instrument everything: log queries with low retrieval confidence, review them weekly, and add successful mappings back to the system. The semantic gap narrows over time with active maintenance."

**Q: "What are the failure modes of RAG systems and how do you mitigate them?"**

**Strong Answer**: "There are four main failure modes I plan for.

First, retrieval failure: the relevant document exists but isn't retrieved. Mitigation includes hybrid search, query expansion, ensuring chunk sizes aren't so large that specific information is diluted, and monitoring retrieval recall metrics.

Second, context poisoning: irrelevant or incorrect information is retrieved and contaminates the response. Mitigation includes confidence thresholds, reranking, and prompting the model to be skeptical of context that doesn't directly answer the question.

Third, context window overflow: too much context is retrieved, pushing out the actual question or exceeding model limits. Mitigation includes aggressive reranking to keep only top results, and for long conversations, summarizing prior context rather than including everything.

Fourth, staleness: the index contains outdated information. Mitigation includes timestamp metadata, freshness boosting, scheduled re-indexing, and for critical documents, real-time indexing on change.

For all these, I implement monitoring: track retrieval scores over time, sample and review responses, and set up alerts when confidence drops or user satisfaction declines."

---

## The Economics of RAG

### Cost Structure

RAG systems have three main cost components:

| Component | Cost Driver | Typical Range |
|-----------|-------------|---------------|
| Embedding | API calls or compute for generating embeddings | $0.0001-0.001 per 1K tokens |
| Storage | Vector database hosting | $20-500/month depending on scale |
| Inference | LLM API calls for generation | $0.001-0.06 per 1K tokens |

### Cost Optimization Strategies

**1. Caching Embeddings**: Don't re-embed documents that haven't changed. A document library of 10,000 documents costs ~$1 to embed initially. Re-embedding daily would cost $365/year unnecessarily.

**2. Query Caching**: Cache responses for common queries. In customer support, 20% of queries often account for 80% of volume. Caching these eliminates both retrieval and generation costs.

**3. Model Selection**: Use smaller models for simpler tasks. Not every query needs gpt-5. A routing layer can direct simple factual questions to cheaper models while reserving expensive models for complex reasoning.

**4. Batch Processing**: For non-real-time use cases, batch queries and use discounted batch API pricing. Many providers offer 50% discounts for async batch processing.

### ROI Calculation

A typical enterprise RAG deployment:

```
Monthly Costs:
- Vector database: $100
- Embeddings (1M queries): $100
- LLM inference (1M queries): $500
- Engineering time: $5,000
Total: ~$5,700/month

Monthly Value:
- Support tickets deflected (10,000 × $15 each): $150,000
- Engineer time saved (200 hours × $100/hour): $20,000
- Faster customer resolutions: Incalculable goodwill
Total value: $170,000+/month

ROI: ~30x
```

This is why RAG adoption is so rapid—the economics are overwhelmingly favorable for knowledge-intensive applications.

---

## Key Takeaways

1. **RAG solves the hallucination problem** by teaching LLMs to look things up rather than make things up. The model's role shifts from unreliable oracle to skilled synthesizer.

2. **Chunking is an art, not a science**. Start with 400-600 tokens with overlap, then tune based on your use case. Semantic chunking beats fixed-size for most applications.

3. **Hybrid search beats pure semantic search** in most production systems. Keywords matter for exact matches; semantics matter for conceptual similarity.

4. **Reranking is worth the latency**. A cross-encoder scoring 20 candidates to select 5 produces dramatically better results than taking the top 5 from vector search alone.

5. **Metadata filtering is your precision tool**. Semantic search casts a wide net; metadata filtering ensures you're fishing in the right pond.

6. **Handle "I don't know" gracefully**. When retrieval confidence is low, it's better to admit uncertainty than hallucinate with irrelevant context.

7. **Freshness requires active management**. Static indexes become liabilities. Build re-indexing into your pipeline from day one.

8. **Evaluation is non-negotiable**. Measure faithfulness (did it use the retrieved context?) and relevance (was the context appropriate for the question?). RAGAS provides a good starting framework.

9. **Domain expertise shapes architecture**. Legal RAG needs citation tracking. Medical RAG needs temporal validity. E-commerce RAG needs inventory awareness. Generic approaches fail.

10. **RAG economics favor adoption**. The cost of retrieval and generation is tiny compared to the value of accurate, domain-specific AI responses. A 30x ROI is typical for enterprise deployments.

---

## Module Summary

**What you learned**:
- RAG architecture: Retrieve → Augment → Generate
- Document chunking strategies and their trade-offs
- Advanced techniques: Hybrid search, reranking, query expansion
- Evaluation metrics: Recall@K, MRR, Faithfulness, Relevance
- Common pitfalls and how to avoid them
- Real-world applications for kaizen, vibe, contrarian

**Key formulas**:
```
RAG = Retrieval + Augmented Generation

Recall@K = |Retrieved ∩ Relevant| / |Relevant|

MRR = 1 / (rank of first relevant document)
```

**Best practices**:
1. **Chunk size**: 400-600 tokens for most use cases
2. **Retrieval**: Start with k=5-10, rerank if needed
3. **Context**: Quality over quantity - don't stuff the prompt
4. **Sources**: Always include citations
5. **Evaluation**: Measure faithfulness AND relevance
6. **Updates**: Keep your index fresh

---

## ️ Next Steps

**Next module**: Module 13: RAG vs Fine-tuning Trade-offs 

You'll learn:
- When to use RAG vs fine-tuning
- Parameter-efficient fine-tuning (LoRA, QLoRA)
- Combining RAG + fine-tuning
- Cost-benefit analysis

**This is another Heureka Moment** - understanding when each approach is appropriate!

---

** Neural Dojo - You built your first RAG system! **

---

_Last updated: 2025-11-24_
_Module 12: Building Your First RAG System_

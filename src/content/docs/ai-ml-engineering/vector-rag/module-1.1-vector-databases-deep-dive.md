---
title: "Vector Databases Deep Dive"
slug: ai-ml-engineering/vector-rag/module-1.1-vector-databases-deep-dive
sidebar:
  order: 402
---

# Vector Databases Deep Dive

> **AI/ML Engineering Track** | Complexity: `[COMPLEX]` | Time: 5-6 hours
>
> **Prerequisites**: Prior experience with embeddings, semantic search, Python, HTTP APIs, and basic database concepts.

---

## Learning Outcomes

By the end of this module, you will be able to:

| Outcome | Bloom Level | Evidence You Can Produce |
|---------|-------------|--------------------------|
| Compare exact, keyword, and vector search architectures and justify which one fits a RAG workload. | Analyze | A decision table that explains why SQL, BM25, pgvector, or a dedicated vector database is appropriate. |
| Design a vector collection schema that aligns embeddings, distance metrics, metadata, and deterministic IDs. | Create | A collection plan that prevents dimension mismatch, duplicate ingestion, and inefficient filtering. |
| Debug poor vector search results by checking embeddings, dimensions, distance metrics, filters, and score distributions. | Analyze | A repeatable troubleshooting checklist with commands or scripts that expose the failure mode. |
| Evaluate HNSW tuning trade-offs between recall, latency, memory, and ingestion speed for production workloads. | Evaluate | A tuning recommendation for a specific scenario, including which parameter changes and why. |
| Implement a small persistent vector search workflow with metadata filtering and verify it survives restart. | Apply | A working Qdrant lab with semantic search, filtered search, update, delete, and persistence checks. |

---

## Why This Module Matters

A platform engineer at a healthcare company is asked to make clinical guidelines searchable by meaning rather than by exact wording. Doctors type questions like
"safe anticoagulant options before surgery," but the source documents use phrasing such as "perioperative management of blood thinning medication." A keyword system misses
important material because the words do not line up, while a naive embedding demo works only on a small notebook-sized corpus and loses data whenever the process restarts.

The first prototype impresses leadership because it retrieves semantically related passages from a few thousand documents. Then the real requirements arrive: millions of chunks,
strict tenant isolation, daily document updates, audit-friendly persistence, low-latency search, and filters for specialty, publication year, and document status. The team discovers
that "semantic search" is not only an embedding problem. It is a storage, indexing, filtering, update, observability, and operations problem.

Vector databases exist because production AI systems need more than a pile of vectors in memory. They need to find approximate nearest neighbors quickly, keep metadata connected
to each vector, update indexes while traffic continues, shard data across machines, replicate data for availability, and expose predictable APIs that application teams can operate.
This module teaches the mechanism behind those capabilities so you can choose, tune, and debug vector storage deliberately instead of treating it as a black box.

---

## 1. From Exact Search to Semantic Search

The simplest way to understand vector databases is to start with what traditional databases are already excellent at. A relational database handles exact identity, structured joins,
transactional updates, and range filters with mature indexes. If the question is "show orders where `customer_id = 1029` and `created_at` is after last Monday," a vector database
is the wrong tool because the problem is not about meaning or similarity.

Keyword search adds a different capability: it finds documents that contain important terms, stems, synonyms, or weighted text fields. Search engines such as Elasticsearch and
OpenSearch use inverted indexes that map terms to documents, which makes them very fast when the query and the document share vocabulary. They work well for logs, product catalogs,
and documentation search where exact terminology matters and users often type the same words that authors used.

Vector search solves a different problem: the query and the answer may have similar meaning even when they share few words. An embedding model maps text, images, audio, or code
into a high-dimensional numeric vector. Similar items land near each other in that vector space, so search becomes "find the stored vectors closest to this query vector." The database
does not understand meaning like a person, but it can exploit the geometry learned by the embedding model.

| Search Style | Primary Index | Best Question Type | Failure Mode |
|--------------|---------------|--------------------|--------------|
| SQL exact/range search | B-tree, hash, GiST, or similar structured indexes | "Which rows match this known attribute or range?" | Misses semantic matches because it compares values, not meaning. |
| Keyword search | Inverted index with term statistics | "Which documents mention these terms or close lexical variants?" | Misses answers that use different vocabulary or paraphrase the concept. |
| Vector search | ANN index over embedding vectors | "Which items are closest in learned semantic space?" | Can return plausible but wrong neighbors when embeddings, chunks, or filters are poor. |
| Hybrid search | Keyword index plus vector index plus re-ranker | "Which results are semantically related and lexically grounded?" | Costs more to operate and requires careful score calibration. |

A production RAG system often uses all of these search styles at once. PostgreSQL may store users, permissions, billing records, and canonical document metadata. A keyword engine
may catch exact product names, error codes, and acronyms. A vector database retrieves semantically related chunks. A re-ranker may then rescore the top candidates before the LLM
sees them, because retrieval quality directly limits answer quality.

```text
                   User question
                        |
                        v
              +-------------------+
              |  Embedding model  |
              |  query -> vector  |
              +-------------------+
                        |
                        v
+-------------+   +-------------------+   +----------------------+
| SQL metadata|<--| Vector database   |-->| Top semantic chunks  |
| permissions |   | ANN + payloads    |   | ids, text, scores    |
+-------------+   +-------------------+   +----------------------+
                        |
                        v
              +-------------------+
              | Optional re-rank  |
              | lexical + semantic|
              +-------------------+
                        |
                        v
              +-------------------+
              | LLM answer with   |
              | retrieved context |
              +-------------------+
```

The diagram shows why a vector database complements traditional storage rather than replacing it. The vector database is responsible for similarity search and payload filtering,
while the system of record remains the source of truth for identities, permissions, transactions, and document lifecycle state. Treating the vector store as the only database is a
common source of operational trouble because ANN indexes are optimized for retrieval, not for every workload an application needs.

**Pause and predict:** If a user searches for "pods cannot talk across namespaces" and the indexed document says "NetworkPolicy denies cross-namespace traffic," which search style
is most likely to retrieve it without special synonym rules? Before reading further, decide whether exact SQL, keyword search, vector search, or hybrid search would be most robust
and write down the reason. The correct answer depends on whether "pods," "namespaces," and "NetworkPolicy" are shared terms, but vector search gives the system a chance to match
the paraphrased meaning even when the words differ.

A useful rule is to ask what must be preserved exactly and what may be compared approximately. Tenant IDs, access control, document status, and publication date should be exact
filters. The meaning of a question, title, paragraph, image, or code snippet can be approximate. Strong RAG architecture keeps those responsibilities separate, then combines them
at query time so approximate semantic retrieval never bypasses exact authorization or compliance rules.

### Why Regular Databases Struggle With Vectors

A vector for a text embedding may have hundreds or thousands of dimensions. Comparing one query vector to one stored vector requires a distance calculation across every dimension.
Comparing one query to millions of stored vectors by brute force becomes expensive because the database must repeat that calculation for every candidate before it can sort the top
neighbors. Traditional indexes are not designed to prune high-dimensional similarity search in the same way they prune a one-dimensional range query.

```python
from math import sqrt

def cosine_similarity(left: list[float], right: list[float]) -> float:
    """Return cosine similarity for two non-empty vectors of equal length."""
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = sqrt(sum(a * a for a in left))
    right_norm = sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        raise ValueError("Cosine similarity is undefined for a zero vector")
    return dot / (left_norm * right_norm)

def brute_force_search(query: list[float], vectors: dict[str, list[float]], limit: int = 3) -> list[tuple[str, float]]:
    scored = [(doc_id, cosine_similarity(query, vector)) for doc_id, vector in vectors.items()]
    return sorted(scored, key=lambda item: item[1], reverse=True)[:limit]

demo_vectors = {
    "linux-permissions": [0.10, 0.82, 0.12, 0.09],
    "kubernetes-networking": [0.80, 0.15, 0.72, 0.10],
    "rag-retrieval": [0.22, 0.19, 0.11, 0.93],
}

query_vector = [0.77, 0.18, 0.70, 0.13]
for document_id, score in brute_force_search(query_vector, demo_vectors):
    print(f"{document_id}: {score:.3f}")
```

This worked example is intentionally small so the mechanics are visible. The query vector is compared against every stored vector, each score is calculated, and the results are sorted.
That is acceptable for a classroom example and sometimes acceptable for a tiny internal tool. It does not survive when the corpus grows, when multiple users search concurrently, or
when each request has a strict latency budget.

A vector database changes the problem by adding a specialized approximate nearest neighbor index. Instead of checking every vector, it uses a graph, partitioning scheme, quantized
representation, or a combination of techniques to inspect a much smaller candidate set. Approximate search accepts a controlled risk of missing the mathematically perfect neighbor
in exchange for dramatically lower latency and memory-aware operation.

| Approach | Query Work | Typical Use | Main Trade-off |
|----------|------------|-------------|----------------|
| Brute force | Compare query with every vector | Tiny datasets, test harnesses, exact evaluation baselines | Perfect recall but slow growth as data increases. |
| HNSW | Navigate a layered nearest-neighbor graph | General-purpose production vector search | High recall and low latency, with extra memory for graph links. |
| IVF | Search selected coarse clusters | Very large datasets with clusterable vectors | Faster search but requires training and can miss neighbors across cluster boundaries. |
| Product quantization | Search compressed vector representations | Memory-constrained large-scale systems | Saves memory but may reduce precision depending on compression. |
| Hybrid retrieval | Combine vector and lexical candidates | Search systems with exact terms and semantic intent | Better quality but requires score merging and more moving parts. |

The important shift is not "vector databases are faster" in a vague sense. The important shift is that the database builds an access path for high-dimensional similarity, exposes
controls for the accuracy-latency trade-off, keeps payload metadata beside the vector, and supports update patterns that a static notebook index often ignores. Those capabilities are
what turn a semantic search demo into production infrastructure.

---

## 2. Worked Example: Designing the First Collection

Before choosing a vendor or tuning HNSW, a team must design the basic collection contract. A collection is the logical container for vectors of the same shape and purpose. Every point
inside a collection should use the same embedding model, the same vector dimension, a compatible distance metric, and a payload schema that supports the queries the application must
answer. Many retrieval bugs begin when this contract is implicit.

Imagine an internal documentation assistant for platform engineers. The assistant indexes pages about Kubernetes, Linux, CI/CD, and incident response. Users ask operational questions,
and the system retrieves the most relevant chunks for a RAG answer. The first design decision is not "which vector database is fashionable." The first decision is what a stored point
means and how the application can safely retrieve it later.

```text
Point in collection: platform_docs
+---------------------------------------------------------------+
| id: sha256(source_path + chunk_index + content_hash)           |
| vector: embedding(text_chunk)                                  |
| payload:                                                       |
|   text: "NetworkPolicy controls traffic between pods..."       |
|   source_path: "docs/k8s/networking/network-policy.md"         |
|   chunk_index: 8                                               |
|   product_area: "kubernetes"                                   |
|   document_status: "published"                                 |
|   audience: "intermediate"                                     |
|   updated_year: 2026                                           |
|   tenant_id: "internal-platform"                               |
+---------------------------------------------------------------+
```

The ID is deterministic because ingestion should be idempotent. If the same chunk is processed again, the pipeline should update the existing point rather than inserting a duplicate.
The payload contains both human-useful text and machine-useful filters. The vector is generated from the text chunk, but the filters protect the query from retrieving drafts, wrong
tenants, retired documents, or content outside the user's intended product area.

```python
import hashlib

def deterministic_chunk_id(source_path: str, chunk_index: int, content: str) -> str:
    stable_key = f"{source_path}:{chunk_index}:{hashlib.sha256(content.encode()).hexdigest()}"
    return hashlib.sha256(stable_key.encode()).hexdigest()[:32]

sample_text = "NetworkPolicy controls allowed traffic between selected pods."
print(deterministic_chunk_id("docs/k8s/network-policy.md", 8, sample_text))
```

This code is runnable with the standard library and demonstrates the design principle without requiring a vector database. The stable ID includes the source path, chunk index, and
content hash so identical ingestion runs do not multiply points. In a real pipeline, you would also decide how to handle chunk movement after document edits, because changing chunk
boundaries can create new IDs even when most text remains familiar.

**Stop and think:** Your ingestion job currently uses auto-generated IDs, and a scheduled sync runs every night. What will happen after a month if the job accidentally reprocesses
the same documents without deleting old points? Predict the effect on storage, search ranking, and user trust before looking at the common mistakes table later in this module.

A collection design should also state the embedding model and distance metric together. Cosine distance is common for normalized text embeddings because it compares direction rather
than magnitude. Dot product is useful when the model and retrieval setup are trained for it. Euclidean distance is appropriate for some vector spaces but should not be chosen simply
because it sounds familiar from geometry class. The embedding model documentation should drive the decision.

| Design Field | Good Choice | Why It Matters |
|--------------|-------------|----------------|
| Embedding model | One named model per collection, recorded in config and deployment metadata. | Mixed models can produce incompatible geometry even when dimensions happen to match. |
| Dimension | Enforced at collection creation, such as 384 for `all-MiniLM-L6-v2`. | A query vector with the wrong dimension fails or silently breaks retrieval quality. |
| Distance metric | Matched to the model's training and normalization assumptions. | Wrong metrics can rank irrelevant neighbors above relevant ones. |
| Point ID | Deterministic from stable source information and content identity. | Re-ingestion updates existing points instead of creating duplicates. |
| Payload schema | Fields that represent authorization, lifecycle, domain, and retrieval constraints. | Filters can narrow the candidate set before or during search. |
| Chunk text | Stored with enough context to support answer generation and debugging. | Scores alone are hard to inspect when retrieval quality is poor. |

The simplest safe collection contract is often better than a clever one. Start with one collection per embedding purpose, not one collection per user or category. Use metadata filters
for tenant, category, status, and time range unless isolation requirements demand separate collections. Collections have operational overhead, so multiplying them prematurely makes
backup, monitoring, and migration harder.

### Metadata Filtering as a Retrieval Contract

Metadata filtering is the feature that makes vector search usable in real applications. Semantic similarity alone can retrieve a technically related result that the user is not
allowed to see, an outdated draft, a document from the wrong tenant, or a result outside the requested date range. Filters turn retrieval from "near this meaning" into "near this
meaning and valid for this user, this corpus, and this business context."

```python
from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue, Range

client = QdrantClient(url="http://127.0.0.1:6333")

query_filter = Filter(
    must=[
        FieldCondition(key="tenant_id", match=MatchValue(value="internal-platform")),
        FieldCondition(key="document_status", match=MatchValue(value="published")),
        FieldCondition(key="updated_year", range=Range(gte=2024)),
    ]
)

print(query_filter)
```

This snippet constructs the kind of filter a production RAG service should apply before it trusts semantic results. It does not call a live collection, so it can run as a local sanity
check after installing `qdrant-client`. The important point is that metadata constraints belong inside the database query where the engine can use indexes and avoid returning invalid
candidates to application code.

Filtering after retrieval is usually the wrong default. If the application retrieves one hundred neighbors and then removes all documents the user cannot access, it may end up with
too few results or with lower-quality leftovers. Worse, a careless logging or tracing path might expose forbidden payloads before the filter removes them. Push hard constraints into
the vector database query, then apply additional application checks as defense in depth.

```text
Unsafe pattern:
  Query vector store broadly
        |
        v
  Receive top results across tenants and statuses
        |
        v
  Filter in application code after payloads already returned

Safer pattern:
  Build authorization and lifecycle filter
        |
        v
  Query vector store with vector + metadata filter
        |
        v
  Receive only eligible candidates for ranking and generation
```

The same principle applies to product search, legal discovery, incident runbooks, and healthcare retrieval. Similarity tells you what is close in embedding space. Metadata tells you
what is eligible. Production retrieval needs both because a result can be semantically excellent and still be operationally invalid.

---

## 3. How HNSW Makes Search Fast

Hierarchical Navigable Small World indexing, usually shortened to HNSW, is the default mental model for many modern vector databases. It stores vectors in a graph where each point
connects to nearby points, then adds upper layers with longer-range connections. Search starts from a sparse upper layer, moves greedily toward a closer region, drops to lower layers,
and refines the candidate set near the dense base graph.

```text
Layer 2:          [A] ------------------------------ [M]
                   |                                  |
                   v                                  v

Layer 1:          [A] -------- [F] -------- [M] ----- [T]
                   |            |            |         |
                   v            v            v         v

Layer 0: [A]-[B]-[C]-[D]-[E]-[F]-[G]-[H]-[J]-[M]-[P]-[T]
          \       /       \       /       \       /       \
           -------         -------         -------         ---
```

The structure is similar to navigating a city with highways, arterial roads, and local streets. The top layer gets you near the right neighborhood quickly. The middle layer improves
the route. The bottom layer does the detailed local search. The database does not need to compare the query with every vector because the graph gives it a path toward promising
neighbors.

The "small world" part means that useful paths are short even when the graph contains many nodes. Social networks have a similar property: two people may be connected by only a few
intermediate relationships despite the network being huge. HNSW applies that idea to vector neighborhoods so search can move through a manageable number of candidates rather than
scan the entire corpus.

| HNSW Concept | Practical Meaning | Operational Trade-off |
|--------------|-------------------|-----------------------|
| `M` or max connections | How many neighbors each graph node tries to keep. | Higher values improve recall but increase memory and build cost. |
| `ef_construct` | How broadly the index searches while adding new vectors. | Higher values build a better graph but slow ingestion. |
| `ef_search` or search width | How many candidates the query explores at search time. | Higher values improve recall but increase latency. |
| Graph layers | Sparse upper layers guide search before dense lower layers refine it. | More structure improves navigation but consumes memory. |
| Approximate recall | The index may miss a true nearest neighbor. | Most RAG systems accept this when latency and scale improve dramatically. |

The key engineering skill is not memorizing parameter names. The key skill is recognizing which constraint is binding. If user-facing latency is high and recall is already acceptable,
lowering search width may help. If evaluation shows the system misses relevant chunks, raising search width or rebuilding with stronger construction settings may help. If memory is
the bottleneck, compression, fewer graph connections, smaller embeddings, or sharding may matter more than query tuning.

**Pause and predict:** A team doubles `ef_search` because users complain that answers miss relevant documents. What should happen to recall, query latency, and CPU usage? Write your
prediction before continuing. In most HNSW systems, recall should improve or plateau, latency should increase, and CPU work per query should rise because the index explores more
candidates before returning the top results.

A good evaluation harness measures these trade-offs with your data rather than relying on vendor screenshots. Create a small labeled set of queries, known relevant documents, and
expected filters. Run the same queries at different settings. Record recall at a fixed top-k, p50 latency, p95 latency, p99 latency, memory usage, and ingestion rate. Only then can
you decide whether a tuning change is an improvement for your workload.

```python
from statistics import mean

def recall_at_k(expected_ids: set[str], returned_ids: list[str], k: int) -> float:
    if not expected_ids:
        raise ValueError("expected_ids must not be empty")
    top_k = set(returned_ids[:k])
    return len(expected_ids & top_k) / len(expected_ids)

examples = [
    ({"doc-a", "doc-c"}, ["doc-a", "doc-b", "doc-c"], 3),
    ({"doc-x"}, ["doc-y", "doc-z", "doc-x"], 2),
    ({"doc-k", "doc-m"}, ["doc-k", "doc-n", "doc-p"], 3),
]

scores = [recall_at_k(expected, returned, k) for expected, returned, k in examples]
print(f"mean recall: {mean(scores):.2f}")
```

This small evaluation function is useful because it forces precision into the conversation. "Search feels better" is not a sufficient production signal. If a higher `ef_search`
setting improves recall from 0.72 to 0.86 while raising p95 latency from 35 ms to 51 ms, the team can make an explicit product decision. If it improves recall by only a tiny amount
while doubling latency, the bottleneck may be chunking, embeddings, or filters rather than HNSW.

### Brute Force Still Has a Role

Approximate indexes are not always the first tool. Brute force search is useful for tiny datasets, unit tests, and offline evaluation because it gives an exact baseline. When an ANN
index returns surprising results, comparing against brute force on a sampled subset can reveal whether the issue is approximate search, embedding quality, filtering, or application
logic. Senior practitioners keep exact search around as a diagnostic tool even when production uses ANN.

| Dataset Size and Need | Reasonable Starting Point | Why |
|-----------------------|---------------------------|-----|
| Fewer than ten thousand vectors, low traffic | Brute force, Chroma, FAISS, or pgvector | Simplicity matters more than distributed indexing. |
| Tens of thousands to a few million vectors, production RAG | Qdrant, Weaviate, Pinecone, Milvus, or pgvector with HNSW | Persistence, filtering, and operational APIs become important. |
| Many millions with strict latency | Dedicated vector database with tuned HNSW and payload indexes | Specialized storage and search controls become worth the complexity. |
| Extremely large or memory-constrained corpus | Sharding, compression, tiered storage, and hybrid retrieval | Architecture choices dominate individual query syntax. |

Do not over-engineer the first version, but do not ignore the migration path. A small prototype can use local storage, but it should still use deterministic IDs, recorded model names,
consistent chunking rules, and a query interface that can move to a production backend. These habits reduce the cost of graduating from a demo to a service.

---

## 4. Choosing a Vector Database Architecture

Vector database selection is a design decision, not a popularity contest. The right choice depends on data sensitivity, operational skill, query volume, latency expectations, hybrid
search needs, update frequency, budget model, and whether the platform team already runs stateful services well. The same company may use Chroma for local experiments, pgvector for a
small product feature, Qdrant for self-hosted RAG, and Pinecone for a managed service where speed of delivery outweighs infrastructure control.

| Option | Strong Fit | Watch Carefully |
|--------|------------|-----------------|
| Qdrant | Self-hosted production RAG, rich payload filtering, Rust-based service, Docker-friendly operations. | You own backups, upgrades, capacity planning, and cluster operations. |
| Pinecone | Managed vector search when the team wants minimal infrastructure work. | Pricing, quotas, vendor lock-in, data residency, and cold-start behavior for some capacity models. |
| Weaviate | Hybrid semantic and keyword search with schema-rich objects and managed or self-hosted options. | More concepts to learn, more resource planning, and GraphQL/API design decisions. |
| Chroma | Local development, teaching, small prototypes, and quick LangChain-style experiments. | Validate production scale, durability, concurrency, and filtering before relying on it heavily. |
| pgvector | Keeping smaller vector workloads beside relational data in PostgreSQL. | PostgreSQL remains responsible for operational load, memory, indexes, and query planning. |
| FAISS | High-performance local or embedded ANN search controlled by application code. | Persistence, metadata filters, multi-user serving, and updates require additional engineering. |

The vendor comparison should start from workload shape. A compliance-heavy enterprise may prefer self-hosting because data control and network boundaries matter. A small team racing
toward a product demo may prefer a managed service because operational focus is expensive. A platform team standardizing internal RAG across many departments may choose an open
service with strong filtering and automation hooks so it can provide a shared capability.

```text
Decision path:
  Is semantic search tiny and local?
        |
        +-- yes --> Chroma, FAISS, or pgvector may be enough.
        |
        +-- no --> Do you need managed operations?
                    |
                    +-- yes --> Evaluate Pinecone, managed Weaviate, managed Qdrant, or cloud-native options.
                    |
                    +-- no --> Evaluate Qdrant, Weaviate, Milvus, or pgvector depending on scale and team skills.
```

This flow is intentionally conservative. Many teams adopt a dedicated vector database before they have enough traffic to justify it, then spend more time on infrastructure than on
retrieval quality. Other teams stay too long on a notebook index and suffer outages when persistence, filtering, or updates become mandatory. The better path is to design the
retrieval contract cleanly and move backends when requirements prove the need.

**Stop and think:** Your team already runs PostgreSQL well, has fewer than one million vectors, and needs transactional joins between business records and embeddings. Would you start
with a dedicated vector database or pgvector? Now change the scenario: the team has fifty million vectors, heavy semantic traffic, and independent scaling requirements. Explain why
your answer changes.

### Hybrid Search and Re-Ranking

Pure vector search can miss exact identifiers. If a user searches for "ERR_CONN_RESET" or "iPhone 15," semantic similarity may retrieve broadly related networking or phone documents
while missing the exact term the user cares about. Keyword search handles those exact tokens well. Hybrid search combines both candidate sources, then merges or re-ranks results so
the final context benefits from semantic breadth and lexical precision.

```text
User query: "ERR_CONN_RESET after ingress rollout"
        |
        +--> Keyword retrieval: exact error strings, product names, command flags
        |
        +--> Vector retrieval: semantically related outage reports and ingress docs
        |
        v
Candidate union: keyword hits + vector hits
        |
        v
Re-ranker: scores candidates against the original query
        |
        v
Final context: diverse, grounded, and relevant passages
```

A re-ranker is usually slower than the first-stage retriever, so it operates on a limited candidate set. For example, the system might retrieve the top fifty vector candidates and
the top fifty keyword candidates, deduplicate by document ID, then re-rank the best candidates down to eight passages for the LLM. This pattern improves answer quality because the
first stage favors recall and the second stage favors precision.

Hybrid search is especially important in technical education and operations content. Acronyms, version numbers, API fields, error messages, and command flags are not just words;
they are exact artifacts. A high-quality KubeDojo retrieval system should understand that "pod cannot resolve service DNS" and "CoreDNS lookup failure" are semantically related, but
it should also respect exact strings such as `CrashLoopBackOff`, `ImagePullBackOff`, `NetworkPolicy`, and `containerPort`.

### Storage, Sharding, and Replication

A single-node vector database can be enough for a long time if the corpus is modest and traffic is predictable. Eventually, one machine may not have enough memory, disk, CPU, or
availability guarantees. Sharding splits the collection across machines so capacity and query work can grow horizontally. Replication keeps copies of shards so the service can
survive node failure and continue serving reads.

```text
Collection: platform_docs
Total vectors: split across three shards

              +-------------------+
Query ------->|  Search coordinator|
              +-------------------+
                 |        |        |
                 v        v        v
            +--------+ +--------+ +--------+
            |Shard A | |Shard B | |Shard C |
            |Primary | |Primary | |Primary |
            +--------+ +--------+ +--------+
                |          |          |
                v          v          v
            +--------+ +--------+ +--------+
            |Replica | |Replica | |Replica |
            +--------+ +--------+ +--------+
```

The coordinator sends the query to relevant shards, each shard returns local top candidates, and the coordinator merges those candidates into a global top-k result. This architecture
scales capacity and can improve latency through parallelism, but it also adds coordination, network hops, operational complexity, and failure modes. Sharding is powerful when needed
and unnecessary complexity when one node is sufficient.

Replication has a different purpose. It protects availability and enables read scaling, but it increases storage cost and may complicate consistency during updates. For RAG, slightly
stale reads may be acceptable for many documents, while legal, medical, or security workflows may require stricter guarantees after deletion or access revocation. The retrieval design
must match the risk of the domain.

| Production Concern | Design Response | What to Measure |
|--------------------|-----------------|-----------------|
| Data too large for one node | Shard the collection by hash, tenant, time, or domain strategy. | Per-shard size, skew, query fan-out, and merge latency. |
| Node failure must not stop search | Replicate shards and test failover. | Recovery time, read availability, and replica lag. |
| Filters are slow | Create payload indexes for heavily filtered fields. | Filter selectivity, p95 latency, and query plans or engine metrics. |
| Memory pressure grows | Use smaller embeddings, quantization, on-disk vectors, or more shards. | Resident memory, cache hit rate, recall, and p99 latency. |
| Updates are frequent | Batch writes and monitor indexing backlog. | Write throughput, index build delay, and freshness. |
| Deletes must be enforced quickly | Use exact filters, tombstones, and validation tests for removed IDs. | Time from delete request to unavailable result. |

A senior-level architecture review asks what happens during re-indexing, restore, node loss, embedding-model migration, tenant deletion, and traffic spikes. Those events are not edge
cases in a production AI system. They are the normal lifecycle of a service that stores meaning-bearing data for real users.

---

## 5. Operating and Debugging Vector Search

Vector search quality problems often look mysterious because the result can be "kind of related" while still being wrong. The fastest debugging path is to split the system into
layers: embedding generation, collection contract, filters, ANN search, candidate scoring, re-ranking, and final LLM prompt assembly. Each layer has different symptoms and different
tests, so guessing usually wastes time.

```text
Debug path for bad retrieval:
  1. Is the query embedded with the same model used for indexed chunks?
  2. Does the query vector dimension match the collection dimension?
  3. Is the distance metric compatible with the embedding model?
  4. Are mandatory filters excluding good documents or allowing bad ones?
  5. Does brute force on a sample find better neighbors than ANN?
  6. Are chunks too small, too large, stale, duplicated, or missing context?
  7. Does re-ranking improve or harm the candidate order?
  8. Does the LLM receive the retrieved text you inspected?
```

Worked example: a support RAG service returns Linux file-permission content for the query "why does my Kubernetes service have no endpoints?" The team might blame the vector database,
but the real issue could be that the query was embedded with a different model after a deployment. The vector database faithfully searched a broken vector space. Checking dimensions,
model versions, and a few raw results often finds the problem faster than changing index parameters.

```python
from math import sqrt

def vector_magnitude(vector: list[float]) -> float:
    return sqrt(sum(value * value for value in vector))

def inspect_query_vector(query_vector: list[float], expected_dimension: int) -> None:
    actual_dimension = len(query_vector)
    magnitude = vector_magnitude(query_vector)
    print(f"expected_dimension={expected_dimension}")
    print(f"actual_dimension={actual_dimension}")
    print(f"dimension_match={actual_dimension == expected_dimension}")
    print(f"magnitude={magnitude:.4f}")

inspect_query_vector([0.12, -0.20, 0.31, 0.44], expected_dimension=4)
```

This simple inspection is not enough to prove retrieval quality, but it catches basic contract violations. If the dimension is wrong, the query should fail before search. If the
magnitude is unexpectedly large or small for a normalized embedding workflow, normalization or model assumptions may be wrong. If the embedding model changed without a re-index, the
geometry of stored vectors and query vectors no longer matches.

**Pause and predict:** A collection was created with 384-dimensional vectors from one embedding model, but a new deployment sends 768-dimensional query vectors. What should a well
designed system do? It should reject the query loudly before search, because silently truncating, padding, or accepting incompatible vectors would produce untrustworthy results.

### Query Optimization Patterns

Batching is one of the simplest performance improvements because network and request overhead often dominate small operations. Ingestion should send batches of points rather than
one request per document. Query services should batch independent searches when the API and product flow allow it. Batching is not a substitute for good indexes, but it removes a
large amount of avoidable overhead from high-volume systems.

```python
def batches(items: list[str], size: int) -> list[list[str]]:
    if size <= 0:
        raise ValueError("batch size must be positive")
    return [items[index:index + size] for index in range(0, len(items), size)]

documents = [f"document-{index}" for index in range(1, 13)]
for batch in batches(documents, 5):
    print(batch)
```

Result limits are another basic control. Retrieving one thousand candidates and then using five is usually wasteful unless a downstream re-ranker genuinely needs that many candidates.
Choose the smallest top-k that supports answer quality, diversity, and fallback behavior. Measure the effect because an overly tiny top-k can make the LLM answer from incomplete
context even when the correct document exists.

Payload indexes matter when filters are common and selective. If every query filters by `tenant_id`, `document_status`, or `product_area`, the vector database should be configured
so those fields are efficient filter keys. Otherwise the system may spend too much time intersecting semantic candidates with metadata constraints. The exact API varies by database,
but the design principle is stable: repeatedly filtered fields deserve indexing.

| Optimization | When It Helps | Risk If Misused |
|--------------|---------------|-----------------|
| Batched upserts | Ingestion sends many points to the database. | Very large batches can exceed request limits or cause long retries. |
| Lower top-k | The app needs only a small context window. | Good supporting documents may be excluded too early. |
| Higher `ef_search` | Evaluation shows relevant documents are missing. | Latency and CPU can rise without meaningful quality gain. |
| Payload indexes | Queries repeatedly filter by the same fields. | Indexes consume memory and write overhead, so do not index everything blindly. |
| Quantization | Memory or cache pressure limits scale. | Compression can reduce ranking quality if tested poorly. |
| Smaller embeddings | Storage and latency matter more than marginal quality gains. | A weaker model can damage retrieval more than any database tuning can fix. |
| Hybrid retrieval | Exact terms and semantic intent both matter. | Score merging and duplicate handling need careful evaluation. |

The most common senior mistake is optimizing the database before evaluating the retrieval pipeline. If chunking splits necessary context across documents, HNSW tuning cannot recover
the missing information. If the embedding model is weak for your domain, payload indexing will not improve semantic relevance. If access filters are wrong, faster search simply
returns wrong results sooner.

### Migration and Model Upgrades

Embedding models change, and production systems must handle that without corrupting retrieval. A new model may have a different dimension, different normalization assumptions, or a
different semantic geometry. You cannot safely insert vectors from a new model into an old collection unless the model is intentionally compatible. The usual pattern is to create a
new collection, backfill it, evaluate quality, switch reads gradually, then retire the old collection after rollback risk falls.

```text
Embedding model migration:
  1. Keep old collection serving production traffic.
  2. Create new collection with new dimension and distance metric.
  3. Backfill documents with deterministic IDs and new embeddings.
  4. Run evaluation queries against both collections.
  5. Shadow production queries and compare results.
  6. Gradually route read traffic to the new collection.
  7. Keep rollback available until quality and operations are stable.
  8. Delete old collection only after retention and compliance checks.
```

This migration flow prevents a half-upgraded vector space. It also gives the team a measurement point: the new model should improve an agreed retrieval metric, reduce cost, improve
latency, support multilingual queries, or solve another concrete problem. Upgrading because a model is newer is not a production reason by itself.

Backups and restores deserve the same discipline. A snapshot is useful only if it can be restored into a working service. Test restore procedures on a schedule, verify collection
counts and sample queries, and confirm that application configuration can point to the restored service. The time to discover a broken backup procedure is not during an outage.

---

## Did You Know?

1. **HNSW became influential because it changed the production trade-off:** instead of choosing between exact brute force and unacceptable latency, teams could get high recall with graph-based approximate search on ordinary CPU-backed systems.

2. **A vector database does not create semantic meaning by itself:** the embedding model creates the vector space, while the database stores, indexes, filters, updates, and retrieves vectors inside that space.

3. **Hybrid retrieval is common because technical queries contain exact artifacts:** error codes, API names, version strings, and command flags often need keyword matching even when the surrounding intent benefits from embeddings.

4. **Deterministic IDs are an operational quality feature:** they make ingestion idempotent, simplify reprocessing, reduce duplicate results, and make delete or update behavior easier to reason about.

---

## Common Mistakes

| Mistake | What Goes Wrong | How to Fix It |
|---------|-----------------|---------------|
| Mixing embedding models inside one collection | Results become incoherent because stored vectors and query vectors do not share the same learned geometry. | Record the model name and dimension in configuration, then create a new collection for incompatible model upgrades. |
| Filtering after broad retrieval | The app may drop most candidates, leak forbidden payloads into logs, or return weak leftovers after authorization filtering. | Push tenant, status, date, and domain constraints into the vector database query as metadata filters. |
| Using auto-generated IDs for document chunks | Reprocessing inserts duplicates, inflates storage, and makes repeated documents dominate search results. | Generate deterministic IDs from stable source fields and content hashes, then use upsert semantics. |
| Choosing a distance metric by habit | Cosine, dot product, and Euclidean distance rank neighbors differently, so the wrong metric can damage relevance. | Follow the embedding model guidance and test retrieval quality with labeled queries. |
| Creating one collection per user by default | Collection sprawl makes backups, migrations, monitoring, and query routing harder than necessary. | Use payload filters for user or tenant fields unless isolation requirements justify separate collections. |
| Ignoring payload indexes | Frequent filters become slow because the database has to work too hard to apply metadata constraints. | Index heavily used filter fields such as tenant, status, product area, and updated year. |
| Tuning HNSW without an evaluation set | The team changes latency and recall blindly, so improvements are anecdotal and regressions go unnoticed. | Build a small query set with expected documents, then measure recall, p95 latency, p99 latency, and memory. |
| Treating the vector store as the system of record | Application state, permissions, transactions, and lifecycle rules become difficult to enforce correctly. | Keep canonical records in a transactional store and use the vector database for retrieval-focused representations. |

---

## Quiz

**Q1.** Your team has a PostgreSQL application with product records, inventory state, and customer-specific pricing. Leadership wants users to search for products using natural language phrases such as "quiet keyboard for shared office." What architecture should you recommend, and why?

<details>
<summary>Answer</summary>

Use PostgreSQL as the system of record for products, inventory, pricing, permissions, and transactions, then add vector retrieval for semantic product matching. The vector database or pgvector index should store embeddings and retrieval payloads, while PostgreSQL remains authoritative for exact business data. This design keeps approximate semantic search separate from exact state and lets the application apply pricing, availability, and authorization rules safely.

</details>

**Q2.** A RAG service returns strong results in development, but after a deployment its answers become unrelated. The collection was built with 384-dimensional embeddings, and the new application version sends 768-dimensional query vectors. What should you debug first, and what should the system do?

<details>
<summary>Answer</summary>

Debug the embedding contract first. The query model no longer matches the collection model and dimension, so the search should fail loudly before retrieval. A safe system validates vector dimension and model configuration, rejects incompatible queries, and routes model upgrades through a new collection with backfill and evaluation rather than mixing vector spaces.

</details>

**Q3.** A legal search platform reprocesses two million contracts every weekend. After several months, customers see the same contract repeated across top results, and storage costs have multiplied. Which ingestion design change would prevent this failure?

<details>
<summary>Answer</summary>

Use deterministic IDs for document chunks and upsert points instead of inserting with auto-generated IDs. The ID should include stable source metadata and a content hash so reprocessing the same chunk updates the existing point. This prevents duplicate vectors, reduces storage waste, and avoids ranking distortion caused by repeated copies of the same document.

</details>

**Q4.** An incident-response assistant must never retrieve draft runbooks or documents from another tenant, even if they are semantically close to the query. The current service retrieves the top one hundred vector results and filters them in application code. What should change?

<details>
<summary>Answer</summary>

The tenant and document-status constraints should move into the vector database query as metadata filters. Filtering after broad retrieval can return forbidden payloads to the application and may leave weak candidates after invalid results are removed. Query-time filtering lets the database search only eligible candidates and supports defense-in-depth authorization.

</details>

**Q5.** Your evaluation set shows that relevant documents exist in the collection, but HNSW search misses them for several important queries. Latency is currently well below the product budget. What tuning change would you test first, and what trade-off should you expect?

<details>
<summary>Answer</summary>

Increase the HNSW search width, often called `ef_search` or a database-specific equivalent such as `hnsw_ef`. This should explore more candidates and may improve recall, but it will usually increase query latency and CPU usage. The change should be tested against recall, p95 latency, p99 latency, and resource metrics rather than accepted by intuition.

</details>

**Q6.** A platform team has fewer than one million vectors, already runs PostgreSQL well, and needs vector search tightly joined with relational records. Another team has fifty million vectors, high query traffic, and independent scaling needs. Compare the likely storage choices.

<details>
<summary>Answer</summary>

The first team can reasonably start with pgvector because the workload is moderate, relational joins matter, and operational simplicity is valuable. The second team should evaluate a dedicated vector database because independent scaling, specialized ANN performance, sharding, payload indexing, and operational separation become more important at that size and traffic level. The right answer changes because the binding constraints change.

</details>

**Q7.** A documentation assistant retrieves semantically related pages but often misses exact error strings such as `ImagePullBackOff` and `ERR_CONN_RESET`. Users complain that the system understands the general topic but not the concrete failure. What retrieval pattern should you design?

<details>
<summary>Answer</summary>

Design hybrid retrieval that combines keyword candidates with vector candidates, then deduplicates and optionally re-ranks them. Keyword search preserves exact error strings, command flags, and API names, while vector search captures paraphrased intent and related explanations. A re-ranker can then choose final context that is both semantically relevant and lexically grounded.

</details>

---

## Hands-On Exercise

Goal: build a local vector search workflow that demonstrates persistent storage, deterministic IDs, semantic retrieval, metadata filtering, update/delete behavior, and basic debugging. The lab uses Qdrant because it is easy to run locally and exposes the production concepts this module teaches.

Before starting, verify that Docker is available and that your repository already has a `.venv` directory. The commands below use `.venv/bin/python` explicitly so the lab follows the project rule that scripts should run through the repository virtual environment.

- [ ] Start a local Qdrant container with persistent storage.

```bash
mkdir -p qdrant_storage

docker rm -f qdrant-lab >/dev/null 2>&1 || true

docker run -d \
  --name qdrant-lab \
  -p 6333:6333 \
  -v "$(pwd)/qdrant_storage:/qdrant/storage" \
  qdrant/qdrant
```

- [ ] Verify that Qdrant is reachable on the local API port.

```bash
curl -s http://127.0.0.1:6333/readyz
curl -s http://127.0.0.1:6333/collections
```

- [ ] Install the Python dependencies into the existing virtual environment.

```bash
.venv/bin/python -m pip install qdrant-client sentence-transformers
```

- [ ] Create a file named `vector_lab.py` with the following runnable lab code.

```python
import hashlib
from typing import Iterable

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, FieldCondition, Filter, MatchValue, PointStruct, Range, VectorParams
from sentence_transformers import SentenceTransformer

COLLECTION = "rag_lab"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def stable_id(source: str, chunk_index: int, text: str) -> int:
    key = f"{source}:{chunk_index}:{hashlib.sha256(text.encode()).hexdigest()}"
    return int(hashlib.sha256(key.encode()).hexdigest()[:15], 16)


def chunks() -> list[dict[str, object]]:
    return [
        {
            "source": "k8s/networking.md",
            "chunk_index": 1,
            "text": "A Kubernetes Service selects ready pods and gives clients a stable virtual address.",
            "category": "kubernetes",
            "year": 2026,
            "difficulty": "intermediate",
        },
        {
            "source": "k8s/network-policy.md",
            "chunk_index": 2,
            "text": "NetworkPolicy controls which pods can communicate across namespaces and labels.",
            "category": "kubernetes",
            "year": 2025,
            "difficulty": "advanced",
        },
        {
            "source": "linux/permissions.md",
            "chunk_index": 1,
            "text": "Linux file permissions use owner, group, and other bits to control access.",
            "category": "linux",
            "year": 2024,
            "difficulty": "beginner",
        },
        {
            "source": "linux/systemd.md",
            "chunk_index": 2,
            "text": "systemd units describe services, dependencies, restart behavior, and logs.",
            "category": "linux",
            "year": 2025,
            "difficulty": "intermediate",
        },
        {
            "source": "ml/rag.md",
            "chunk_index": 1,
            "text": "Retrieval augmented generation supplies relevant context to a language model before answering.",
            "category": "machine-learning",
            "year": 2026,
            "difficulty": "intermediate",
        },
        {
            "source": "ml/embeddings.md",
            "chunk_index": 2,
            "text": "Embeddings map text into vectors so semantically similar passages are near each other.",
            "category": "machine-learning",
            "year": 2025,
            "difficulty": "beginner",
        },
        {
            "source": "platform/incidents.md",
            "chunk_index": 1,
            "text": "Incident reviews should identify contributing factors, detection gaps, and follow-up actions.",
            "category": "platform",
            "year": 2024,
            "difficulty": "intermediate",
        },
        {
            "source": "platform/slo.md",
            "chunk_index": 2,
            "text": "Service level objectives define reliability targets that guide engineering trade-offs.",
            "category": "platform",
            "year": 2026,
            "difficulty": "advanced",
        },
    ]


def batched(items: list[dict[str, object]], size: int) -> Iterable[list[dict[str, object]]]:
    for index in range(0, len(items), size):
        yield items[index:index + size]


def create_collection(client: QdrantClient) -> None:
    if client.collection_exists(COLLECTION):
        client.delete_collection(COLLECTION)

    client.create_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )


def load_points(client: QdrantClient, model: SentenceTransformer) -> None:
    for batch in batched(chunks(), 4):
        texts = [str(item["text"]) for item in batch]
        vectors = model.encode(texts, normalize_embeddings=True).tolist()
        points = []

        for item, vector in zip(batch, vectors):
            point_id = stable_id(str(item["source"]), int(item["chunk_index"]), str(item["text"]))
            payload = dict(item)
            points.append(PointStruct(id=point_id, vector=vector, payload=payload))

        client.upsert(collection_name=COLLECTION, points=points)


def print_results(label: str, results) -> None:
    print(f"\n{label}")
    for result in results:
        payload = result.payload or {}
        print(f"{result.score:.3f} | {payload.get('category')} | {payload.get('year')} | {payload.get('text')}")


def search_plain(client: QdrantClient, model: SentenceTransformer) -> None:
    query = "how do pods communicate inside a cluster"
    query_vector = model.encode(query, normalize_embeddings=True).tolist()

    results = client.query_points(
        collection_name=COLLECTION,
        query=query_vector,
        limit=3,
        with_payload=True,
    ).points

    print_results("plain semantic search", results)


def search_filtered(client: QdrantClient, model: SentenceTransformer) -> None:
    query = "how do pods communicate inside a cluster"
    query_vector = model.encode(query, normalize_embeddings=True).tolist()

    query_filter = Filter(
        must=[
            FieldCondition(key="category", match=MatchValue(value="kubernetes")),
            FieldCondition(key="year", range=Range(gte=2025)),
        ]
    )

    results = client.query_points(
        collection_name=COLLECTION,
        query=query_vector,
        query_filter=query_filter,
        limit=3,
        with_payload=True,
    ).points

    print_results("filtered semantic search", results)


def update_and_delete(client: QdrantClient, model: SentenceTransformer) -> None:
    docs = chunks()
    updated = dict(docs[0])
    updated["text"] = "A Kubernetes Service tracks ready pod endpoints and gives clients stable discovery."
    updated_id = stable_id(str(updated["source"]), int(updated["chunk_index"]), str(docs[0]["text"]))
    updated_vector = model.encode(str(updated["text"]), normalize_embeddings=True).tolist()

    client.upsert(
        collection_name=COLLECTION,
        points=[PointStruct(id=updated_id, vector=updated_vector, payload=updated)],
    )

    deleted = docs[-1]
    deleted_id = stable_id(str(deleted["source"]), int(deleted["chunk_index"]), str(deleted["text"]))
    client.delete(collection_name=COLLECTION, points_selector=[deleted_id])


def main() -> None:
    client = QdrantClient(url="http://127.0.0.1:6333")
    model = SentenceTransformer(MODEL_NAME)

    create_collection(client)
    load_points(client, model)

    info = client.get_collection(COLLECTION)
    print(f"points after load: {info.points_count}")

    search_plain(client, model)
    search_filtered(client, model)

    update_and_delete(client, model)
    info = client.get_collection(COLLECTION)
    print(f"\npoints after update/delete: {info.points_count}")


if __name__ == "__main__":
    main()
```

- [ ] Run the lab and inspect the plain and filtered search results.

```bash
.venv/bin/python vector_lab.py
```

- [ ] Confirm that the collection exists and contains points after the script runs.

```bash
curl -s http://127.0.0.1:6333/collections/rag_lab
```

- [ ] Restart Qdrant and verify that the collection remains available because storage is mounted on disk.

```bash
docker restart qdrant-lab
curl -s http://127.0.0.1:6333/collections/rag_lab
```

- [ ] Run a manual filtered query experiment by changing the filter from `category = kubernetes` to `category = linux`, then run the script again and compare the retrieved documents.

- [ ] Change the query text to `how do services find healthy endpoints` and predict whether the Kubernetes service chunk or the NetworkPolicy chunk should rank higher before running the script.

- [ ] Write a short note explaining what changed between plain semantic search and filtered semantic search.

- [ ] Write a short note explaining why deterministic IDs are safer than auto-generated IDs for recurring ingestion jobs.

- [ ] Write a short note identifying which fields in the payload would deserve indexes in a larger production collection.

Success criteria:

- [ ] Qdrant responds on `127.0.0.1:6333`.

- [ ] The `rag_lab` collection is created with 384-dimensional cosine vectors.

- [ ] The lab loads at least eight points with text and metadata payloads.

- [ ] Plain semantic search returns results that are meaningfully related to the query.

- [ ] Filtered semantic search narrows the result set by metadata while preserving semantic relevance.

- [ ] The update and delete step changes the collection state without recreating the container.

- [ ] The collection remains available after a container restart.

- [ ] Your notes explain persistence, deterministic IDs, metadata filtering, and the difference between semantic similarity and exact filters.

---

## Next Module

Next: [Module 1.2: Building a RAG Retrieval Pipeline](./module-1.2-building-a-rag-retrieval-pipeline/)

---

## Sources

- [arxiv.org: 1603.09320](https://arxiv.org/abs/1603.09320) — The arXiv record directly gives the paper title, authors, and 2016 submission date.
- [github.com: weaviate](https://github.com/weaviate/weaviate) — The GitHub README explicitly describes Weaviate as open-source and highlights hybrid/vector-plus-keyword search with filtering.
- [github.com: chroma](https://github.com/chroma-core/chroma) — The GitHub README directly shows `pip install chromadb`, in-memory prototyping, and optional persistence.
- [huggingface.co: all MiniLM L6 v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) — The Hugging Face model card explicitly states that the model maps text to a 384-dimensional dense vector space.
- [huggingface.co: e5 large v2](https://huggingface.co/intfloat/e5-large-v2) — The Hugging Face model card explicitly states that the embedding size is 1024.

---
title: "Module 9.6: LangChain & LlamaIndex - LLM Application Frameworks"
slug: platform/toolkits/data-ai-platforms/ml-platforms/module-9.6-langchain-llamaindex
sidebar:
  order: 7
---
## Complexity: [COMPLEX]

**Time to Complete**: 90 minutes
**Prerequisites**: Module 9.4 (vLLM), Basic Python, Understanding of LLM APIs
**Learning Objectives**:
- Understand RAG architecture and implementation
- Build chains and agents with LangChain
- Create document indexes with LlamaIndex
- Deploy LLM applications on Kubernetes

---

## Why This Module Matters

Raw LLMs have limitations: they hallucinate, don't know about your data, and can't take actions. Building production LLM applications requires retrieval, context management, output parsing, and orchestration. Writing this from scratch takes months.

**LangChain and LlamaIndex are the toolkits for LLM applications.**

They provide the building blocks: document loaders, text splitters, vector stores, retrievers, chains, and agents. Instead of reinventing the wheel, you compose proven components into production applications.

> "LangChain is to LLM apps what Rails is to web apps—you get the patterns, you focus on the product."

---

## Did You Know?

- LangChain has **600+ integrations** with LLMs, vector stores, tools, and APIs
- LlamaIndex was originally called "GPT Index" before the naming got confusing
- The RAG pattern (Retrieval-Augmented Generation) can **reduce hallucinations by 80%+**
- LangChain's agent framework powers many of the "AI assistants" you use daily
- LlamaIndex can index **structured data, code, SQL databases**, not just documents
- Both frameworks can run with **local models** (Ollama, vLLM) or cloud APIs (OpenAI, Anthropic)

---

## RAG: The Core Pattern

```
┌─────────────────────────────────────────────────────────────────────────┐
│              RAG (Retrieval-Augmented Generation)                       │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    1. INDEXING (Offline)                         │   │
│  │                                                                  │   │
│  │  Documents → Chunks → Embeddings → Vector Store                 │   │
│  │  ┌───────┐   ┌───────┐   ┌───────┐   ┌───────────────────┐     │   │
│  │  │ PDFs  │──▶│ 512   │──▶│ [0.1, │──▶│     Pinecone      │     │   │
│  │  │ Docs  │   │ token │   │  0.3, │   │     Weaviate      │     │   │
│  │  │ Web   │   │ chunks│   │  ...] │   │     ChromaDB      │     │   │
│  │  └───────┘   └───────┘   └───────┘   └───────────────────┘     │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    2. RETRIEVAL (Online)                         │   │
│  │                                                                  │   │
│  │  Query → Embed → Search → Top K Chunks                          │   │
│  │  ┌───────────┐   ┌───────┐   ┌───────────────────────────┐     │   │
│  │  │"What is   │──▶│[0.2,  │──▶│ Similarity Search         │     │   │
│  │  │ K8s?"     │   │ 0.4,] │   │ → Chunk 1, Chunk 5, Chunk │     │   │
│  │  └───────────┘   └───────┘   └───────────────────────────┘     │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    3. GENERATION (Online)                        │   │
│  │                                                                  │   │
│  │  Context + Query → LLM → Answer                                 │   │
│  │  ┌─────────────────────────────┐   ┌───────────────────────┐   │   │
│  │  │ System: Use this context... │──▶│      LLM              │   │   │
│  │  │ Context: [Chunk 1, 5, 7]    │   │  (GPT-4, Llama, etc.) │   │   │
│  │  │ Query: What is K8s?         │   │                       │   │   │
│  │  └─────────────────────────────┘   └───────────┬───────────┘   │   │
│  │                                                 │               │   │
│  │                                                 ▼               │   │
│  │                                    "Kubernetes is an open-      │   │
│  │                                     source container..."        │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## LangChain vs LlamaIndex

| Aspect | LangChain | LlamaIndex |
|--------|-----------|------------|
| **Focus** | General LLM orchestration | Data-centric LLM apps |
| **Strengths** | Agents, chains, tools | Indexing, retrieval, data connectors |
| **Philosophy** | "Lego blocks for LLMs" | "Build knowledge bases" |
| **Best For** | Complex workflows, agents | RAG, document Q&A |
| **Learning Curve** | Steeper | Gentler |
| **Integration** | Work great together! | Work great together! |

### When to Use What

```
USE LANGCHAIN WHEN:
├── Building agents that use tools
├── Creating multi-step reasoning chains
├── Integrating with many external systems
├── Need fine-grained control over prompts
└── Building conversational agents

USE LLAMAINDEX WHEN:
├── Building document Q&A systems
├── Creating knowledge bases from varied sources
├── Need sophisticated retrieval strategies
├── Working with structured + unstructured data
└── Want simpler RAG setup

USE BOTH WHEN:
├── Building production RAG applications
├── LlamaIndex for indexing/retrieval
└── LangChain for orchestration/agents
```

---

## LangChain Fundamentals

### Installation

```bash
pip install langchain langchain-openai langchain-community
pip install chromadb  # Vector store
pip install tiktoken  # Token counting
```

### Basic Chain

```python
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser

# Initialize LLM (can also use local models)
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# Create a simple prompt
prompt = ChatPromptTemplate.from_template(
    "Explain {concept} in the context of Kubernetes. Keep it under 100 words."
)

# Build the chain
chain = prompt | llm | StrOutputParser()

# Run
result = chain.invoke({"concept": "pods"})
print(result)
```

### RAG Chain with LangChain

```python
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA

# 1. Load documents
loader = WebBaseLoader("https://kubernetes.io/docs/concepts/overview/")
documents = loader.load()

# 2. Split into chunks
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
)
chunks = text_splitter.split_documents(documents)

# 3. Create embeddings and vector store
embeddings = OpenAIEmbeddings()
vectorstore = Chroma.from_documents(chunks, embeddings)

# 4. Create retrieval chain
llm = ChatOpenAI(model="gpt-4o", temperature=0)
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
)

# 5. Query
result = qa_chain.invoke("What are the main components of Kubernetes?")
print(result["result"])
```

### Agent with Tools

```python
from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.tools import tool
from langchain import hub

# Define custom tools
@tool
def get_pod_count(namespace: str) -> str:
    """Get the number of pods in a Kubernetes namespace."""
    # In reality, this would call kubectl or K8s API
    return f"There are 5 pods in namespace {namespace}"

@tool
def get_deployment_status(name: str) -> str:
    """Get the status of a Kubernetes deployment."""
    return f"Deployment {name} is running with 3/3 replicas ready"

# Create agent
llm = ChatOpenAI(model="gpt-4o", temperature=0)
tools = [get_pod_count, get_deployment_status]

# Get a prompt template
prompt = hub.pull("hwchase17/openai-functions-agent")

# Create the agent
agent = create_openai_functions_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# Run
result = agent_executor.invoke({
    "input": "How many pods are in the default namespace and what's the status of the nginx deployment?"
})
print(result["output"])
```

---

## LlamaIndex Fundamentals

### Installation

```bash
pip install llama-index
pip install llama-index-llms-openai
pip install llama-index-embeddings-openai
pip install llama-index-vector-stores-chroma
```

### Simple Document Q&A

```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

# Load documents from a directory
documents = SimpleDirectoryReader("./data").load_data()

# Create index (handles chunking and embedding)
index = VectorStoreIndex.from_documents(documents)

# Query
query_engine = index.as_query_engine()
response = query_engine.query("What is Kubernetes?")
print(response)
```

### Advanced RAG with LlamaIndex

```python
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    Settings,
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb

# Configure settings
Settings.llm = OpenAI(model="gpt-4o", temperature=0)
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
Settings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=50)

# Create persistent vector store
chroma_client = chromadb.PersistentClient(path="./chroma_db")
chroma_collection = chroma_client.get_or_create_collection("k8s_docs")
vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

# Load and index documents
documents = SimpleDirectoryReader("./k8s_docs").load_data()
index = VectorStoreIndex.from_documents(
    documents,
    storage_context=storage_context,
)

# Create query engine with custom settings
query_engine = index.as_query_engine(
    similarity_top_k=5,
    response_mode="tree_summarize",
)

# Query
response = query_engine.query(
    "How do I troubleshoot a pod in CrashLoopBackOff?"
)
print(response)
print("\nSources:")
for node in response.source_nodes:
    print(f"- {node.node.metadata.get('file_name', 'Unknown')}: {node.score:.3f}")
```

### Hybrid Search (Semantic + Keyword)

```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.retrievers import VectorIndexRetriever, KeywordTableSimpleRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.postprocessor import SimilarityPostprocessor

# Create indices
documents = SimpleDirectoryReader("./data").load_data()
vector_index = VectorStoreIndex.from_documents(documents)

# Semantic retriever
vector_retriever = VectorIndexRetriever(
    index=vector_index,
    similarity_top_k=3,
)

# Create query engine with reranking
query_engine = RetrieverQueryEngine(
    retriever=vector_retriever,
    node_postprocessors=[
        SimilarityPostprocessor(similarity_cutoff=0.7)
    ],
)

response = query_engine.query("kubectl commands for debugging")
```

---

## Production Patterns

### 1. Using Local Models (vLLM)

```python
# LangChain with vLLM
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="mistralai/Mistral-7B-Instruct-v0.2",
    openai_api_base="http://vllm-server:8000/v1",
    openai_api_key="not-needed",
)

# LlamaIndex with vLLM
from llama_index.llms.openai_like import OpenAILike

llm = OpenAILike(
    model="mistralai/Mistral-7B-Instruct-v0.2",
    api_base="http://vllm-server:8000/v1",
    api_key="not-needed",
)
```

### 2. Streaming Responses

```python
# LangChain streaming
from langchain_openai import ChatOpenAI
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

llm = ChatOpenAI(
    model="gpt-4o",
    streaming=True,
    callbacks=[StreamingStdOutCallbackHandler()],
)

# LlamaIndex streaming
from llama_index.core import VectorStoreIndex

index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine(streaming=True)

streaming_response = query_engine.query("Explain pods")
for text in streaming_response.response_gen:
    print(text, end="", flush=True)
```

### 3. Conversation Memory

```python
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains import ConversationChain

llm = ChatOpenAI(model="gpt-4o")
memory = ConversationBufferWindowMemory(k=5)  # Keep last 5 exchanges

conversation = ConversationChain(
    llm=llm,
    memory=memory,
    verbose=True,
)

# Maintains context across calls
conversation.predict(input="What is a Kubernetes pod?")
conversation.predict(input="How does it relate to containers?")  # Knows "it" = pod
conversation.predict(input="Can you give me an example?")  # Still in context
```

### 4. FastAPI Integration

```python
from fastapi import FastAPI
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser

app = FastAPI()

# Initialize chain
llm = ChatOpenAI(model="gpt-4o")
prompt = ChatPromptTemplate.from_template(
    "Answer this Kubernetes question: {question}"
)
chain = prompt | llm | StrOutputParser()

class Query(BaseModel):
    question: str

@app.post("/ask")
async def ask_question(query: Query):
    result = await chain.ainvoke({"question": query.question})
    return {"answer": result}

# Run with: uvicorn main:app --host 0.0.0.0 --port 8080
```

---

## Deploying on Kubernetes

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rag-service
  namespace: llm-apps
spec:
  replicas: 2
  selector:
    matchLabels:
      app: rag-service
  template:
    metadata:
      labels:
        app: rag-service
    spec:
      containers:
      - name: rag
        image: myregistry/rag-service:v1
        ports:
        - containerPort: 8080
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: openai-credentials
              key: api-key
        - name: VLLM_ENDPOINT
          value: "http://vllm-server:8000/v1"
        - name: CHROMA_HOST
          value: "chromadb-service"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: rag-service
spec:
  selector:
    app: rag-service
  ports:
  - port: 80
    targetPort: 8080
```

### Vector Database (ChromaDB)

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: chromadb
  namespace: llm-apps
spec:
  serviceName: chromadb
  replicas: 1
  selector:
    matchLabels:
      app: chromadb
  template:
    metadata:
      labels:
        app: chromadb
    spec:
      containers:
      - name: chromadb
        image: chromadb/chroma:latest
        ports:
        - containerPort: 8000
        volumeMounts:
        - name: data
          mountPath: /chroma/chroma
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 20Gi
```

---

## War Story: The Chatbot That Forgot Everything

A fintech company built a customer support chatbot using LangChain. It worked great in demos but failed in production.

**The Problem**:
Customers would ask follow-up questions, and the bot would have no idea what they were talking about.

```
Customer: What's my account balance?
Bot: Your balance is $1,234.56

Customer: Why is it so low?
Bot: I'm sorry, I don't have information about what is low.
     Could you clarify what you're referring to?
```

**The Root Cause**:
- No conversation memory between requests
- Each Lambda invocation was stateless
- The chat UI was sending only the latest message

**The Solution**:

```python
from langchain.memory import ConversationBufferWindowMemory
from langchain_community.chat_message_histories import RedisChatMessageHistory

# Store conversation history in Redis
def get_memory(session_id: str):
    message_history = RedisChatMessageHistory(
        session_id=session_id,
        url="redis://redis-cluster:6379",
        ttl=3600,  # Expire after 1 hour
    )
    return ConversationBufferWindowMemory(
        memory_key="chat_history",
        chat_memory=message_history,
        return_messages=True,
        k=10,  # Keep last 10 exchanges
    )

@app.post("/chat")
async def chat(request: ChatRequest):
    memory = get_memory(request.session_id)
    chain = ConversationChain(llm=llm, memory=memory)
    response = await chain.ainvoke({"input": request.message})
    return {"response": response["response"]}
```

**Kubernetes changes**:
```yaml
# Added Redis for session storage
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis-cluster
spec:
  # ... Redis configuration
```

**Results**:
- Customer satisfaction: 45% → 82%
- Issue resolution rate: 30% → 65%
- Average conversation length: 2 messages → 8 messages

The lesson: **LLM applications need state management**. The model doesn't remember—you have to build the memory.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| No chunk overlap | Missing context at boundaries | Use 10-20% overlap |
| Chunks too large | Diluted relevance | 500-1000 tokens typical |
| Ignoring metadata | Can't filter results | Include source, date, etc. |
| No reranking | Poor retrieval quality | Add reranker after retrieval |
| Stateless design | No conversation memory | Add Redis/DB for sessions |
| Prompt injection | Security vulnerability | Validate inputs, use guards |

---

## Hands-On Exercise: Build a K8s Documentation Bot

**Objective**: Create a RAG chatbot that answers questions about Kubernetes.

### Task 1: Set Up the Environment

```bash
pip install langchain langchain-openai chromadb

# Create data directory
mkdir -p ./k8s_data
```

### Task 2: Download Sample Data

```python
# download_docs.py
import requests

urls = [
    "https://raw.githubusercontent.com/kubernetes/website/main/content/en/docs/concepts/overview/what-is-kubernetes.md",
    "https://raw.githubusercontent.com/kubernetes/website/main/content/en/docs/concepts/workloads/pods/_index.md",
]

for i, url in enumerate(urls):
    response = requests.get(url)
    with open(f"./k8s_data/doc_{i}.md", "w") as f:
        f.write(response.text)
    print(f"Downloaded doc_{i}.md")
```

### Task 3: Build the RAG Application

```python
# rag_bot.py
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader
from langchain_community.vectorstores import Chroma
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory

# Load documents
loader = DirectoryLoader("./k8s_data", glob="**/*.md")
documents = loader.load()
print(f"Loaded {len(documents)} documents")

# Split
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
)
chunks = splitter.split_documents(documents)
print(f"Created {len(chunks)} chunks")

# Create vector store
embeddings = OpenAIEmbeddings()
vectorstore = Chroma.from_documents(
    chunks,
    embeddings,
    persist_directory="./chroma_db"
)

# Create conversational chain
llm = ChatOpenAI(model="gpt-4o", temperature=0)
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True,
)

qa_chain = ConversationalRetrievalChain.from_llm(
    llm=llm,
    retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
    memory=memory,
    verbose=True,
)

# Interactive chat loop
print("\nK8s Documentation Bot ready! Type 'quit' to exit.\n")
while True:
    question = input("You: ")
    if question.lower() == 'quit':
        break

    result = qa_chain.invoke({"question": question})
    print(f"\nBot: {result['answer']}\n")
```

### Task 4: Test the Bot

```bash
python rag_bot.py

# Try these questions:
# - What is Kubernetes?
# - What are pods?
# - How do pods relate to containers?  # Tests memory
# - Can you give me an example?  # Tests context
```

### Task 5: Wrap in FastAPI

```python
# main.py
from fastapi import FastAPI
from pydantic import BaseModel
# ... import the chain from above

app = FastAPI()

class Query(BaseModel):
    session_id: str
    question: str

# Store chains per session (use Redis in production)
sessions = {}

@app.post("/chat")
async def chat(query: Query):
    if query.session_id not in sessions:
        sessions[query.session_id] = create_chain()

    chain = sessions[query.session_id]
    result = await chain.ainvoke({"question": query.question})
    return {"answer": result["answer"]}

@app.get("/health")
def health():
    return {"status": "ok"}
```

### Success Criteria

- [ ] Documents loaded and chunked
- [ ] Vector store created and persisted
- [ ] Can ask questions and get relevant answers
- [ ] Bot remembers conversation context
- [ ] Follow-up questions work correctly

---

## Quiz

### Question 1
What is RAG and why is it important?

<details>
<summary>Show Answer</summary>

**RAG (Retrieval-Augmented Generation) retrieves relevant context before generating responses**

RAG reduces hallucinations by grounding the LLM's responses in actual documents. Instead of relying solely on training data, the model uses retrieved context to answer questions accurately.
</details>

### Question 2
When should you use LangChain vs LlamaIndex?

<details>
<summary>Show Answer</summary>

**LangChain for agents/chains/orchestration, LlamaIndex for indexing/retrieval**

LangChain excels at building complex workflows with tools and agents. LlamaIndex focuses on turning data into queryable indexes. They work well together—LlamaIndex for retrieval, LangChain for orchestration.
</details>

### Question 3
What is chunk overlap and why is it important?

<details>
<summary>Show Answer</summary>

**Chunk overlap ensures context isn't lost at chunk boundaries**

When splitting documents into chunks, overlap (e.g., 200 tokens) means adjacent chunks share some text. This prevents important context from being split between chunks and lost during retrieval.
</details>

### Question 4
How do you use local models (vLLM) with LangChain?

<details>
<summary>Show Answer</summary>

**Point ChatOpenAI to vLLM's OpenAI-compatible endpoint**

```python
llm = ChatOpenAI(
    model="model-name",
    openai_api_base="http://vllm-server:8000/v1",
    openai_api_key="not-needed",
)
```
</details>

### Question 5
What is an agent in LangChain?

<details>
<summary>Show Answer</summary>

**An LLM that can decide which tools to use to accomplish a task**

Agents use the LLM to reason about what actions to take, call tools (functions), observe results, and continue until the task is complete. They're more flexible than fixed chains.
</details>

### Question 6
How do you add conversation memory to a LangChain application?

<details>
<summary>Show Answer</summary>

**Use ConversationBufferMemory or similar memory classes**

```python
from langchain.memory import ConversationBufferMemory
memory = ConversationBufferMemory(return_messages=True)
chain = ConversationChain(llm=llm, memory=memory)
```

For production, use Redis or a database backend for persistence.
</details>

### Question 7
What is the purpose of a vector store in RAG?

<details>
<summary>Show Answer</summary>

**Store document embeddings and enable semantic similarity search**

Vector stores (Chroma, Pinecone, Weaviate) store the numerical representations (embeddings) of text chunks. When a query comes in, it's embedded and compared to stored vectors to find semantically similar content.
</details>

### Question 8
What's the typical chunk size for RAG applications?

<details>
<summary>Show Answer</summary>

**500-1000 tokens with 10-20% overlap**

Chunks should be small enough to be specific but large enough to contain context. 512-1024 tokens is common. Too large dilutes relevance; too small loses context.
</details>

---

## Key Takeaways

1. **RAG grounds LLMs in facts** - retrieval + generation reduces hallucinations
2. **LangChain for orchestration** - chains, agents, tools, memory
3. **LlamaIndex for data** - indexing, retrieval, structured data
4. **Chunk size matters** - 500-1000 tokens with overlap
5. **Memory is essential** - use Redis/DB for conversation state
6. **Local models work** - vLLM, Ollama via OpenAI-compatible APIs
7. **Streaming improves UX** - show tokens as they generate
8. **Metadata enables filtering** - include source, date, etc.
9. **Reranking improves quality** - post-process retrieved results
10. **Production needs persistence** - vector stores, session storage

---

## Further Reading

- [LangChain Documentation](https://python.langchain.com/docs/) - Official guides
- [LlamaIndex Documentation](https://docs.llamaindex.ai/) - Official guides
- [RAG Survey Paper](https://arxiv.org/abs/2312.10997) - Academic overview
- [LangChain Templates](https://github.com/langchain-ai/langchain/tree/master/templates) - Production examples

---

## Toolkit Complete!

Congratulations! You've completed the ML Platforms Toolkit. You now understand:
- Model training with Kubeflow
- Experiment tracking with MLflow
- Feature stores for ML
- High-throughput inference with vLLM
- Distributed serving with Ray Serve
- Building LLM applications with LangChain and LlamaIndex

Continue to other toolkits or apply these skills to build production ML systems!

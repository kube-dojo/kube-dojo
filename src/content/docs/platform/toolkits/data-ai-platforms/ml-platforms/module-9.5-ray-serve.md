---
title: "Module 9.5: Ray Serve - Distributed Model Serving"
slug: platform/toolkits/data-ai-platforms/ml-platforms/module-9.5-ray-serve
sidebar:
  order: 6
---
## Complexity: [COMPLEX]

**Time to Complete**: 90 minutes
**Prerequisites**: Module 9.4 (vLLM), Basic Python, Understanding of distributed systems
**Learning Objectives**:
- Understand Ray's architecture for distributed computing
- Deploy Ray Serve on Kubernetes with KubeRay
- Build inference pipelines with model composition
- Scale GPU inference across multiple nodes

---

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Deploy Ray Serve on Kubernetes for scalable model serving with dynamic batching and autoscaling**
- **Configure Ray Serve deployments with resource allocation, replica management, and traffic routing**
- **Implement multi-model serving pipelines with Ray Serve's composition API for inference graphs**
- **Compare Ray Serve's unified compute framework against dedicated serving solutions for ML workloads**


## Why This Module Matters

Single-node inference hits limits fast. Your LLM needs 4 GPUs, your embedding model needs 1, and your reranker needs 2. You can't fit them on one machine. And when traffic spikes, you need to scale each component independently.

**Ray Serve solves the distributed inference puzzle.**

Built on the Ray distributed computing framework, Ray Serve lets you compose models into pipelines, scale them independently, and spread computation across a cluster. It's the bridge between "works on my machine" and "works at production scale."

> "Ray Serve is like Kubernetes for ML inference—it handles the distribution so you can focus on the models."

---

## Did You Know?

- Ray powers ML infrastructure at **OpenAI, Uber, Amazon, and Spotify**
- Ray can scale to **10,000+ nodes** in a single cluster
- Ray Serve can handle **millions of requests per second** across a cluster
- The name "Ray" comes from the rays of light spreading out—representing distributed computation
- Ray was created at UC Berkeley's RISELab (same lab that created Spark)
- Ray Serve supports **fractional GPU allocation**—run 4 models on 1 GPU

---

## Ray Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Ray Cluster                                     │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────────┐│
│  │                        Head Node                                    ││
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐    ││
│  │  │   GCS (Global   │  │    Dashboard    │  │   Ray Serve     │    ││
│  │  │   Control Store)│  │   (port 8265)   │  │   Controller    │    ││
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘    ││
│  │                              │                                      ││
│  │            ┌─────────────────┼─────────────────┐                   ││
│  │            ▼                 ▼                 ▼                   ││
│  │  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐      ││
│  │  │    Raylet       │ │    Raylet       │ │    Raylet       │      ││
│  │  │  (Worker mgmt)  │ │  (Worker mgmt)  │ │  (Worker mgmt)  │      ││
│  │  └─────────────────┘ └─────────────────┘ └─────────────────┘      ││
│  └────────────────────────────────────────────────────────────────────┘│
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────────┐│
│  │                      Worker Nodes                                   ││
│  │                                                                     ││
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐    ││
│  │  │  Worker Node 1  │  │  Worker Node 2  │  │  Worker Node 3  │    ││
│  │  │  ┌───────────┐  │  │  ┌───────────┐  │  │  ┌───────────┐  │    ││
│  │  │  │ Raylet    │  │  │  │ Raylet    │  │  │  │ Raylet    │  │    ││
│  │  │  └───────────┘  │  │  └───────────┘  │  │  └───────────┘  │    ││
│  │  │  ┌───────────┐  │  │  ┌───────────┐  │  │  ┌───────────┐  │    ││
│  │  │  │ Workers   │  │  │  │ Workers   │  │  │  │ Workers   │  │    ││
│  │  │  │ (GPU/CPU) │  │  │  │ (GPU/CPU) │  │  │  │ (GPU/CPU) │  │    ││
│  │  │  └───────────┘  │  │  └───────────┘  │  │  └───────────┘  │    ││
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘    ││
│  └────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
```

### Key Components

| Component | Role | Description |
|-----------|------|-------------|
| **GCS** | Cluster state | Global Control Store tracks all actors/tasks |
| **Head Node** | Coordination | Runs GCS, dashboard, Serve controller |
| **Worker Nodes** | Computation | Run actual workloads (models) |
| **Raylet** | Node manager | Manages workers on each node |
| **Ray Serve** | Inference | HTTP serving layer on top of Ray |

---

## Installing Ray Serve on Kubernetes

### Option 1: KubeRay Operator (Recommended)

```bash
# Install KubeRay operator
helm repo add kuberay https://ray-project.github.io/kuberay-helm/
helm repo update

helm install kuberay-operator kuberay/kuberay-operator \
    --namespace ray-system \
    --create-namespace

# Verify
kubectl get pods -n ray-system
```

### Option 2: Deploy Ray Cluster

```yaml
apiVersion: ray.io/v1
kind: RayCluster
metadata:
  name: ray-cluster
  namespace: ray-serving
spec:
  rayVersion: '2.9.0'
  headGroupSpec:
    rayStartParams:
      dashboard-host: '0.0.0.0'
    template:
      spec:
        containers:
        - name: ray-head
          image: rayproject/ray-ml:2.9.0-py310-gpu
          ports:
          - containerPort: 6379
            name: gcs
          - containerPort: 8265
            name: dashboard
          - containerPort: 10001
            name: client
          - containerPort: 8000
            name: serve
          resources:
            limits:
              cpu: "4"
              memory: "16Gi"
            requests:
              cpu: "2"
              memory: "8Gi"
  workerGroupSpecs:
  - groupName: gpu-workers
    replicas: 2
    minReplicas: 1
    maxReplicas: 4
    rayStartParams: {}
    template:
      spec:
        containers:
        - name: ray-worker
          image: rayproject/ray-ml:2.9.0-py310-gpu
          resources:
            limits:
              cpu: "8"
              memory: "32Gi"
              nvidia.com/gpu: "1"
            requests:
              cpu: "4"
              memory: "16Gi"
              nvidia.com/gpu: "1"
```

### Deploy RayService (Model Serving)

```yaml
apiVersion: ray.io/v1
kind: RayService
metadata:
  name: llm-service
  namespace: ray-serving
spec:
  serviceUnhealthySecondThreshold: 900
  deploymentUnhealthySecondThreshold: 300
  serveConfigV2: |
    applications:
    - name: llm-app
      route_prefix: /
      import_path: serve_llm:deployment
      runtime_env:
        pip:
          - vllm
          - transformers
      deployments:
      - name: LLMDeployment
        num_replicas: 2
        ray_actor_options:
          num_gpus: 1
  rayClusterConfig:
    rayVersion: '2.9.0'
    headGroupSpec:
      rayStartParams:
        dashboard-host: '0.0.0.0'
      template:
        spec:
          containers:
          - name: ray-head
            image: rayproject/ray-ml:2.9.0-py310-gpu
            resources:
              limits:
                cpu: "4"
                memory: "16Gi"
    workerGroupSpecs:
    - groupName: gpu-workers
      replicas: 2
      template:
        spec:
          containers:
          - name: ray-worker
            image: rayproject/ray-ml:2.9.0-py310-gpu
            resources:
              limits:
                nvidia.com/gpu: "1"
```

---

## Ray Serve Basics

### Simple Deployment

```python
# serve_example.py
from ray import serve
from starlette.requests import Request

@serve.deployment
class HelloWorld:
    def __call__(self, request: Request) -> str:
        return "Hello from Ray Serve!"

# Bind and deploy
app = HelloWorld.bind()

# Run with: serve run serve_example:app
```

### LLM Deployment with vLLM

```python
# serve_llm.py
from ray import serve
from vllm import LLM, SamplingParams
from starlette.requests import Request
import json

@serve.deployment(
    ray_actor_options={"num_gpus": 1},
    autoscaling_config={
        "min_replicas": 1,
        "max_replicas": 4,
        "target_num_ongoing_requests_per_replica": 10,
    }
)
class LLMDeployment:
    def __init__(self):
        self.llm = LLM(
            model="mistralai/Mistral-7B-Instruct-v0.2",
            tensor_parallel_size=1,
            gpu_memory_utilization=0.90,
        )
        self.sampling_params = SamplingParams(
            temperature=0.7,
            max_tokens=500,
        )

    async def __call__(self, request: Request) -> dict:
        body = await request.json()
        prompt = body.get("prompt", "")

        outputs = self.llm.generate([prompt], self.sampling_params)
        generated_text = outputs[0].outputs[0].text

        return {"generated_text": generated_text}

deployment = LLMDeployment.bind()
```

### Model Composition (Pipeline)

```python
# serve_pipeline.py
from ray import serve
from starlette.requests import Request
import numpy as np

@serve.deployment(ray_actor_options={"num_cpus": 1})
class Preprocessor:
    def preprocess(self, text: str) -> str:
        # Clean and prepare text
        return text.lower().strip()

@serve.deployment(ray_actor_options={"num_gpus": 0.5})
class Embedder:
    def __init__(self):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def embed(self, text: str) -> list:
        return self.model.encode(text).tolist()

@serve.deployment(ray_actor_options={"num_gpus": 1})
class LLM:
    def __init__(self):
        from vllm import LLM as VLLMModel, SamplingParams
        self.llm = VLLMModel("mistralai/Mistral-7B-Instruct-v0.2")
        self.params = SamplingParams(max_tokens=200)

    def generate(self, prompt: str) -> str:
        outputs = self.llm.generate([prompt], self.params)
        return outputs[0].outputs[0].text

@serve.deployment
class RAGPipeline:
    def __init__(self, preprocessor, embedder, llm):
        self.preprocessor = preprocessor
        self.embedder = embedder
        self.llm = llm

    async def __call__(self, request: Request) -> dict:
        body = await request.json()
        query = body.get("query", "")

        # Step 1: Preprocess
        clean_query = await self.preprocessor.preprocess.remote(query)

        # Step 2: Embed (for retrieval - simplified here)
        embedding = await self.embedder.embed.remote(clean_query)

        # Step 3: Generate with LLM
        prompt = f"Answer this question: {clean_query}"
        response = await self.llm.generate.remote(prompt)

        return {
            "query": query,
            "response": response
        }

# Compose the pipeline
preprocessor = Preprocessor.bind()
embedder = Embedder.bind()
llm = LLM.bind()
pipeline = RAGPipeline.bind(preprocessor, embedder, llm)
```

---

## Advanced: Autoscaling

### Request-Based Autoscaling

```python
@serve.deployment(
    autoscaling_config={
        "min_replicas": 1,
        "max_replicas": 10,
        "target_num_ongoing_requests_per_replica": 5,
        "upscale_delay_s": 10,
        "downscale_delay_s": 60,
    }
)
class AutoscaledModel:
    # ...
```

### Scaling Configuration Explained

| Parameter | Effect |
|-----------|--------|
| `min_replicas` | Minimum instances (always running) |
| `max_replicas` | Maximum instances |
| `target_num_ongoing_requests_per_replica` | Target queue depth per replica |
| `upscale_delay_s` | Seconds before scaling up |
| `downscale_delay_s` | Seconds before scaling down |

### GPU Fractional Allocation

```python
# Run 2 small models on 1 GPU
@serve.deployment(ray_actor_options={"num_gpus": 0.5})
class SmallModel1:
    pass

@serve.deployment(ray_actor_options={"num_gpus": 0.5})
class SmallModel2:
    pass
```

---

## Ray Serve vs Alternatives

| Feature | Ray Serve | Triton | Seldon Core | KServe |
|---------|----------|--------|-------------|--------|
| **Distributed** | Native | Limited | Via K8s | Via K8s |
| **Model Composition** | Python native | Config-based | Graph | Pipeline |
| **Autoscaling** | Built-in | External | External | Knative |
| **GPU Fractional** | Yes | No | No | Limited |
| **Framework Support** | Any Python | ONNX, TF, PyTorch | Many | Many |
| **Learning Curve** | Medium | High | High | High |
| **Best For** | Python ML | Low latency | Enterprise | KNative users |

### When to Choose Ray Serve

**Choose Ray Serve when:**
- You need model composition (pipelines)
- You want Python-native development
- You need fractional GPU allocation
- You're already using Ray for training
- You need flexible autoscaling

**Consider alternatives when:**
- You need lowest possible latency (Triton)
- You're in a KNative environment (KServe)
- You need enterprise ML governance (Seldon)

---

## Monitoring Ray Serve

### Ray Dashboard

```bash
# Port forward dashboard
kubectl port-forward svc/ray-cluster-head-svc 8265:8265 -n ray-serving

# Open http://localhost:8265
```

Dashboard shows:
- Cluster resources (CPU/GPU/memory)
- Actor and task status
- Serve deployment metrics
- Log streaming

### Prometheus Metrics

```yaml
# Enable metrics export
apiVersion: ray.io/v1
kind: RayCluster
metadata:
  name: ray-cluster
spec:
  headGroupSpec:
    rayStartParams:
      metrics-export-port: '8080'
```

Key metrics:
- `ray_serve_deployment_replica_healthy`
- `ray_serve_num_ongoing_requests`
- `ray_serve_request_latency_ms`
- `ray_node_gpu_utilization`

### Grafana Dashboard

```promql
# Request latency P99
histogram_quantile(0.99, sum(rate(ray_serve_request_latency_ms_bucket[5m])) by (le, deployment))

# Throughput
sum(rate(ray_serve_num_requests_total[5m])) by (deployment)

# GPU utilization across cluster
avg(ray_node_gpu_utilization) by (node)

# Queue depth
sum(ray_serve_num_ongoing_requests) by (deployment)
```

---

## War Story: The Multi-Model Nightmare

A legal tech startup was building an AI document analysis platform. They needed:
- OCR model for scanned documents
- Entity extraction model (NER)
- Summarization model (LLM)
- Classification model

**The Challenge**:
Each model had different requirements:
- OCR: CPU-only, fast
- NER: Small GPU, medium speed
- LLM: Large GPU, slow
- Classifier: Small GPU, fast

**The Naive Approach**:
4 separate Kubernetes deployments, each with dedicated resources.

```yaml
# Ended up with:
# - OCR: 4 pods, 2 CPU each
# - NER: 2 pods, 1 GPU each
# - LLM: 2 pods, 4 GPUs each (tensor parallel)
# - Classifier: 2 pods, 1 GPU each
#
# Total: 10 pods, 12 GPUs
# GPU utilization: ~30% (lots of idle time)
```

**The Ray Serve Solution**:

```python
@serve.deployment(ray_actor_options={"num_cpus": 2})
class OCR:
    # CPU-bound, scales independently
    pass

@serve.deployment(ray_actor_options={"num_gpus": 0.25})
class NER:
    # 4 can share 1 GPU
    pass

@serve.deployment(ray_actor_options={"num_gpus": 4})
class LLM:
    # Needs full 4 GPUs
    pass

@serve.deployment(ray_actor_options={"num_gpus": 0.25})
class Classifier:
    # 4 can share 1 GPU
    pass

@serve.deployment
class Pipeline:
    def __init__(self, ocr, ner, llm, classifier):
        self.ocr = ocr
        self.ner = ner
        self.llm = llm
        self.classifier = classifier

    async def process(self, document):
        # OCR runs in parallel with classification of metadata
        text_future = self.ocr.extract.remote(document)
        meta_class_future = self.classifier.classify.remote(document.metadata)

        text = await text_future

        # NER and LLM can run in parallel on text
        entities_future = self.ner.extract.remote(text)
        summary_future = self.llm.summarize.remote(text)

        return {
            "text": text,
            "entities": await entities_future,
            "summary": await summary_future,
            "classification": await meta_class_future
        }
```

**The Results**:
- GPUs needed: 6 (down from 12)
- GPU utilization: ~75%
- Latency: 40% lower (parallel execution)
- Cost: 50% reduction

The key insight: Ray Serve's composition and fractional GPU allocation let them pack models efficiently while maintaining independent scaling.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Not setting resource requests | OOM or GPU contention | Always specify `num_gpus`, `num_cpus` |
| Blocking in async handlers | Poor throughput | Use `async`/`await` properly |
| Too many replicas | Wasted resources | Start small, use autoscaling |
| Ignoring warmup time | Slow first requests | Use `@serve.deployment(health_check_period_s=...)` |
| Not using batching | Low GPU utilization | Use `@serve.batch` for compatible models |
| Missing error handling | Cascading failures | Add timeouts and retries |

---

## Hands-On Exercise: Build a RAG Pipeline with Ray Serve

**Objective**: Deploy a RAG (Retrieval-Augmented Generation) pipeline using Ray Serve.

### Setup

```bash
# Create namespace
kubectl create namespace ray-demo

# Install KubeRay operator (if not installed)
helm install kuberay-operator kuberay/kuberay-operator \
    -n ray-system --create-namespace
```

### Task 1: Deploy Ray Cluster

```bash
kubectl apply -f - <<EOF
apiVersion: ray.io/v1
kind: RayCluster
metadata:
  name: ray-demo-cluster
  namespace: ray-demo
spec:
  rayVersion: '2.9.0'
  headGroupSpec:
    rayStartParams:
      dashboard-host: '0.0.0.0'
    template:
      spec:
        containers:
        - name: ray-head
          image: rayproject/ray:2.9.0-py310
          ports:
          - containerPort: 6379
          - containerPort: 8265
          - containerPort: 8000
          resources:
            limits:
              cpu: "2"
              memory: "4Gi"
  workerGroupSpecs:
  - groupName: workers
    replicas: 2
    template:
      spec:
        containers:
        - name: ray-worker
          image: rayproject/ray:2.9.0-py310
          resources:
            limits:
              cpu: "2"
              memory: "4Gi"
EOF

# Wait for cluster
kubectl wait --for=condition=ready pod -l ray.io/cluster=ray-demo-cluster -n ray-demo --timeout=300s
```

### Task 2: Create the RAG Application

```python
# rag_app.py
from ray import serve
from starlette.requests import Request
import httpx

# Simulated vector store (in production, use Pinecone, Weaviate, etc.)
KNOWLEDGE_BASE = {
    "kubernetes": "Kubernetes is an open-source container orchestration platform...",
    "docker": "Docker is a platform for developing, shipping, and running containers...",
    "ray": "Ray is a distributed computing framework for scaling Python applications...",
}

@serve.deployment(num_replicas=2)
class Retriever:
    def retrieve(self, query: str) -> str:
        # Simple keyword matching (use vector similarity in production)
        query_lower = query.lower()
        for key, value in KNOWLEDGE_BASE.items():
            if key in query_lower:
                return value
        return "No relevant context found."

@serve.deployment(num_replicas=1)
class Generator:
    async def generate(self, query: str, context: str) -> str:
        # In production, call your LLM here
        # For demo, we'll use a simple template
        return f"Based on the context: {context[:100]}...\n\nAnswer: This is a generated response about {query}"

@serve.deployment
class RAGPipeline:
    def __init__(self, retriever, generator):
        self.retriever = retriever
        self.generator = generator

    async def __call__(self, request: Request) -> dict:
        body = await request.json()
        query = body.get("query", "")

        # Step 1: Retrieve relevant context
        context = await self.retriever.retrieve.remote(query)

        # Step 2: Generate response with context
        response = await self.generator.generate.remote(query, context)

        return {
            "query": query,
            "context": context,
            "response": response
        }

# Compose the pipeline
retriever = Retriever.bind()
generator = Generator.bind()
app = RAGPipeline.bind(retriever, generator)
```

### Task 3: Deploy the Application

```bash
# Copy app to head pod
kubectl cp rag_app.py ray-demo-cluster-head-xxxxx:/tmp/rag_app.py -n ray-demo

# Exec into head pod
kubectl exec -it ray-demo-cluster-head-xxxxx -n ray-demo -- bash

# Inside pod:
cd /tmp
serve run rag_app:app --host 0.0.0.0 --port 8000
```

### Task 4: Test the Pipeline

```bash
# Port forward
kubectl port-forward svc/ray-demo-cluster-head-svc 8000:8000 -n ray-demo &

# Test
curl http://localhost:8000 \
    -H "Content-Type: application/json" \
    -d '{"query": "What is Kubernetes?"}'
```

### Task 5: Check the Dashboard

```bash
# Port forward dashboard
kubectl port-forward svc/ray-demo-cluster-head-svc 8265:8265 -n ray-demo

# Open http://localhost:8265
# Check:
# - Serve deployments
# - Replica status
# - Request metrics
```

### Success Criteria

- [ ] Ray cluster is running on Kubernetes
- [ ] RAG pipeline deployed with 3 components
- [ ] Can make requests and get responses
- [ ] Dashboard shows deployment health
- [ ] Understand how components communicate

### Cleanup

```bash
kubectl delete namespace ray-demo
```

---

## Quiz

### Question 1
What is the main advantage of Ray Serve over simple HTTP servers?

<details>
<summary>Show Answer</summary>

**Native distributed computing, model composition, and autoscaling**

Ray Serve builds on Ray's distributed runtime, allowing models to be deployed across multiple nodes, composed into pipelines, and scaled independently based on load.
</details>

### Question 2
What is KubeRay?

<details>
<summary>Show Answer</summary>

**A Kubernetes operator for managing Ray clusters**

KubeRay provides CRDs (RayCluster, RayJob, RayService) for deploying and managing Ray on Kubernetes with native autoscaling and lifecycle management.
</details>

### Question 3
How does Ray Serve enable fractional GPU allocation?

<details>
<summary>Show Answer</summary>

**By specifying `num_gpus` as a fraction (e.g., 0.5) in ray_actor_options**

Ray's scheduler allows multiple actors to share a GPU by specifying fractional resources. This enables running multiple small models on a single GPU efficiently.
</details>

### Question 4
What is model composition in Ray Serve?

<details>
<summary>Show Answer</summary>

**Connecting multiple deployments into a pipeline using `.bind()` and remote calls**

Ray Serve lets you bind deployments together and call them using `.remote()`, enabling complex inference pipelines where each component scales independently.
</details>

### Question 5
How does Ray Serve autoscaling work?

<details>
<summary>Show Answer</summary>

**Based on `target_num_ongoing_requests_per_replica` metric**

Ray Serve scales replicas up when queue depth exceeds the target and scales down after `downscale_delay_s` seconds of low load, configurable via `autoscaling_config`.
</details>

### Question 6
What is the Ray Dashboard used for?

<details>
<summary>Show Answer</summary>

**Monitoring cluster resources, actors, tasks, and Serve deployments**

The dashboard (port 8265) shows real-time cluster state, GPU/CPU utilization, deployment health, request metrics, and logs.
</details>

### Question 7
When should you use `.remote()` vs direct function calls?

<details>
<summary>Show Answer</summary>

**Use `.remote()` for distributed/async execution, direct calls for local execution**

`.remote()` returns a Ray ObjectRef (future) and executes the function potentially on another node. Direct calls execute synchronously in the same process.
</details>

### Question 8
What's the difference between RayCluster and RayService CRDs?

<details>
<summary>Show Answer</summary>

**RayCluster deploys the cluster; RayService deploys cluster + Serve applications**

RayCluster just manages the Ray runtime. RayService also deploys and manages Serve applications with automatic updates and health checking.
</details>

---

## Key Takeaways

1. **Ray Serve extends Ray to HTTP serving** - distributed inference made simple
2. **Model composition is Python-native** - bind deployments, call with `.remote()`
3. **Fractional GPUs maximize utilization** - run 4 models on 1 GPU
4. **Autoscaling is built-in** - based on queue depth
5. **KubeRay simplifies Kubernetes deployment** - CRDs for clusters and services
6. **Dashboard provides visibility** - real-time cluster and deployment metrics
7. **Async handlers improve throughput** - use `async`/`await` properly
8. **Resource requests are important** - always specify CPU/GPU needs
9. **Great for ML pipelines** - RAG, multi-model, preprocessing chains
10. **Production-proven at scale** - used by OpenAI, Uber, Amazon

---

## Further Reading

- [Ray Serve Documentation](https://docs.ray.io/en/latest/serve/index.html) - Official guides
- [KubeRay Documentation](https://ray-project.github.io/kuberay/) - Kubernetes deployment
- [Ray Serve Autoscaling](https://docs.ray.io/en/latest/serve/scaling-and-resource-allocation.html) - Scaling guide
- [Ray GitHub](https://github.com/ray-project/ray) - Source and examples

---

## Next Module

Continue to [Module 9.6: LangChain & LlamaIndex](../module-9.6-langchain-llamaindex/) to learn about building LLM applications with frameworks for RAG, agents, and chains.

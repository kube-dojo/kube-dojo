---
title: "Module 9.4: vLLM - High-Throughput LLM Serving"
slug: platform/toolkits/data-ai-platforms/ml-platforms/module-9.4-vllm
sidebar:
  order: 5
---
## Complexity: [COMPLEX]

**Time to Complete**: 90 minutes
**Prerequisites**: Module 9.1 (Kubeflow basics), Understanding of transformer models, Kubernetes GPU support basics
**Learning Objectives**:
- Understand vLLM's PagedAttention architecture
- Deploy vLLM on Kubernetes with GPU support
- Configure batching, memory, and model sharding
- Optimize inference latency and throughput

---

## What You'll Be Able to Do

After completing this module, you will be able to:

- **Deploy vLLM on Kubernetes for high-throughput large language model inference with PagedAttention**
- **Configure vLLM serving with model parallelism, quantization, and continuous batching for GPU efficiency**
- **Implement vLLM's OpenAI-compatible API for drop-in replacement of commercial LLM endpoints**
- **Optimize GPU memory utilization and throughput with vLLM's KV cache management strategies**


## Why This Module Matters

Large Language Models (LLMs) are expensive to serve. A single Llama-70B inference can use 140GB of GPU memory and take 30+ seconds. Naive serving approaches waste 50-90% of GPU capacity because of how attention memory is managed.

**vLLM solves the LLM serving efficiency crisis.**

Through innovations like PagedAttention and continuous batching, vLLM achieves 2-24x higher throughput than alternatives like Hugging Face's text-generation-inference. It's the difference between serving 10 users or 200 users on the same hardware.

> "We went from $50K/month in GPU costs to $8K/month. Same traffic, same model, just vLLM instead of vanilla transformers."

---

## Did You Know?

- vLLM's PagedAttention was inspired by **operating system virtual memory** techniques from the 1960s
- vLLM can serve a 70B parameter model on 2 GPUs that would normally require 8 GPUs with naive serving
- The project was created at UC Berkeley and achieved **24x throughput** improvements in benchmarks
- vLLM supports **100+ model architectures** including Llama, Mistral, Falcon, GPT-NeoX, and more
- Continuous batching means vLLM **never waits** for slow requests to finish before starting new ones
- vLLM's memory efficiency comes from sharing attention key-value cache pages between requests

---

## The LLM Serving Challenge

### Why Traditional Serving Fails

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Traditional LLM Serving                              │
│                                                                         │
│  Request 1: "Write a poem about..."                                     │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ KV Cache: ████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │   │
│  │           Used: 40%    Wasted (reserved but unused): 60%         │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  Request 2: "Summarize this document..."                                │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ KV Cache: ██████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │   │
│  │           Used: 25%    Wasted: 75%                               │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  Problem: Each request reserves MAX possible memory upfront             │
│  Result: 2 concurrent requests max, 50-70% GPU memory wasted           │
└─────────────────────────────────────────────────────────────────────────┘
```

### How vLLM Fixes It: PagedAttention

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    vLLM with PagedAttention                             │
│                                                                         │
│  Shared KV Cache Pool (allocated in pages):                             │
│  ┌──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┐         │
│  │R1│R1│R1│R2│R2│R3│R3│R3│R3│R1│R2│R4│R4│  │  │  │  │  │  │  │         │
│  └──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┘         │
│   ^     ^     ^                                                         │
│   │     │     └── Pages for Request 3                                  │
│   │     └──────── Pages for Request 2                                  │
│   └────────────── Pages for Request 1                                  │
│                                                                         │
│  Benefits:                                                              │
│  • Memory allocated on-demand (per page)                                │
│  • Pages can be non-contiguous                                          │
│  • Shared prefixes reuse pages (chat history!)                          │
│  • 4x more concurrent requests possible                                 │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## vLLM Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         vLLM Server                                     │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────────┐│
│  │                    API Layer (OpenAI Compatible)                    ││
│  │  /v1/completions    /v1/chat/completions    /v1/embeddings         ││
│  └─────────────────────────────┬──────────────────────────────────────┘│
│                                │                                        │
│  ┌─────────────────────────────┼──────────────────────────────────────┐│
│  │                    Scheduler                                        ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 ││
│  │  │  Request    │  │ Continuous  │  │  Preemption │                 ││
│  │  │  Queue      │  │  Batching   │  │  Manager    │                 ││
│  │  └─────────────┘  └─────────────┘  └─────────────┘                 ││
│  └─────────────────────────────┬──────────────────────────────────────┘│
│                                │                                        │
│  ┌─────────────────────────────┼──────────────────────────────────────┐│
│  │                    PagedAttention Engine                            ││
│  │  ┌─────────────────────────────────────────────────────────────┐   ││
│  │  │              Block Manager (KV Cache)                        │   ││
│  │  │  • Page allocation    • Sharing    • Swapping               │   ││
│  │  └─────────────────────────────────────────────────────────────┘   ││
│  └─────────────────────────────┬──────────────────────────────────────┘│
│                                │                                        │
│  ┌─────────────────────────────┼──────────────────────────────────────┐│
│  │                    Model Executor                                   ││
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐       ││
│  │  │   GPU 0   │  │   GPU 1   │  │   GPU 2   │  │   GPU 3   │       ││
│  │  │  (Shard)  │  │  (Shard)  │  │  (Shard)  │  │  (Shard)  │       ││
│  │  └───────────┘  └───────────┘  └───────────┘  └───────────┘       ││
│  └────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
```

### Key Components

| Component | Role | Description |
|-----------|------|-------------|
| **API Layer** | Request handling | OpenAI-compatible endpoints |
| **Scheduler** | Request management | Continuous batching, preemption |
| **PagedAttention** | Memory management | Efficient KV cache with pages |
| **Block Manager** | Page allocation | Manages memory pages per request |
| **Model Executor** | Inference | Runs model across GPUs |

---

## Installing vLLM

### Prerequisites

- NVIDIA GPU with compute capability 7.0+ (V100, A100, H100, etc.)
- CUDA 11.8+
- 16GB+ GPU memory (model-dependent)

### Option 1: Docker (Quickest)

```bash
# Run vLLM server with a model
docker run --runtime nvidia --gpus all \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    -p 8000:8000 \
    --ipc=host \
    vllm/vllm-openai:latest \
    --model mistralai/Mistral-7B-Instruct-v0.2

# Test it
curl http://localhost:8000/v1/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "mistralai/Mistral-7B-Instruct-v0.2",
        "prompt": "Hello, world!",
        "max_tokens": 100
    }'
```

### Option 2: Python Installation

```bash
# Install vLLM
pip install vllm

# Run the server
python -m vllm.entrypoints.openai.api_server \
    --model mistralai/Mistral-7B-Instruct-v0.2 \
    --host 0.0.0.0 \
    --port 8000
```

### Option 3: Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vllm-mistral
  namespace: llm-serving
spec:
  replicas: 1
  selector:
    matchLabels:
      app: vllm-mistral
  template:
    metadata:
      labels:
        app: vllm-mistral
    spec:
      containers:
      - name: vllm
        image: vllm/vllm-openai:latest
        args:
        - --model
        - mistralai/Mistral-7B-Instruct-v0.2
        - --tensor-parallel-size
        - "1"
        - --max-model-len
        - "4096"
        ports:
        - containerPort: 8000
        resources:
          limits:
            nvidia.com/gpu: "1"
          requests:
            nvidia.com/gpu: "1"
            memory: "32Gi"
            cpu: "4"
        env:
        - name: HUGGING_FACE_HUB_TOKEN
          valueFrom:
            secretKeyRef:
              name: hf-token
              key: token
        volumeMounts:
        - name: cache
          mountPath: /root/.cache/huggingface
        - name: shm
          mountPath: /dev/shm
      volumes:
      - name: cache
        persistentVolumeClaim:
          claimName: model-cache-pvc
      - name: shm
        emptyDir:
          medium: Memory
          sizeLimit: "16Gi"
      nodeSelector:
        nvidia.com/gpu.product: NVIDIA-A100-SXM4-40GB
---
apiVersion: v1
kind: Service
metadata:
  name: vllm-mistral
  namespace: llm-serving
spec:
  selector:
    app: vllm-mistral
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
```

---

## Configuration Deep Dive

### Memory and Throughput Configuration

```bash
# Key parameters for optimization
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-2-70b-chat-hf \
    --tensor-parallel-size 4 \          # Split model across 4 GPUs
    --gpu-memory-utilization 0.90 \     # Use 90% of GPU memory
    --max-num-batched-tokens 8192 \     # Max tokens per batch
    --max-num-seqs 256 \                # Max concurrent sequences
    --max-model-len 4096 \              # Max context length
    --block-size 16 \                   # KV cache page size
    --swap-space 4 \                    # CPU swap space (GB)
    --enforce-eager                      # Disable CUDA graph (debug)
```

### Parameter Explained

| Parameter | Default | Effect |
|-----------|---------|--------|
| `--tensor-parallel-size` | 1 | GPUs to shard model across |
| `--gpu-memory-utilization` | 0.90 | % of GPU memory for KV cache |
| `--max-num-batched-tokens` | varies | Tokens processed per forward pass |
| `--max-num-seqs` | 256 | Max concurrent requests |
| `--max-model-len` | model max | Max context length |
| `--block-size` | 16 | KV cache page size (tokens) |
| `--swap-space` | 4 | GB of CPU memory for swapping |

### Model Parallelism

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Tensor Parallelism (--tensor-parallel-size)          │
│                                                                         │
│  Model Layer (e.g., attention):                                         │
│  ┌────────────────────────────────────────────────────────────────────┐│
│  │                        Weight Matrix                                ││
│  │  ┌─────────────┬─────────────┬─────────────┬─────────────┐         ││
│  │  │   GPU 0     │    GPU 1    │    GPU 2    │    GPU 3    │         ││
│  │  │  (shard 0)  │  (shard 1)  │  (shard 2)  │  (shard 3)  │         ││
│  │  └─────────────┴─────────────┴─────────────┴─────────────┘         ││
│  └────────────────────────────────────────────────────────────────────┘│
│                                                                         │
│  70B model requirements:                                                │
│  - FP16: ~140GB VRAM                                                   │
│  - With TP=4: ~35GB per GPU (fits A100-40GB)                          │
│  - With TP=8: ~17.5GB per GPU (fits V100-32GB)                        │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Using vLLM

### OpenAI-Compatible API

```python
from openai import OpenAI

# Point to vLLM server
client = OpenAI(
    base_url="http://vllm-server:8000/v1",
    api_key="not-needed"  # vLLM doesn't require auth by default
)

# Chat completion
response = client.chat.completions.create(
    model="mistralai/Mistral-7B-Instruct-v0.2",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is Kubernetes?"}
    ],
    max_tokens=500,
    temperature=0.7
)

print(response.choices[0].message.content)
```

### Streaming Responses

```python
# Stream for better UX
stream = client.chat.completions.create(
    model="mistralai/Mistral-7B-Instruct-v0.2",
    messages=[
        {"role": "user", "content": "Write a haiku about containers."}
    ],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

### Batch Processing

```python
# Process many prompts efficiently
prompts = [
    "Summarize: Kubernetes orchestrates containers...",
    "Summarize: Docker builds container images...",
    "Summarize: Prometheus collects metrics...",
]

# vLLM batches these automatically
responses = []
for prompt in prompts:
    response = client.completions.create(
        model="mistralai/Mistral-7B-Instruct-v0.2",
        prompt=prompt,
        max_tokens=100
    )
    responses.append(response.choices[0].text)
```

---

## Advanced: Prefix Caching

vLLM can share KV cache between requests with common prefixes:

```python
# System prompt is cached and reused
system_prompt = """You are a Kubernetes expert assistant.
You help users understand container orchestration,
deployments, services, and cloud-native practices.
Always provide examples when helpful."""

# First request computes KV cache for system prompt
response1 = client.chat.completions.create(
    model="mistralai/Mistral-7B-Instruct-v0.2",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "What is a Pod?"}
    ]
)

# Subsequent requests REUSE the cached system prompt KV!
# This makes responses ~30-50% faster
response2 = client.chat.completions.create(
    model="mistralai/Mistral-7B-Instruct-v0.2",
    messages=[
        {"role": "system", "content": system_prompt},  # Same prefix
        {"role": "user", "content": "What is a Service?"}  # Different question
    ]
)
```

---

## vLLM vs Alternatives

| Feature | vLLM | TGI (HuggingFace) | Triton + TensorRT-LLM |
|---------|------|-------------------|----------------------|
| **Throughput** | Highest | High | Very High |
| **Memory Efficiency** | Best (PagedAttention) | Good | Good |
| **Setup Complexity** | Low | Low | High |
| **Model Support** | 100+ | 50+ | Limited |
| **Quantization** | AWQ, GPTQ, SqueezeLLM | GPTQ, AWQ | INT8, FP8 |
| **Multi-GPU** | Tensor parallelism | Limited | Pipeline + Tensor |
| **OpenAI API** | Native | Native | Via adapter |
| **Best For** | Most use cases | HF ecosystem | Maximum perf |

### When to Choose vLLM

**Choose vLLM when:**
- You need maximum throughput on limited GPUs
- You want OpenAI-compatible API
- You're serving many concurrent users
- You need prefix caching (chatbots)
- You want simple deployment

**Consider alternatives when:**
- You need absolute minimum latency (TensorRT-LLM)
- You're already deep in HuggingFace ecosystem (TGI)
- You need very specific optimizations (custom solutions)

---

## Monitoring vLLM

### Prometheus Metrics

vLLM exposes metrics at `/metrics`:

```yaml
# ServiceMonitor for Prometheus
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: vllm-metrics
  namespace: llm-serving
spec:
  selector:
    matchLabels:
      app: vllm-mistral
  endpoints:
  - port: http
    path: /metrics
    interval: 15s
```

### Key Metrics

| Metric | Description |
|--------|-------------|
| `vllm:num_requests_running` | Currently processing requests |
| `vllm:num_requests_waiting` | Queued requests |
| `vllm:gpu_cache_usage_perc` | KV cache utilization |
| `vllm:avg_generation_throughput_toks_per_s` | Token generation speed |
| `vllm:avg_prompt_throughput_toks_per_s` | Prompt processing speed |
| `vllm:time_to_first_token_seconds` | TTFT latency |
| `vllm:time_per_output_token_seconds` | Per-token latency |

### Grafana Dashboard Queries

```promql
# Throughput (tokens per second)
rate(vllm:avg_generation_throughput_toks_per_s[5m])

# Queue depth
vllm:num_requests_waiting

# GPU KV cache utilization
vllm:gpu_cache_usage_perc

# P99 time to first token
histogram_quantile(0.99, rate(vllm:time_to_first_token_seconds_bucket[5m]))
```

---

## Scaling vLLM on Kubernetes

### Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: vllm-hpa
  namespace: llm-serving
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: vllm-mistral
  minReplicas: 1
  maxReplicas: 4
  metrics:
  - type: Pods
    pods:
      metric:
        name: vllm_num_requests_waiting
      target:
        type: AverageValue
        averageValue: "10"  # Scale when queue > 10
```

### Multi-Model Deployment

```yaml
# Deploy multiple models with different resource profiles
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vllm-mistral-7b
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: vllm
        args:
        - --model
        - mistralai/Mistral-7B-Instruct-v0.2
        resources:
          limits:
            nvidia.com/gpu: "1"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vllm-llama-70b
spec:
  replicas: 1
  template:
    spec:
      containers:
      - name: vllm
        args:
        - --model
        - meta-llama/Llama-2-70b-chat-hf
        - --tensor-parallel-size
        - "4"
        resources:
          limits:
            nvidia.com/gpu: "4"  # Needs 4 GPUs
```

---

## War Story: The GPU Cost Disaster

A startup building an AI writing assistant was spending $180K/month on GPU costs. They were using naive Hugging Face transformers inference:

**The Setup**:
- Model: Llama-2-13B
- Traffic: 50K requests/day
- Infrastructure: 8x A100-40GB GPUs on AWS
- Approach: One model instance per GPU

**The Problems**:
- GPU utilization: ~15% (waiting on I/O most of the time)
- Max concurrent users: 8 (one per GPU)
- Average latency: 8 seconds
- Cost per inference: $0.04

**The vLLM Migration**:

```bash
# Before: 8 separate model instances
# Each serving 1 request at a time

# After: 2 vLLM instances, each on 4 GPUs
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-2-13b-chat-hf \
    --tensor-parallel-size 4 \
    --max-num-seqs 128 \
    --gpu-memory-utilization 0.90
```

**The Results**:
- GPU utilization: ~85%
- Max concurrent users: 256 (128 per instance)
- Average latency: 1.2 seconds
- Cost per inference: $0.006

**Monthly savings: $155K**

The key insights:
1. Continuous batching dramatically improved throughput
2. PagedAttention allowed 16x more concurrent requests
3. Tensor parallelism gave better latency than separate instances
4. Proper memory configuration was crucial

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Not setting `--gpu-memory-utilization` | Wasted GPU memory | Set to 0.85-0.95 based on model |
| Wrong `--tensor-parallel-size` | OOM or wasted GPUs | Match to model size requirements |
| Missing `/dev/shm` mount | Crashes under load | Mount emptyDir with memory medium |
| Not caching model weights | Slow pod restarts | Use PVC for HuggingFace cache |
| Ignoring `--max-model-len` | Memory issues | Set based on your use case |
| Single replica only | No fault tolerance | Run 2+ replicas with load balancer |

---

## Hands-On Exercise: Deploy vLLM for a Chatbot

**Objective**: Deploy vLLM on Kubernetes and build a simple chatbot interface.

### Prerequisites

- Kubernetes cluster with GPU nodes
- NVIDIA GPU Operator installed
- At least 1 GPU with 16GB+ VRAM

### Task 1: Deploy vLLM

```bash
# Create namespace
kubectl create namespace llm-demo

# Create HuggingFace token secret (if using gated models)
kubectl create secret generic hf-token \
    -n llm-demo \
    --from-literal=token=hf_YOUR_TOKEN_HERE

# Deploy vLLM
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vllm-server
  namespace: llm-demo
spec:
  replicas: 1
  selector:
    matchLabels:
      app: vllm
  template:
    metadata:
      labels:
        app: vllm
    spec:
      containers:
      - name: vllm
        image: vllm/vllm-openai:latest
        args:
        - --model
        - microsoft/phi-2  # Small model for demo
        - --max-model-len
        - "2048"
        ports:
        - containerPort: 8000
        resources:
          limits:
            nvidia.com/gpu: "1"
        volumeMounts:
        - name: shm
          mountPath: /dev/shm
      volumes:
      - name: shm
        emptyDir:
          medium: Memory
          sizeLimit: "8Gi"
---
apiVersion: v1
kind: Service
metadata:
  name: vllm-server
  namespace: llm-demo
spec:
  selector:
    app: vllm
  ports:
  - port: 8000
EOF

# Wait for deployment
kubectl wait --for=condition=ready pod -l app=vllm -n llm-demo --timeout=300s
```

### Task 2: Test the API

```bash
# Port forward
kubectl port-forward -n llm-demo svc/vllm-server 8000:8000 &

# Test completion
curl http://localhost:8000/v1/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "microsoft/phi-2",
        "prompt": "Kubernetes is",
        "max_tokens": 50
    }'
```

### Task 3: Build a Simple Chatbot

```python
# chatbot.py
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="not-needed"
)

print("Chatbot ready! Type 'quit' to exit.\n")

messages = [
    {"role": "system", "content": "You are a helpful Kubernetes expert."}
]

while True:
    user_input = input("You: ")
    if user_input.lower() == 'quit':
        break

    messages.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model="microsoft/phi-2",
        messages=messages,
        max_tokens=200,
        temperature=0.7
    )

    assistant_message = response.choices[0].message.content
    messages.append({"role": "assistant", "content": assistant_message})

    print(f"\nAssistant: {assistant_message}\n")
```

```bash
# Run chatbot
python chatbot.py
```

### Task 4: Monitor Performance

```bash
# Check metrics
curl http://localhost:8000/metrics | grep vllm

# Observe key metrics:
# - vllm:num_requests_running
# - vllm:gpu_cache_usage_perc
# - vllm:avg_generation_throughput_toks_per_s
```

### Task 5: Load Test

```python
# load_test.py
import asyncio
import aiohttp
import time

async def send_request(session, prompt):
    start = time.time()
    async with session.post(
        "http://localhost:8000/v1/completions",
        json={
            "model": "microsoft/phi-2",
            "prompt": prompt,
            "max_tokens": 100
        }
    ) as response:
        await response.json()
        return time.time() - start

async def main():
    prompts = [f"Explain Kubernetes concept #{i}" for i in range(20)]

    async with aiohttp.ClientSession() as session:
        start = time.time()
        tasks = [send_request(session, p) for p in prompts]
        latencies = await asyncio.gather(*tasks)
        total_time = time.time() - start

    print(f"Total requests: {len(prompts)}")
    print(f"Total time: {total_time:.2f}s")
    print(f"Throughput: {len(prompts)/total_time:.2f} req/s")
    print(f"Avg latency: {sum(latencies)/len(latencies):.2f}s")
    print(f"P99 latency: {sorted(latencies)[int(len(latencies)*0.99)]:.2f}s")

asyncio.run(main())
```

### Success Criteria

- [ ] vLLM server is running on Kubernetes
- [ ] Can make completion requests via API
- [ ] Chatbot maintains conversation context
- [ ] Can observe metrics showing batching behavior
- [ ] Load test shows concurrent request handling

### Cleanup

```bash
kubectl delete namespace llm-demo
```

---

## Quiz

### Question 1
What is PagedAttention and why is it important?

<details>
<summary>Show Answer</summary>

**PagedAttention manages KV cache memory in fixed-size pages (like OS virtual memory)**

Traditional LLM serving allocates maximum possible memory for each request upfront. PagedAttention allocates memory on-demand in pages, allowing much higher concurrency because memory isn't wasted on incomplete sequences.
</details>

### Question 2
What does `--tensor-parallel-size` control?

<details>
<summary>Show Answer</summary>

**The number of GPUs to shard the model across**

Tensor parallelism splits model layers across multiple GPUs, allowing you to serve models that don't fit on a single GPU. A 70B model might need TP=4 to fit on A100-40GB GPUs.
</details>

### Question 3
What is continuous batching in vLLM?

<details>
<summary>Show Answer</summary>

**Processing new requests immediately without waiting for existing batches to complete**

Unlike static batching where you wait for all requests in a batch to finish, continuous batching adds new requests to the GPU as soon as capacity is available. This dramatically improves throughput.
</details>

### Question 4
What is the benefit of prefix caching?

<details>
<summary>Show Answer</summary>

**Reusing KV cache for common prompt prefixes across requests**

When multiple requests share the same system prompt or chat history prefix, vLLM can cache and reuse the KV cache for that prefix. This makes responses 30-50% faster for chatbot use cases.
</details>

### Question 5
What does `--gpu-memory-utilization` control?

<details>
<summary>Show Answer</summary>

**The percentage of GPU memory vLLM can use for the KV cache**

Higher values (0.90-0.95) allow more concurrent requests but leave less room for the model weights and compute. Default is 0.90.
</details>

### Question 6
Why is `/dev/shm` important for vLLM?

<details>
<summary>Show Answer</summary>

**vLLM uses shared memory for inter-process communication**

Without adequate shared memory, vLLM can crash under load. Mount an emptyDir with `medium: Memory` to provide enough shared memory.
</details>

### Question 7
How does vLLM achieve 24x throughput improvement?

<details>
<summary>Show Answer</summary>

**Combination of PagedAttention, continuous batching, and optimized CUDA kernels**

PagedAttention eliminates memory waste, continuous batching keeps GPUs busy, and custom kernels minimize overhead. Together these achieve dramatic improvements over naive serving.
</details>

### Question 8
What metric indicates vLLM needs more replicas?

<details>
<summary>Show Answer</summary>

**`vllm:num_requests_waiting` (queue depth)**

When this metric is consistently high, requests are waiting in queue, indicating the need for more replicas or larger batch sizes.
</details>

---

## Key Takeaways

1. **PagedAttention is the key innovation** - memory management like an OS
2. **Continuous batching maximizes GPU utilization** - no waiting for slow requests
3. **Tensor parallelism enables large models** - shard across GPUs
4. **Prefix caching accelerates chatbots** - reuse common prompt KV cache
5. **OpenAI-compatible API** - easy migration from OpenAI
6. **Memory configuration matters** - tune `--gpu-memory-utilization`
7. **Monitor queue depth** - key scaling metric
8. **Mount `/dev/shm`** - required for stability
9. **Cache model weights** - faster pod restarts
10. **2-24x improvement is real** - benchmark your use case

---

## Further Reading

- [vLLM Documentation](https://docs.vllm.ai/) - Official guides
- [PagedAttention Paper](https://arxiv.org/abs/2309.06180) - Technical details
- [vLLM GitHub](https://github.com/vllm-project/vllm) - Source and issues
- [Supported Models](https://docs.vllm.ai/en/latest/models/supported_models.html) - Full model list

---

## Next Module

Continue to [Module 9.5: Ray Serve](../module-9.5-ray-serve/) to learn about distributed inference and scaling LLM serving across multiple nodes.

---
title: "Private LLM Serving"
description: "Deploy, scale, and optimize large language models on bare-metal Kubernetes using vLLM, TGI, and KServe."
slug: on-premises/ai-ml-infrastructure/module-9.3-private-llm-serving
sidebar:
  order: 93
---

# Private LLM Serving

Operating Large Language Models (LLMs) on bare-metal Kubernetes shifts the operational bottleneck from CPU and network I/O to GPU memory bandwidth and interconnect speed. Private LLM serving requires specialized inference engines capable of managing the KV cache, batching requests dynamically, and handling asynchronous token streaming. 

This module covers the operational primitives for serving open-weights models (Llama 3, Mixtral, Qwen) on proprietary infrastructure using engines like vLLM and Text Generation Inference (TGI), wrapped in orchestrators like KServe.

## Learning Outcomes

* Deploy and configure vLLM and Text Generation Inference (TGI) as containerized workloads on bare-metal Kubernetes.
* Configure continuous batching and PagedAttention to maximize GPU memory utilization and token throughput.
* Compare and implement quantization formats (AWQ, GPTQ, FP8) to fit models into memory-constrained GPU environments.
* Architect autoscaling inference workloads using KServe, Knative, and custom Prometheus metrics (e.g., KV cache usage, queue length).
* Diagnose GPU out-of-memory (OOM) errors and optimize model parallel execution across multiple GPUs using Tensor Parallelism.

## The Physics of LLM Inference

LLM inference consists of two distinct phases. Understanding these phases is critical for tuning deployment manifests.

1. **Prefill Phase (Time to First Token - TTFT):** The model processes the input prompt all at once. This phase is heavily **compute-bound**. The GPU matrix multiplication units (Tensor Cores) are fully saturated.
2. **Decode Phase (Time Per Output Token - TPOT):** The model generates tokens one by one autoregressively. Each new token requires reading the entire model weights and the attention KV cache from GPU High Bandwidth Memory (HBM) into the compute cores. This phase is heavily **memory-bandwidth-bound**.

Because the decode phase underutilizes compute but maxes out memory bandwidth, serving a single request sequentially is highly inefficient. Inference engines group multiple requests together (batching) to read the model weights once and apply them to multiple sequences simultaneously.

### Continuous Batching and PagedAttention

Traditional static batching required all requests in a batch to finish before a new batch could start, leading to wasted cycles when sequence lengths varied. Modern inference relies on **Continuous Batching** (also known as in-flight batching). As soon as one sequence in a batch emits its end-of-sequence (EOS) token, a new prompt from the queue is immediately swapped into the batch.

> **Stop and think**: If continuous batching allows sequences to be swapped out dynamically, how does the engine keep track of the attention state for an incomplete sequence without running out of memory?

To support continuous batching without memory fragmentation, engines use **PagedAttention**. Similar to operating system virtual memory, PagedAttention divides the KV cache into fixed-size blocks (pages). 

> **Pause and predict**: If you allocate nearly 100% of your GPU memory to the KV cache, what will happen when PyTorch tries to initialize its CUDA context?

:::note
When configuring vLLM, the `gpu-memory-utilization` flag (default `0.9`) reserves a block of GPU HBM upfront for the KV cache. If you set this too high on a shared GPU, the PyTorch context initialization will OOM. If you set it too low, your batch sizes will be artificially constrained, tanking throughput.
:::

## Inference Engine Landscape

Selecting the right engine dictates your container configuration, available metrics, and hardware utilization limits.

| Feature / Engine | vLLM | Text Generation Inference (TGI) | Ollama |
| :--- | :--- | :--- | :--- |
| **Primary Use Case** | High-throughput production serving | Production serving (Hugging Face ecosystem) | Local dev, edge, simple low-scale deployments |
| **KV Cache Mgmt** | PagedAttention | PagedAttention | Static / Basic |
| **Quantization** | AWQ, GPTQ, FP8, Marlin | AWQ, GPTQ, EETQ, BitsAndBytes | GGUF |
| **API Format** | OpenAI Compatible API | Custom REST, OpenAI wrapper available | Custom REST, OpenAI compatible API |
| **Multi-GPU** | Tensor Parallelism (Ray/NCCL) | Tensor Parallelism (NCCL) | Limited/Basic |
| **Metrics** | Prometheus endpoint built-in | Prometheus endpoint built-in | None native (requires exporters) |

For bare-metal production, **vLLM** and **TGI** are the standard choices. vLLM (especially from v0.10.0 onwards) highlights advanced throughput features like chunked prefill, speculative decoding, and robust PagedAttention. Both engines natively support the OpenAI API format (e.g., TGI v1.4.0+ introduced an OpenAI-compatible Messages API, and vLLM provides fully compliant Chat and Completions endpoints), making them drop-in replacements for cloud APIs.

Commercial alternatives like **NVIDIA NIM LLM 1.14.0+** (which adds native tool calling, thinking budget controls, and observability) or the **NVIDIA Triton Inference Server** (which wraps both TRT-LLM and vLLM backends) are also commonly deployed via Helm or operators in enterprise Kubernetes environments.

### Multi-GPU Scaling: Tensor Parallelism vs. Pipeline Parallelism

When a model's weights exceed the memory of a single GPU (e.g., a 70B parameter model in FP16 requires ~140GB of VRAM, exceeding an 80GB A100), the model must be split.

* **Tensor Parallelism (TP):** Slices individual matrix operations across multiple GPUs. Requires high-bandwidth interconnects (NVLink) between GPUs. In Kubernetes, this means the GPUs *must* reside on the same physical node. Configured via `--tensor-parallel-size` in vLLM.
* **Pipeline Parallelism (PP):** Slices the model by layers (e.g., layers 1-40 on GPU 1, 41-80 on GPU 2). Can span across nodes via network interfaces, but introduces pipeline bubbles (idle time). Configured via `--pipeline-parallel-size`.

## Quantization Strategies for Bare Metal

If you cannot afford 8xH100 nodes, quantization is your primary lever. It reduces the precision of the model weights, slashing VRAM requirements and increasing memory bandwidth efficiency (which speeds up the decode phase).

1. **FP16 / BF16:** Unquantized baseline. Safe, zero degradation.
2. **AWQ (Activation-aware Weight Quantization):** 4-bit weight quantization. Excellent balance of speed and VRAM reduction with negligible perplexity degradation. **Highly recommended for vLLM.**
3. **GPTQ:** An older 4-bit weight quantization method. Slightly slower decode speeds compared to AWQ on modern kernels.
4. **FP8:** The emerging standard for Hopper (H100) architecture. Requires hardware support but offers the best throughput without the calibration overhead of AWQ/GPTQ.
5. **GGUF:** Used primarily by `llama.cpp` and Ollama. Heavily optimized for CPU and Apple Silicon, but less performant for high-batch GPU serving compared to AWQ/FP8 on vLLM.

:::caution
Do not use `BitsAndBytes` (LLM.int8()) for production serving. It is designed for training (LoRA fine-tuning) and its inference kernels are slow, leading to high latency. Use AWQ or GPTQ pre-quantized models instead.
:::

## Orchestrating with KServe

Running raw Deployments of vLLM works, but managing autoscaling based on hardware metrics and routing traffic to specific model versions becomes complex. **KServe** (accepted as a CNCF incubating project in late 2025) is built around Kubernetes controllers and Custom Resource Definitions (CRDs) to standardize model serving.

KServe relies on Knative Serving for scale-to-zero and request-based autoscaling, and integrates natively with Istio or the Kubernetes Gateway API (supported as of KServe v0.15). For Hugging Face models, KServe's LLM runtime defaults to the vLLM backend, exposing an OpenAI-compatible generative endpoint using a route-prefix style integration (e.g., under `/openai/v1/`).

> **Stop and think**: How do you autoscale a pod that deliberately consumes nearly 100% of its memory allocation upon startup?

:::caution
If you are deploying multi-node, multi-GPU Hugging Face vLLM workloads in KServe v0.15+, note that this functionality is limited to `RawDeployment` mode, which explicitly disables Knative's scale-to-zero autoscaling capabilities.
:::

```mermaid
graph TD
    User[Client Application] -->|HTTP /v1/chat/completions| Gateway[Istio Ingress Gateway]
    Gateway --> KubeProxy[Knative Activator / Autoscaler]
    KubeProxy --> KServe[KServe InferenceService]
    KServe --> Pod1[vLLM Pod - GPU 0]
    KServe --> Pod2[vLLM Pod - GPU 1]
    
    subgraph Kubernetes Node
        Pod1 --> GPU1[NVIDIA A100]
        Pod2 --> GPU2[NVIDIA A100]
    end
```

### Autoscaling Metrics

CPU and Memory metrics are useless for LLM autoscaling. LLM containers allocate all available VRAM at startup (due to PagedAttention) and often peg the CPU handling the event loop.

You must scale on:
1. **Concurrency/Queue Length:** The number of pending requests waiting in the vLLM scheduler queue. If the queue length exceeds a threshold (e.g., 50), trigger a scale-up.
2. **KV Cache Utilization:** Exposed by vLLM as `vllm:gpu_cache_usage_perc`. If cache usage stays >90%, the node is thrashing and dropping requests; scale up.

KServe abstracts this by hooking into Knative's concurrency metrics.

## Hands-on Lab: Deploying a Quantized Model with vLLM

In this lab, we will deploy a 4-bit AWQ quantized Llama 3 8B model using vLLM on a Kubernetes node with an NVIDIA GPU.

### Prerequisites

* A Kubernetes cluster (v1.35+ recommended, where Dynamic Resource Allocation for GPUs is fully stable, though traditional extended resources are still widely used). GPU scheduling via device plugins has been stable since v1.26.
* The **NVIDIA GPU Operator** installed. This operator automates the deployment of essential components including the NVIDIA drivers, the Kubernetes device plugin, the NVIDIA Container Toolkit, GFD, and DCGM for exporting GPU telemetry.
* At least one node with 1x NVIDIA GPU (T4, A10g, A100, etc.) having a minimum of 16GB VRAM.
* `kubectl` configured.

### Step 1: Create the vLLM Deployment

We will deploy vLLM, instructing it to download the `casperhansen/llama-3-8b-instruct-awq` model directly from the Hugging Face Hub. Note how the NVIDIA GPU is requested as an extended resource (`nvidia.com/gpu`).

Create a file named `vllm-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vllm-llama3-8b
  namespace: default
  labels:
    app: vllm
spec:
  replicas: 1
  selector:
    matchLabels:
      app: vllm
  template:
    metadata:
      labels:
        app: vllm
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
    spec:
      containers:
      - name: vllm
        image: vllm/vllm-openai:v0.5.0.post1
        command: ["python3", "-m", "vllm.entrypoints.openai.api_server"]
        args:
        - "--model"
        - "casperhansen/llama-3-8b-instruct-awq"
        - "--quantization"
        - "awq"
        - "--gpu-memory-utilization"
        - "0.85"
        - "--max-model-len"
        - "4096"
        - "--port"
        - "8000"
        env:
        - name: HUGGING_FACE_HUB_TOKEN
          valueFrom:
            secretKeyRef:
              name: hf-token-secret
              key: token
              optional: true # Only needed for gated models
        ports:
        - containerPort: 8000
          name: http
        resources:
          limits:
            nvidia.com/gpu: "1"
            memory: "32Gi"
            cpu: "4"
          requests:
            nvidia.com/gpu: "1"
            memory: "16Gi"
            cpu: "2"
        volumeMounts:
        - mountPath: /root/.cache/huggingface
          name: cache-volume
        - mountPath: /dev/shm
          name: dshm
      volumes:
      - name: cache-volume
        emptyDir: {}
      - name: dshm
        emptyDir:
          medium: Memory
          sizeLimit: 2Gi
```

:::tip
**Why `/dev/shm`?**
PyTorch uses shared memory for inter-process communication, especially when using Tensor Parallelism (NCCL). The default Kubernetes Docker/containerd shm size is 64MB, which will cause NCCL to crash under load. Always mount a memory-backed `emptyDir` to `/dev/shm` with at least 2Gi for LLM workloads.
:::

Apply the deployment:

```bash
kubectl apply -f vllm-deployment.yaml
```

### Step 2: Create the Service

Expose the deployment internally within the cluster.

```yaml
# vllm-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: vllm-service
  namespace: default
spec:
  selector:
    app: vllm
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
```

```bash
kubectl apply -f vllm-service.yaml
```

### Step 3: Verify the Deployment

Downloading the model weights (approx 5-6GB for a 4-bit 8B model) takes time. Watch the logs to verify the engine starts successfully.

```bash
# Check pod status
kubectl get pods -l app=vllm

# Follow logs
kubectl logs -f deployment/vllm-llama3-8b
```

You are looking for a log line indicating the server is ready, such as:
`INFO 06-12 10:45:12 api_server.py:122] Uvicorn running on http://0.0.0.0:8000`

### Step 4: Test the OpenAI-Compatible Endpoint

Port-forward the service to your local machine:

```bash
kubectl port-forward svc/vllm-service 8080:80
```

In a new terminal, send a request using `curl` formatted exactly like an OpenAI API call:

```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "casperhansen/llama-3-8b-instruct-awq",
    "messages": [
      {"role": "system", "content": "You are a Kubernetes expert."},
      {"role": "user", "content": "Explain what a DaemonSet is in one sentence."}
    ],
    "max_tokens": 100,
    "temperature": 0.2
  }'
```

**Expected Output:**
A JSON response containing the generated text within the `choices[0].message.content` field.

### Troubleshooting the Lab

* **Pod stuck in `Pending`:** You likely do not have a node with `nvidia.com/gpu` available, or the NVIDIA device plugin is crashing. Run `kubectl describe pod <pod-name>`.
* **Container restarts with OOMKilled:** The node does not have enough system memory (RAM), OR the GPU VRAM is exhausted during weight loading. Lower `--gpu-memory-utilization` to `0.7` or check `dmesg` on the node.
* **Hugging Face 401 Unauthorized:** If using a gated model (like official Meta Llama weights), you must create a secret `hf-token-secret` containing your Hugging Face access token and ensure you have accepted the license agreement on the Hugging Face website.

## Practitioner Gotchas

### 1. The NCCL Timeout Crash
**Context:** When scaling vLLM across multiple GPUs using `--tensor-parallel-size > 1`, the NVIDIA Collective Communications Library (NCCL) is used to synchronize the GPUs.
**Gotcha:** If a network blip occurs or CPU contention delays a synchronization step, NCCL times out and crashes the entire pod.
**Fix:** Set the environment variable `NCCL_TIMEOUT=120` (or higher) to prevent transient latency spikes from killing the serving container. Ensure `hostIPC: true` is set on the pod spec for multi-GPU communication if not relying solely on shared memory volumes.

### 2. Context Length OOMs
**Context:** You deploy a model with a theoretical context length of 128k tokens. You test it with a 100-token prompt, and it works flawlessly.
**Gotcha:** A user submits an 80k token prompt. The KV cache allocation immediately attempts to reserve massive contiguous blocks of memory, exhausting VRAM and crashing the inference engine.
**Fix:** Hard-cap the maximum context length at the engine level using `--max-model-len`. Do not trust the model's theoretical maximum; calculate what fits in your remaining VRAM after weights are loaded, and clamp the API to that limit.

### 3. Starving the CPU Scheduler
**Context:** GPU inference is fast, but the event loop handling HTTP requests, tokenizing text, and scheduling batches runs on the CPU.
**Gotcha:** If you assign `cpu: 1` to a vLLM pod handling 500 requests/sec, the GPU will idle because the CPU cannot tokenize prompts fast enough to feed it.
**Fix:** Inference is not solely a GPU problem. Provision ample CPU limits (e.g., `cpu: 8` or `cpu: 16` for high-throughput nodes) to ensure the Python event loops and tokenizer libraries can keep the GPU saturated.

### 4. Head-of-Line Blocking with Mixed Workloads
**Context:** You serve both real-time chat requests (short prompts, short output) and background document summarization (massive prompts, long output) on the same vLLM endpoint.
**Gotcha:** The long summarization requests consume all available KV cache blocks. The continuous batching scheduler cannot accept the small chat requests until the summaries finish, causing chat latency to spike from 200ms to 45 seconds.
**Fix:** Segregate workloads. Deploy two separate KServe InferenceServices—one dedicated to low-latency chat, and one configured with high batch sizes and lower priority for background processing.

## Quiz

**1. You are running a 70B parameter model utilizing Tensor Parallelism across 4 GPUs on a single bare-metal Kubernetes node. The pod crashes randomly under heavy load. The logs show NCCL synchronization timeouts and failures. Which configuration change is the most appropriate first step?**
- A) Switch from Tensor Parallelism to Pipeline Parallelism to avoid NCCL.
- B) Decrease `--gpu-memory-utilization` to free up VRAM for NCCL.
- C) Ensure an `emptyDir` backed by memory is mounted to `/dev/shm` with sufficient size (e.g., 2Gi).
- D) Increase the Knative scale-up concurrency threshold.

<details>
<summary>Answer</summary>
**Correct Answer: C**

When using Tensor Parallelism across multiple GPUs on the same node, the NVIDIA Collective Communications Library (NCCL) is responsible for synchronizing the matrix math between the GPUs. NCCL relies heavily on the operating system's shared memory space (`/dev/shm`) for this high-speed inter-process communication. The default Kubernetes container runtime configuration provisions a very small shared memory segment (usually only 64MB). Under heavy inference load, this tiny segment quickly fills up, causing NCCL processes to timeout or crash, which brings down the entire pod. Mounting a memory-backed `emptyDir` to `/dev/shm` gives NCCL the headroom it needs to synchronize efficiently.
</details>

**2. Your production vLLM instance is experiencing increased latency during peak hours. You need to configure KServe's autoscaler to spin up additional replicas before the current pods become overwhelmed. Which metric is the most reliable indicator that your vLLM deployment needs to scale out?**
- A) The container's CPU utilization exceeds 85%.
- B) The `vllm:gpu_cache_usage_perc` is sustained above 90% and the scheduler queue is growing.
- C) The container's Memory (RAM) utilization hits the Kubernetes limit.
- D) The GPU core temperature exceeds 80°C.

<details>
<summary>Answer</summary>
**Correct Answer: B**

Because LLM engines like vLLM pre-allocate a massive block of GPU VRAM at startup for the KV cache (using PagedAttention), traditional memory utilization metrics will always report near 100% usage regardless of actual load. Similarly, CPU usage is not strongly correlated with GPU capacity or sequence throughput. The true bottleneck for an LLM server is the availability of KV cache blocks; when the cache is nearly full (above 90%), the engine cannot process new requests and must place them in a pending queue. Scaling out based on this specific KV cache utilization metric, along with concurrency or queue length, ensures that new pods are ready before the existing ones begin dropping requests.
</details>

**3. A platform engineering team is provisioning hardware for a new internal AI assistant. They want to maximize token throughput on A100 GPUs, but the requested 70B parameter model weights are slightly too large to fit in the VRAM alongside a reasonably sized KV cache. Which quantization strategy should they adopt to ensure the model fits without crippling production decode speeds?**
- A) BitsAndBytes (LLM.int8())
- B) AWQ (Activation-aware Weight Quantization)
- C) GGUF
- D) Dynamic FP32 scaling

<details>
<summary>Answer</summary>
**Correct Answer: B**

Activation-aware Weight Quantization (AWQ) provides an excellent 4-bit weight quantization format that is specifically optimized for high-throughput GPU serving in engines like vLLM. It significantly reduces the VRAM required to load the model weights, leaving more memory available for the KV cache to support larger continuous batches. While BitsAndBytes is easy to use for local testing or LoRA fine-tuning, its inference kernels are notoriously slow and not suitable for production serving. GGUF is a fantastic format, but it is primarily optimized for CPU and Apple Silicon execution, lacking the raw data-center GPU performance of AWQ or FP8 on modern NVIDIA hardware.
</details>

**4. You are migrating an internal chatbot from a legacy static batching inference server to a modern vLLM deployment. The primary motivation for this migration is to improve hardware utilization. What is the operational advantage that Continuous Batching (and PagedAttention) provides over your legacy system?**
- A) It allows the model weights to be paged out to the node's system RAM when not actively in use by a request.
- B) It prevents the need to calculate the expensive attention mechanism entirely during the prefill phase.
- C) It allows new requests to be dynamically inserted into an active batch as soon as another sequence finishes, preventing idle GPU cycles.
- D) It automatically shards the model across multiple Kubernetes nodes without requiring an external orchestrator like KServe.

<details>
<summary>Answer</summary>
**Correct Answer: C**

In a legacy static batching system, the inference engine must wait for all sequences in a given batch to complete before it can process a new batch. If one prompt requires a 100-token response and another requires 1,000 tokens, the GPU spends a massive amount of time sitting idle waiting for the longer sequence to finish. Continuous batching solves this fragmentation by dynamically swapping sequences in and out at the token level; the moment a short request finishes, a new request is pulled from the queue and injected into the active batch. This drastically increases overall token throughput and ensures the GPU's memory bandwidth is constantly saturated.
</details>

**5. You configure a new vLLM Deployment manifest with the argument `--gpu-memory-utilization 0.99` to maximize the available space for your KV cache. Upon applying the manifest, the pod immediately crashes with an `OOMKilled` error before accepting any HTTP requests. What is the most likely cause of this failure?**
- A) The Kubernetes node ran out of physical CPU cores required to run the Python event loop.
- B) Reserving 99% of the VRAM for the KV cache leaves insufficient memory for PyTorch context initialization and essential CUDA kernels.
- C) The Hugging Face container cache failed to mount, causing the weights to overflow into the container's root filesystem.
- D) The KServe Knative autoscaler attempted to inject an overly large batch immediately upon startup.

<details>
<summary>Answer</summary>
**Correct Answer: B**

The `--gpu-memory-utilization` flag in vLLM dictates the percentage of total available GPU VRAM that the engine will allocate completely upfront to hold the model weights and the PagedAttention KV cache. If you set this value too high (like 0.99), the engine reserves nearly all the physical memory on the card. However, the underlying PyTorch runtime, the NVIDIA Collective Communications Library (NCCL), and the CUDA context itself all require a baseline amount of unreserved VRAM just to initialize and execute operations. By starving the runtime of this required overhead memory, PyTorch immediately crashes with a CUDA Out Of Memory error before the server can even begin listening for requests.
</details>

## Further Reading

* [vLLM Official Documentation - Architecture and PagedAttention](https://docs.vllm.ai/en/latest/models/engine_args.html)
* [Text Generation Inference (TGI) GitHub Repository](https://github.com/huggingface/text-generation-inference)
* [KServe Documentation - Autoscaling and Knative Integration](https://kserve.github.io/website/latest/modelserving/autoscaling/autoscaling/)
* [Understanding Tensor Parallelism in LLM Inference (Hugging Face Blog)](https://huggingface.co/blog/inference-endpoints-llm)
* [AWQ: Activation-aware Weight Quantization for LLM Compression and Acceleration (Research Paper)](https://arxiv.org/abs/2306.00978)
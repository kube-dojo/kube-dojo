---
citations_verified: true
title: "Module 9.4: vLLM - High-Throughput LLM Serving"
slug: platform/toolkits/data-ai-platforms/ml-platforms/module-9.4-vllm
sidebar:
  order: 5
---

## Complexity: `[COMPLEX]`

**Time to Complete**: 90 minutes  
**Prerequisites**: Module 9.1 (Kubeflow basics), Kubernetes GPU scheduling basics, transformer inference basics, and comfort reading Prometheus metrics  
**Track**: Platform Toolkits / Data and AI Platforms / ML Platforms

## Learning Outcomes

After completing this module, you will be able to:

- **Design** a vLLM serving deployment that matches model size, GPU memory, concurrency, context length, and user latency requirements.
- **Debug** common vLLM failures on Kubernetes by connecting symptoms to scheduler pressure, KV cache exhaustion, shared memory limits, and GPU placement.
- **Evaluate** when vLLM is a better fit than managed APIs, Hugging Face TGI, or TensorRT-LLM for a production inference workload.
- **Configure** batching, tensor parallelism, prefix caching, model storage, and monitoring so a vLLM service can survive real traffic patterns.
- **Interpret** vLLM metrics to decide whether to tune a single replica, add replicas, reduce context length, or split traffic across model tiers.

## Why This Module Matters

A platform team inherits an internal assistant that started as a prototype and became business critical before anyone designed the serving layer. The application team points it at a large chat model, the first launch campaign succeeds, and suddenly every slow response is visible to sales, support, and executives. GPU spend climbs faster than user growth, support tickets complain about time to first token, and on-call engineers cannot tell whether the problem is the model, the cluster, the queue, or the client.

The expensive part is not only the model weights. During generation, [every active sequence produces a key-value cache](https://arxiv.org/abs/2309.06180), usually called the KV cache, so the model can attend to previous tokens without recomputing the whole prompt each step. If the serving engine reserves too much KV cache per request, the GPU looks full even while useful compute sits idle. If the engine batches poorly, short requests wait behind long ones, and users feel the queue before the GPU ever becomes saturated.

vLLM matters because it gives platform engineers a practical serving engine for this exact failure mode. Its PagedAttention design treats KV cache memory more like paged system memory, while its scheduler continuously admits and advances requests instead of waiting for static batches to complete. That combination can turn a brittle one-request-per-worker service into a shared inference endpoint with real concurrency, observable pressure signals, and operational tuning knobs.

The senior-level lesson is that vLLM is not a magic image you deploy and forget. It is a scheduling and memory system running inside Kubernetes, so the production design still depends on GPU class, node topology, model size, context policy, request mix, cache behavior, rollout strategy, and autoscaling signals. This module teaches the mechanism first, then shows how to use that mechanism to make deployment and troubleshooting decisions.

## Core Content

### 1. Start With the Serving Problem, Not the Tool

An LLM serving system has two jobs that pull against each other. It must keep the GPU busy enough that expensive hardware is not idle, and it must give each user a response quickly enough that the product feels interactive. Traditional web scaling instincts can mislead you here because adding more pods is not the first fix when one pod is wasting most of its GPU memory.

The core pressure comes from the shape of generation. A request begins with a prompt phase, where the model processes existing input tokens, and then enters a decode phase, where it emits output tokens one step at a time. The decode phase is long, incremental, and stateful because every generated token extends the KV cache. That means the scheduler must decide which active sequences get GPU time at each step, not only which request enters the system first.

A naive server often reserves memory as though every request will use the maximum context length. That is safe in the narrow sense that the request will not outgrow its allocation, but it is wasteful in the normal case where many prompts are short or outputs finish early. The consequence is painful: the GPU reports high memory usage, the queue grows, and the operator assumes the model is too large even though the real bottleneck is allocation strategy.

```ascii
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
│  Problem: Each request reserves maximum possible memory upfront          │
│  Result: Few concurrent requests, large amounts of GPU memory wasted     │
└─────────────────────────────────────────────────────────────────────────┘
```

The diagram is simplified, but the operational signal is real. When reserved KV cache dominates available memory, increasing CPU, adding web replicas, or changing the Kubernetes Service will not solve the issue. You need a serving engine that can allocate KV cache closer to actual token growth and schedule work at token granularity.

A useful mental model is to separate three resources. Model weights are the mostly fixed memory cost of loading the model. KV cache is the variable memory cost of active requests. Compute is the GPU work needed to process prompt and decode tokens. A serving incident usually becomes clear when you decide which of those three resources is actually scarce.

| Resource | What consumes it | What pressure looks like | Typical first response |
|---|---|---|---|
| Model weight memory | Model parameters, quantization choice, tensor parallel layout | Pod fails to start or immediately hits out-of-memory during load | Use a smaller model, quantize, or increase tensor parallel size |
| KV cache memory | Active sequences, prompt length, output length, max model length | Queue grows while GPU memory is high and active sequence count is capped | Reduce context policy, tune cache utilization, or add replicas |
| GPU compute | Prompt prefill, decode steps, attention kernels, sampling | GPU utilization high, throughput flat, latency rises with traffic | Tune batching, choose faster model tier, or scale horizontally |
| CPU and host memory | Tokenization, request handling, swapping, metrics, networking | GPU not saturated while server process is slow or unstable | Increase CPU, reduce swapping, inspect server logs |
| Network path | Client streaming, ingress, service mesh, load balancer | Tokens generated but users see delayed or bursty delivery | Test direct service path, streaming behavior, and proxy buffering |

Stop and think: your team reports that `nvidia-smi` shows high memory use but only moderate GPU utilization, and the queue metric is rising. Before changing node size, decide whether the evidence points to model weight memory, KV cache memory, or compute saturation, then name one vLLM setting you would inspect first.

The first engineering decision is whether the workload is interactive, batch, or mixed. Interactive chat cares about time to first token and steady streaming, while offline summarization often cares about total tokens per second. A mixed workload is harder because long batch prompts can steal cache pages and scheduler slots from short user requests. In production, teams often separate these traffic classes before they tune more obscure parameters.

The second decision is whether the platform owns the model serving contract. If application teams need OpenAI-compatible endpoints, predictable metrics, and Kubernetes-native ownership, vLLM is often a strong fit. If the organization wants the lowest possible single-request latency on a narrow hardware and model matrix, a specialized TensorRT-LLM path may be worth the extra operational cost. If the team already standardized on Hugging Face serving and only needs moderate concurrency, TGI may be simpler.

| Workload pattern | Strong fit for vLLM? | Reasoning path |
|---|---:|---|
| Many concurrent chat requests with shared system prompts | Yes | Continuous batching and prefix reuse help keep GPU work productive |
| Low-volume internal tool with strict simplicity requirement | Maybe | A managed API or smaller single-process server may cost less operationally |
| Large model that barely fits across several GPUs | Yes | Tensor parallelism can make the model loadable, but node placement becomes critical |
| Hard real-time single-request latency target | Maybe | Specialized kernels and compiled paths may beat general-purpose serving |
| Offline batch summarization with loose latency | Yes | Throughput-oriented batching can be more important than first-token speed |
| Highly regulated environment requiring full model ownership | Yes | Self-hosting gives stronger control over data path, logs, and access policy |

The point is not that vLLM wins every comparison. The point is that vLLM gives platform teams explicit control over the resource that usually surprises them: the growing KV cache of many concurrent sequences. Once you see the workload as a memory and scheduling problem, the deployment choices become less mystical.

### 2. PagedAttention and Continuous Batching

PagedAttention is vLLM's central memory-management idea. Instead of storing each request's KV cache in one large contiguous block sized for the worst case, [vLLM divides the cache into blocks and maps logical sequence positions to physical cache blocks](https://arxiv.org/abs/2309.06180). That sounds like an implementation detail until you operate the system under bursty traffic, where the difference between reserved memory and used memory becomes the difference between rejecting users and keeping the GPU busy.

The [operating-system analogy](https://arxiv.org/abs/2309.06180) is useful but should not be pushed too far. In an OS, virtual memory lets processes see contiguous address spaces while physical pages can live in different places. In vLLM, a sequence can grow token by token while its KV cache occupies non-contiguous blocks from a shared pool. The practical result is that short requests stop paying the memory cost of long requests.

```ascii
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
│  • Memory allocated on demand per page                                  │
│  • Pages can be non-contiguous                                          │
│  • Shared prefixes can reuse pages                                      │
│  • More concurrent requests can fit in the same GPU memory budget       │
└─────────────────────────────────────────────────────────────────────────┘
```

[Continuous batching](https://raw.githubusercontent.com/vllm-project/vllm/main/README.md) complements PagedAttention. Static batching waits for a group of requests, runs them together, and often waits for the slowest sequence in the group before admitting more work. Continuous batching treats the batch as a living set of active sequences. When one sequence finishes or yields capacity, the scheduler can admit another sequence without draining the whole batch.

This matters because LLM requests vary wildly. One user asks for a one-sentence answer, another pastes a long incident report, and a third asks for generated code. If those requests are tied together in a rigid batch, short work waits behind long work. If the scheduler can continuously refill capacity, the GPU sees a more stable stream of useful tokens.

```ascii
┌─────────────────────────────────────────────────────────────────────────┐
│                 Continuous Batching Timeline                            │
│                                                                         │
│  Time ───────────────────────────────────────────────────────────────▶   │
│                                                                         │
│  Static batch:                                                           │
│  [Req A decode decode done........waits for batch drain..............]   │
│  [Req B decode decode decode decode decode done......................]   │
│  [Req C decode done..............waits for batch drain...............]   │
│  [Req D cannot enter until the whole batch completes................]   │
│                                                                         │
│  vLLM batch:                                                             │
│  [Req A decode decode done] [Req D enters decode decode decode......]   │
│  [Req B decode decode decode decode decode done] [Req E enters......]   │
│  [Req C decode done] [Req F enters decode decode....................]   │
│                                                                         │
│  Scheduler goal: keep useful token work flowing without overfilling KV   │
└─────────────────────────────────────────────────────────────────────────┘
```

Worked example: imagine a single GPU serving a support assistant, and the queue starts rising during a launch. The team sees `vllm:num_requests_running` near the configured sequence limit, `vllm:num_requests_waiting` growing, and `vllm:gpu_cache_usage_perc` close to saturation. A junior operator might immediately add another replica, which may be correct eventually, but a senior operator first asks whether each request is allowed to reserve too much context.

If the product only needs four thousand tokens of context, running the model at a much larger maximum length wastes KV cache capacity. Reducing `--max-model-len` to the product's real policy can let the same GPU admit more concurrent sequences. If the cache is still full after that, the next steps are to inspect `--gpu-memory-utilization`, `--max-num-seqs`, request length distribution, and whether long-running batch jobs belong on a separate deployment.

Here is the reasoning sequence behind that worked example. High waiting requests means demand is not entering the active set. High cache usage means active requests are consuming the limiting memory pool. Moderate GPU utilization means compute is not necessarily the first bottleneck. Those three signals together suggest a KV cache admission problem, not merely a need for faster kernels.

What would happen if the team increased `--max-num-seqs` while cache usage was already near full? The server might admit more sequences only briefly, then preempt, swap, reject, or slow down depending on configuration and workload. More concurrency is not free; it works only when memory blocks and compute steps are available to support the additional sequences.

The scheduler's behavior also explains why load tests must resemble real traffic. A test with identical short prompts may show excellent throughput because prefix behavior, prompt length, and output length are easy. A real workload with long incident reports and open-ended generation can produce a very different cache footprint. You should collect prompt tokens, output tokens, time to first token, and queue depth together, not as isolated metrics.

| Symptom | Likely bottleneck | Evidence that supports it | First investigation |
|---|---|---|---|
| Pod fails while loading model | Model weight memory | CUDA out-of-memory appears before traffic starts | Model size, dtype, quantization, tensor parallel size |
| Queue rises with high cache usage | KV cache memory | Waiting requests grow while active requests are capped | Context length, max sequences, cache utilization |
| Queue rises with high GPU utilization | Compute throughput | GPU busy, cache not full, tokens per second flat | Batch token limits, model tier, replica count |
| First token slow, later stream steady | Prompt prefill cost | Long prompts correlate with high TTFT | Prompt length policy, prefix caching, routing |
| Stream stalls after starting | Decode pressure or proxy path | TTFT acceptable, token cadence poor | Output length, decode throughput, ingress buffering |
| Restarts under load | Host or shared memory issue | Container logs mention shared memory, worker, or IPC errors | `/dev/shm`, CPU, host memory, image version |

The platform takeaway is that PagedAttention improves the memory allocator, while continuous batching improves the work scheduler. You still have to set boundaries so the allocator and scheduler are solving the right problem. Context length, batch token limits, sequence count, and traffic class are product and platform decisions, not just defaults copied from an example.

### 3. vLLM Architecture on Kubernetes

A vLLM server looks simple from the outside because it can expose [OpenAI-compatible HTTP endpoints](https://raw.githubusercontent.com/vllm-project/vllm/main/docs/serving/openai_compatible_server.md). Inside the pod, the request path crosses an API layer, scheduler, cache manager, and model executor. Kubernetes adds another set of concerns around GPU placement, model cache storage, shared memory, rollout behavior, and network routing.

```ascii
┌─────────────────────────────────────────────────────────────────────────┐
│                         vLLM Server                                     │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                    API Layer (OpenAI Compatible)                    │ │
│  │  /v1/completions    /v1/chat/completions    /v1/embeddings         │ │
│  └─────────────────────────────┬──────────────────────────────────────┘ │
│                                │                                        │
│  ┌─────────────────────────────┼──────────────────────────────────────┐ │
│  │                    Scheduler                                        │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │ │
│  │  │  Request    │  │ Continuous  │  │  Preemption │                 │ │
│  │  │  Queue      │  │  Batching   │  │  Manager    │                 │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                 │ │
│  └─────────────────────────────┬──────────────────────────────────────┘ │
│                                │                                        │
│  ┌─────────────────────────────┼──────────────────────────────────────┐ │
│  │                    PagedAttention Engine                            │ │
│  │  ┌─────────────────────────────────────────────────────────────┐    │ │
│  │  │              Block Manager (KV Cache)                        │    │ │
│  │  │  • Page allocation    • Sharing    • Swapping               │    │ │
│  │  └─────────────────────────────────────────────────────────────┘    │ │
│  └─────────────────────────────┬──────────────────────────────────────┘ │
│                                │                                        │
│  ┌─────────────────────────────┼──────────────────────────────────────┐ │
│  │                    Model Executor                                   │ │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐        │ │
│  │  │   GPU 0   │  │   GPU 1   │  │   GPU 2   │  │   GPU 3   │        │ │
│  │  │  (Shard)  │  │  (Shard)  │  │  (Shard)  │  │  (Shard)  │        │ │
│  │  └───────────┘  └───────────┘  └───────────┘  └───────────┘        │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

| Component | Role | Operational question |
|---|---|---|
| API layer | Accepts OpenAI-compatible HTTP requests and streams responses | Are clients sending supported request shapes and handling streaming correctly? |
| Scheduler | Chooses which sequences advance through prefill and decode | Is queue growth caused by too many requests, long requests, or strict limits? |
| Block manager | Allocates and releases KV cache blocks for active sequences | Is cache pressure limiting concurrency before compute is saturated? |
| Model executor | Runs model shards on one or more GPUs | Does the model fit, and are all shards placed on compatible GPUs? |
| Metrics endpoint | Exposes serving pressure and latency data | Can the platform make scaling decisions from current signals? |

The minimum Kubernetes deployment needs a GPU limit, a model name, a Service, and enough shared memory for the worker processes. A production deployment also needs node selection or affinity, model cache persistence, image pinning, probes that respect model load time, and access control in front of the OpenAI-compatible API. The examples below use Kubernetes 1.35+ resource syntax and keep the manifest intentionally explicit.

This module uses `kubectl` for the first command so the alias is clear: if your shell defines `alias k=kubectl`, the later `k` commands are equivalent. For shared curriculum examples, defining the alias in the same shell session makes the commands copy-pasteable without assuming the learner's dotfiles.

```bash
alias k=kubectl
k create namespace llm-serving
```

A small demonstration model is useful for learning the deployment mechanics, but it should not be mistaken for a production recommendation. The following manifest uses `microsoft/phi-2` because it is smaller than common production chat models and can fit in a single-GPU lab more often. In real environments, model licensing, quality, safety review, and memory sizing must happen before the deployment reaches users.

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: model-cache-pvc
  namespace: llm-serving
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 80Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vllm-phi2
  namespace: llm-serving
  labels:
    app: vllm-phi2
spec:
  replicas: 1
  selector:
    matchLabels:
      app: vllm-phi2
  template:
    metadata:
      labels:
        app: vllm-phi2
    spec:
      terminationGracePeriodSeconds: 60
      containers:
        - name: vllm
          image: vllm/vllm-openai:latest
          imagePullPolicy: IfNotPresent
          args:
            - --model
            - microsoft/phi-2
            - --host
            - 0.0.0.0
            - --port
            - "8000"
            - --max-model-len
            - "2048"
            - --gpu-memory-utilization
            - "0.88"
          ports:
            - name: http
              containerPort: 8000
          resources:
            requests:
              cpu: "4"
              memory: 24Gi
              nvidia.com/gpu: "1"
            limits:
              memory: 32Gi
              nvidia.com/gpu: "1"
          readinessProbe:
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 120
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 18
          volumeMounts:
            - name: model-cache
              mountPath: /root/.cache/huggingface
            - name: shm
              mountPath: /dev/shm
      volumes:
        - name: model-cache
          persistentVolumeClaim:
            claimName: model-cache-pvc
        - name: shm
          emptyDir:
            medium: Memory
            sizeLimit: 8Gi
---
apiVersion: v1
kind: Service
metadata:
  name: vllm-phi2
  namespace: llm-serving
  labels:
    app: vllm-phi2
spec:
  selector:
    app: vllm-phi2
  ports:
    - name: http
      port: 8000
      targetPort: http
  type: ClusterIP
```

The model cache is not a performance luxury. Without it, a restarted pod may download model weights again, which turns an ordinary rollout into a long outage or a registry-rate-limit incident. On shared clusters, a persistent cache also reduces pressure on outbound network paths and avoids repeated downloads during node churn.

The [shared memory mount](https://raw.githubusercontent.com/vllm-project/vllm/main/docs/serving/parallelism_scaling.md) is equally practical. vLLM and its worker processes can use shared memory for inter-process communication, and the default container `/dev/shm` may be too small under load. Mounting an in-memory `emptyDir` gives the pod a predictable shared memory budget, which is easier to reason about than debugging intermittent worker crashes after traffic increases.

Production placement requires more than asking for [`nvidia.com/gpu: "1"`](https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/). A model that needs tensor parallelism across four GPUs [must land on a node with four suitable GPUs](https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/) that can communicate efficiently. If the cluster mixes GPU generations, memory sizes, or Multi-Instance GPU profiles, node labels and scheduling constraints become part of the serving design.

```ascii
┌─────────────────────────────────────────────────────────────────────────┐
│                 Kubernetes Placement for vLLM                           │
│                                                                         │
│  Good placement for tensor parallel model:                              │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ node-a: same GPU type, same memory size, high-speed local links     │  │
│  │                                                                   │  │
│  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐                   │  │
│  │  │ GPU 0  │  │ GPU 1  │  │ GPU 2  │  │ GPU 3  │                   │  │
│  │  │ shard  │  │ shard  │  │ shard  │  │ shard  │                   │  │
│  │  └────────┘  └────────┘  └────────┘  └────────┘                   │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  Risky placement idea to avoid:                                         │
│                                                                         │
│  ┌────────────┐      ┌────────────┐      ┌────────────┐                 │
│  │ node-a GPU │      │ node-b GPU │      │ node-c GPU │                 │
│  │ shard 0    │      │ shard 1    │      │ shard 2    │                 │
│  └────────────┘      └────────────┘      └────────────┘                 │
│                                                                         │
│  A single vLLM tensor-parallel replica expects its GPUs in one pod.      │
└─────────────────────────────────────────────────────────────────────────┘
```

Stop and think: a four-GPU vLLM pod is pending even though the cluster has four free GPUs spread across four nodes. What Kubernetes scheduling fact explains the pending pod, and what would you change in the cluster or deployment design?

The answer is that a pod's container resource request is satisfied on a single node. A tensor-parallel vLLM replica that requests four GPUs needs one node with four allocatable GPUs, not four nodes with one GPU each. You can change the node pool, choose a smaller model, use quantization, lower tensor parallel requirements, or run multiple one-GPU replicas serving a model that fits independently.

A mature platform usually wraps this manifest with policy. It pins image versions instead of using `latest`, controls who can call the endpoint, restricts model names, defines safe context limits, and sends metrics to the common observability stack. The serving engine is only one layer; the platform product is the repeatable way teams request and operate inference endpoints.

### 4. Configuration Decisions That Change Behavior

vLLM exposes [many flags](https://raw.githubusercontent.com/vllm-project/vllm/main/vllm/engine/arg_utils.py), but most production tuning begins with a small group. The dangerous pattern is copying a command from a benchmark and applying it to a different model, GPU, and request mix. A good tuning process starts from a hypothesis, changes one control at a time, and watches metrics that correspond to the expected mechanism.

```bash
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Llama-2-70b-chat-hf \
  --host 0.0.0.0 \
  --port 8000 \
  --tensor-parallel-size 4 \
  --gpu-memory-utilization 0.90 \
  --max-num-batched-tokens 8192 \
  --max-num-seqs 128 \
  --max-model-len 4096 \
  --block-size 16 \
  --swap-space 4
```

| Parameter | What it controls | Increase when | Decrease when |
|---|---|---|---|
| `--tensor-parallel-size` | Number of GPUs used to shard a model replica | Model weights do not fit on one GPU or latency improves with sharding | Smaller model fits on one GPU and horizontal replicas are simpler |
| `--gpu-memory-utilization` | Fraction of GPU memory vLLM may reserve for execution and cache | Cache pressure blocks useful concurrency and the pod is stable | Out-of-memory, fragmentation, or other processes need memory |
| `--max-num-batched-tokens` | Token budget the scheduler may process in a batch | GPU compute is underused and cache has room | Time to first token suffers or long prompts dominate scheduling |
| `--max-num-seqs` | Maximum active sequences admitted by scheduler | Many short requests wait and cache usage is moderate | Cache is full, preemption rises, or long generations dominate |
| `--max-model-len` | Maximum context length allowed by the server | Product genuinely needs longer prompts | KV cache pressure is high and product can enforce shorter context |
| `--block-size` | Token granularity for KV cache blocks | Workload benefits from different allocation granularity after testing | Default behavior is stable and there is no measured reason to change |
| `--swap-space` | CPU swap space for KV cache pressure cases | Occasional long requests should complete instead of failing | Latency-sensitive service suffers from swapping delays |

[Tensor parallelism](https://raw.githubusercontent.com/vllm-project/vllm/main/docs/serving/parallelism_scaling.md) is the first setting many engineers meet because it decides whether a large model can load. A model with huge FP16 weights may not fit on one GPU, but sharding it across several GPUs reduces the per-GPU weight burden. The trade-off is that each inference step now requires communication among shards, so the deployment becomes sensitive to GPU topology and node shape.

```ascii
┌─────────────────────────────────────────────────────────────────────────┐
│                    Tensor Parallelism (--tensor-parallel-size)          │
│                                                                         │
│  Model Layer (for example, attention or MLP weights):                   │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                        Weight Matrix                                │ │
│  │  ┌─────────────┬─────────────┬─────────────┬─────────────┐         │ │
│  │  │   GPU 0     │    GPU 1    │    GPU 2    │    GPU 3    │         │ │
│  │  │  shard 0    │  shard 1    │  shard 2    │  shard 3    │         │ │
│  │  └─────────────┴─────────────┴─────────────┴─────────────┘         │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  Example sizing intuition:                                              │
│  - Larger dense models need multiple high-memory GPUs at FP16 or BF16    │
│  - Quantization may reduce the number of GPUs needed for model weights   │
│  - KV cache still grows with context length and active sequences         │
└─────────────────────────────────────────────────────────────────────────┘
```

A senior operator separates weight fit from traffic fit. Tensor parallelism may make the model load, but it does not automatically make the endpoint handle a launch. After loading, the remaining memory must support KV cache blocks for active requests. That is why a model can fit at startup and still fail under real traffic when the context policy is too generous.

[Quantization changes the sizing conversation](https://raw.githubusercontent.com/vllm-project/vllm/main/README.md) by reducing weight memory and sometimes improving throughput, but it is not a free switch. The model quality may shift, supported quantization formats vary by model and vLLM version, and some paths can reduce compatibility with specialized kernels. Treat quantization as a product and evaluation decision, not merely an infrastructure trick.

| Decision | Good reason to choose it | Risk to evaluate |
|---|---|---|
| Smaller model tier | The task does not require the largest model, and latency matters | Quality may fall on complex reasoning or domain-specific prompts |
| Quantized model | Weight memory is the blocker, and quality tests pass | Accuracy, compatibility, and kernel support may differ |
| Larger tensor parallel size | The model will not fit or needs lower latency on one replica | Requires larger nodes and adds communication overhead |
| More replicas | Queue pressure remains after per-replica tuning | GPU cost rises, cache locality may fall, and routing must be fair |
| Shorter context length | Most prompts do not need the advertised model maximum | Some users may hit policy limits and need product handling |
| Separate traffic pools | Batch jobs hurt interactive users or vice versa | More deployments and routing policy to operate |

The setting `--max-model-len` deserves special attention because product teams often ask for the largest possible context window. Long context sounds like a capability, but it becomes an operational budget. Every additional token of allowed context can increase the worst-case KV cache footprint, reducing how many concurrent conversations the GPU can host.

A practical platform pattern is to publish model tiers with explicit context and output budgets. For example, an interactive assistant tier might have a moderate context limit and strict output cap, while a document analysis tier has a larger context limit and a separate queue. That makes performance expectations visible to application teams and prevents one use case from silently consuming all cache capacity.

What would happen if a customer pasted a long document into an endpoint tuned for short chat messages? The prompt prefill cost would increase time to first token, the KV cache would consume more blocks, and other users could wait longer even if their prompts were short. The right fix may be product-side truncation, retrieval, summarization, or routing to a long-context deployment rather than simply increasing every limit.

You should also avoid tuning solely from averages. Average latency can look acceptable while tail latency is terrible for users behind long prompts. Pair average generation throughput with percentiles for time to first token, queue depth, active sequence count, and cache usage. The relationship among these metrics is more useful than any single number.

### 5. Client Integration, Streaming, and Prefix Caching

vLLM's OpenAI-compatible API is a major adoption advantage because many applications can change the base URL without rewriting their client logic. That compatibility should not make the platform careless. Authentication, rate limits, request validation, model naming, and streaming behavior still belong in the platform contract, especially if multiple teams share the endpoint.

The following example uses the OpenAI Python client against a port-forwarded vLLM Service. It keeps the base URL explicit, uses a placeholder API key because local vLLM does not require one by default, and shows the normal chat completion shape that many applications already use. In production, place authentication and authorization in front of the endpoint instead of relying on the [default open behavior](https://raw.githubusercontent.com/vllm-project/vllm/main/vllm/entrypoints/openai/cli_args.py).

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:8000/v1",
    api_key="not-needed-for-local-vllm",
)

response = client.chat.completions.create(
    model="microsoft/phi-2",
    messages=[
        {"role": "system", "content": "You are a concise Kubernetes assistant."},
        {"role": "user", "content": "Explain why a Deployment creates ReplicaSets."},
    ],
    max_tokens=160,
    temperature=0.2,
)

print(response.choices[0].message.content)
```

Streaming is usually the right user experience for chat because the user sees progress before the full answer is complete. Streaming does not make the model compute faster, but it changes perceived latency and exposes proxy buffering problems quickly. If a direct port-forward streams smoothly while the ingress delivers chunks in bursts, the serving engine may be healthy and the network path may be hiding tokens.

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:8000/v1",
    api_key="not-needed-for-local-vllm",
)

stream = client.chat.completions.create(
    model="microsoft/phi-2",
    messages=[
        {"role": "user", "content": "Give three checks for a pending GPU pod."},
    ],
    max_tokens=180,
    temperature=0.2,
    stream=True,
)

for chunk in stream:
    delta = chunk.choices[0].delta.content
    if delta:
        print(delta, end="", flush=True)
print()
```

[Prefix caching](https://raw.githubusercontent.com/vllm-project/vllm/main/docs/features/automatic_prefix_caching.md) helps when many requests share an identical beginning. Chat assistants often send the same system prompt, policy text, tool instructions, or few-shot examples with every request. If the prefix can be reused, vLLM can avoid repeating some KV work for that shared portion, which can improve latency and throughput for workloads with stable prompts.

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:8000/v1",
    api_key="not-needed-for-local-vllm",
)

system_prompt = """You are a Kubernetes platform assistant.
Answer with operational steps, include the signal to inspect,
and avoid recommending cluster-wide changes before checking workload scope."""

questions = [
    "A vLLM pod is pending with one GPU requested. What do you inspect?",
    "A vLLM endpoint has a rising queue but moderate GPU utilization. What do you inspect?",
    "A rollout takes fifteen minutes because model weights download every time. What do you inspect?",
]

for question in questions:
    response = client.chat.completions.create(
        model="microsoft/phi-2",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
        max_tokens=180,
        temperature=0.2,
    )
    print(f"Question: {question}")
    print(response.choices[0].message.content)
    print("---")
```

Prefix caching works best when the prefix is actually identical. If every client injects timestamps, request IDs, random examples, or user-specific text into the beginning of the prompt, the shared prefix may disappear. Prompt templates are therefore an infrastructure concern as well as an application concern because they influence cache reuse and serving cost.

| Client behavior | Serving impact | Better platform guidance |
|---|---|---|
| Stable system prompt at the beginning | Enables prefix reuse across similar requests | Publish shared prompt templates through a versioned library |
| Random metadata before instructions | Breaks common prefixes and increases prefill work | Put variable metadata later or outside the model prompt when possible |
| Unbounded conversation history | Expands KV cache and hurts other users | Summarize, retrieve, or trim history according to product policy |
| Non-streaming chat UI | Users wait for full completion before seeing progress | Use streaming unless the workflow requires full output validation first |
| Very high `max_tokens` by default | Long generations occupy scheduler slots longer | Set task-specific output caps and require justification for exceptions |
| Retrying without idempotency | Duplicate work during transient failures | Use client timeouts, backoff, and request tracing |

A worked integration review starts with the prompt template, not the Kubernetes YAML. Suppose an application sends a shared system prompt, then a user-specific account profile, then the user question. The shared prompt can be reused only up to the point where the account profile differs. If the platform moves stable instructions before variable data and caps the profile length, it may reduce prefill work without changing GPUs.

The next review step is request shape. If the client always asks for a large `max_tokens` value because no one set a default, users with short questions can still reserve a long decode budget. The server may stop when the model emits an end token, but the scheduler and admission policy must still consider the possible generation. Product-level defaults are therefore part of capacity management.

Finally, review streaming and timeout behavior. Clients should not retry a long-running request immediately just because the first token was slow; that can double traffic during an incident. A better pattern is to use visible streaming, sane client timeouts, exponential backoff for transport failures, and request IDs that let operators connect client symptoms to server metrics.

### 6. Monitoring, Scaling, and Troubleshooting

A vLLM endpoint should be [observed as a queueing system](https://raw.githubusercontent.com/vllm-project/vllm/main/docs/design/metrics.md) with GPU-backed workers. The metrics that matter are not only whether the pod is up, but whether requests are waiting, how quickly the first token appears, how fast output tokens stream, and how much KV cache is occupied. Kubernetes readiness tells you the server can answer health checks; vLLM metrics tell you whether the server is serving well.

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: vllm-phi2
  namespace: llm-serving
spec:
  selector:
    matchLabels:
      app: vllm-phi2
  endpoints:
    - port: http
      path: /metrics
      interval: 15s
```

| Metric | What it tells you | Decision it supports |
|---|---|---|
| `vllm:num_requests_running` | Number of active requests currently being processed | Whether the scheduler is admitting enough concurrent work |
| `vllm:num_requests_waiting` | Number of queued requests waiting for capacity | Whether users are experiencing admission pressure |
| `vllm:gpu_cache_usage_perc` | Fraction of KV cache capacity in use | Whether cache memory is limiting concurrency |
| `vllm:avg_generation_throughput_toks_per_s` | Average output token throughput | Whether decode work is productive under load |
| `vllm:avg_prompt_throughput_toks_per_s` | Average prompt processing throughput | Whether long prompts are dominating prefill |
| `vllm:time_to_first_token_seconds` | Delay before the first generated token | Whether prompt prefill, queueing, or scheduling hurts interactivity |
| `vllm:time_per_output_token_seconds` | Cadence of generated output tokens | Whether users see smooth streaming after generation starts |

```promql
vllm:num_requests_waiting
```

```promql
vllm:gpu_cache_usage_perc
```

```promql
histogram_quantile(
  0.99,
  rate(vllm:time_to_first_token_seconds_bucket[5m])
)
```

```promql
rate(vllm:avg_generation_throughput_toks_per_s[5m])
```

Alerting should distinguish saturation from failure. A pod crash loop is a failure. A growing queue with healthy pods is saturation. A high time-to-first-token percentile with normal per-token speed suggests prompt, queue, or prefill pressure. A normal time to first token with slow token cadence suggests decode throughput or network streaming behavior.

```ascii
┌─────────────────────────────────────────────────────────────────────────┐
│                    Troubleshooting Decision Flow                        │
│                                                                         │
│  User reports slow response                                             │
│          │                                                              │
│          ▼                                                              │
│  Is time to first token high?                                           │
│          │                                                              │
│     ┌────┴────┐                                                         │
│     │         │                                                         │
│    Yes        No                                                        │
│     │         │                                                         │
│     ▼         ▼                                                         │
│  Check     Are output tokens arriving slowly or in bursts?              │
│  queue,        │                                                        │
│  prompt   ┌────┴────┐                                                   │
│  length,  │         │                                                   │
│  prefill Yes        No                                                  │
│     │     │         │                                                   │
│     ▼     ▼         ▼                                                   │
│  Cache  Check     Check client render path, product timeout,            │
│  full?  decode    and user-side network before changing GPUs            │
│     │   throughput                                                     │
│     ▼                                                                  │
│  Tune context, sequence limits, cache utilization, or replicas           │
└─────────────────────────────────────────────────────────────────────────┘
```

Horizontal scaling is useful when per-replica tuning cannot meet demand or when fault tolerance requires more than one serving pod. It is not a substitute for understanding cache and compute pressure. If every replica is configured with an unrealistic context length, adding replicas multiplies cost while preserving the underlying inefficiency.

A basic HorizontalPodAutoscaler can scale on a custom queue metric if your metrics adapter exposes it. The exact metric name depends on the adapter and relabeling, so treat the manifest as a pattern rather than a universal copy. The design principle is stable: scale on waiting work or latency pressure, not only CPU, because CPU is rarely the primary signal for GPU inference.

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: vllm-phi2
  namespace: llm-serving
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: vllm-phi2
  minReplicas: 1
  maxReplicas: 4
  metrics:
    - type: Pods
      pods:
        metric:
          name: vllm_num_requests_waiting
        target:
          type: AverageValue
          averageValue: "8"
```

Multi-model deployment often becomes necessary once teams share a platform. A small fast model can handle simple classification or summarization tasks, while a larger model serves complex reasoning requests. The platform value is not only hosting both models; it is helping teams route to the cheapest model that meets quality and latency requirements.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vllm-small-chat
  namespace: llm-serving
spec:
  replicas: 2
  selector:
    matchLabels:
      app: vllm-small-chat
  template:
    metadata:
      labels:
        app: vllm-small-chat
        model-tier: small
    spec:
      containers:
        - name: vllm
          image: vllm/vllm-openai:latest
          args:
            - --model
            - microsoft/phi-2
            - --max-model-len
            - "2048"
          resources:
            limits:
              nvidia.com/gpu: "1"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vllm-large-chat
  namespace: llm-serving
spec:
  replicas: 1
  selector:
    matchLabels:
      app: vllm-large-chat
  template:
    metadata:
      labels:
        app: vllm-large-chat
        model-tier: large
    spec:
      containers:
        - name: vllm
          image: vllm/vllm-openai:latest
          args:
            - --model
            - meta-llama/Llama-2-70b-chat-hf
            - --tensor-parallel-size
            - "4"
            - --max-model-len
            - "4096"
          resources:
            limits:
              nvidia.com/gpu: "4"
```

The final troubleshooting skill is translating symptoms into a change plan. If the queue is high and cache is full, shorten context, reduce long-running traffic, or add cache capacity through replicas. If the queue is high and cache is not full but GPU compute is saturated, tune batching or scale compute. If startup is slow, fix model cache and rollout strategy before blaming vLLM.

| Incident symptom | Most useful first command | What to look for | Likely next action |
|---|---|---|---|
| Pod pending | `k describe pod -n llm-serving <pod-name>` | Unsatisfied GPU, node selector, taint, or affinity | Fix scheduling constraints or node capacity |
| Pod starts then exits | `k logs -n llm-serving <pod-name>` | Model load failure, OOM, token permission, image issue | Adjust model, memory, token secret, or image version |
| Readiness never passes | `k get pods -n llm-serving -w` | Model still loading or health endpoint failing | Extend probe timing or fix startup failure |
| Queue grows during load | Query `vllm:num_requests_waiting` | Sustained waiting requests | Tune context, batch limits, or replicas |
| GPU cache near full | Query `vllm:gpu_cache_usage_perc` | Cache saturation | Lower context, reduce active sequences, or split traffic |
| Streaming bursts through ingress | Compare port-forward with ingress path | Smooth direct stream but bursty proxied stream | Check proxy buffering and timeout behavior |
| Rollout causes long outage | `k describe pod` and image/model logs | Repeated downloads or slow load | Add persistent cache and rolling strategy |

A senior platform engineer closes the loop with a load test that matches the product. The test should include realistic prompt lengths, output caps, concurrency, streaming mode, and shared prefixes if the application uses them. It should report queue depth, time to first token, total latency, and token throughput, because one of those can improve while another gets worse.

```python
import asyncio
import statistics
import time

import aiohttp

URL = "http://127.0.0.1:8000/v1/completions"
MODEL = "microsoft/phi-2"

PROMPTS = [
    "Explain why a Kubernetes Deployment creates ReplicaSets.",
    "Summarize how GPU resource requests affect pod scheduling.",
    "Give a troubleshooting plan for a vLLM endpoint with rising queue depth.",
    "Compare shortening context length with adding another GPU replica.",
    "Write a concise incident update for slow time to first token.",
    "Explain why persistent model cache reduces rollout risk.",
    "Describe how prefix caching changes prompt template design.",
    "Recommend metrics for autoscaling an LLM serving endpoint.",
]

async def send_request(session: aiohttp.ClientSession, prompt: str) -> float:
    started = time.perf_counter()
    async with session.post(
        URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "max_tokens": 120,
            "temperature": 0.2,
        },
        timeout=120,
    ) as response:
        response.raise_for_status()
        await response.json()
    return time.perf_counter() - started

async def main() -> None:
    async with aiohttp.ClientSession() as session:
        started = time.perf_counter()
        latencies = await asyncio.gather(
            *(send_request(session, prompt) for prompt in PROMPTS)
        )
        elapsed = time.perf_counter() - started

    sorted_latencies = sorted(latencies)
    p95_index = max(0, int(len(sorted_latencies) * 0.95) - 1)

    print(f"requests={len(PROMPTS)}")
    print(f"elapsed_seconds={elapsed:.2f}")
    print(f"throughput_requests_per_second={len(PROMPTS) / elapsed:.2f}")
    print(f"mean_latency_seconds={statistics.mean(latencies):.2f}")
    print(f"p95_latency_seconds={sorted_latencies[p95_index]:.2f}")

if __name__ == "__main__":
    asyncio.run(main())
```

When you evaluate the load test, resist the urge to tune until one number looks good. Better throughput with unacceptable first-token latency may be wrong for chat. Better first-token latency with terrible total throughput may be wrong for batch summarization. The correct target comes from the product's service objective and the platform's cost envelope.

## Did You Know?

- vLLM's PagedAttention was inspired by operating-system virtual memory ideas, but it applies the paging concept to transformer KV cache blocks rather than process address spaces.
- Continuous batching improves serving efficiency because a request can enter the active set when scheduler capacity appears, instead of waiting for a whole static batch to drain.
- Prefix caching is most valuable when prompt templates keep shared instructions byte-for-byte stable before user-specific content begins.
- The OpenAI-compatible API reduces application migration effort, but production platforms still need authentication, quotas, request validation, and observability around the endpoint.

## Common Mistakes

| Mistake | Problem | Better practice |
|---|---|---|
| Deploying with the model's maximum context length by default | KV cache capacity is consumed by a product promise that most requests do not need | Set `--max-model-len` from real prompt policy and provide a separate long-context tier when needed |
| Increasing `--max-num-seqs` during cache saturation | More admitted sequences can worsen preemption, swapping, or tail latency | Check cache usage first, then tune sequence limits only when memory headroom exists |
| Treating GPU memory usage as proof of useful work | Model weights and reserved cache can fill memory while compute remains underused | Compare memory, queue depth, active sequences, and token throughput together |
| Omitting a persistent model cache | Pod restarts and rollouts repeatedly download large weights, extending outages | Mount a PVC or node-local cache strategy for model artifacts |
| Forgetting the `/dev/shm` mount | Worker communication can fail or degrade under load with tiny default shared memory | Use an in-memory `emptyDir` sized for the serving process and traffic pattern |
| Scaling on CPU utilization alone | CPU may look normal while GPU-backed request queues are unhealthy | Scale from queue depth, latency, cache pressure, and GPU-serving metrics |
| Mixing batch and interactive traffic in one pool | Long jobs can consume cache and scheduler slots needed by chat users | Split traffic classes or enforce request budgets and routing policies |
| Using `latest` images for production rollouts | Unplanned version changes can alter flags, kernels, compatibility, or metrics | Pin tested image versions and roll forward through a controlled release process |

## Quiz

### Question 1

Your team deploys a single-GPU vLLM endpoint for an internal assistant. During a launch, `vllm:num_requests_waiting` rises steadily, `vllm:gpu_cache_usage_perc` is near full, and GPU compute utilization is not consistently high. What should you investigate before adding more replicas?

<details>
<summary>Show Answer</summary>

Start with KV cache pressure rather than compute capacity. Inspect the configured `--max-model-len`, request prompt and output length distribution, `--max-num-seqs`, and whether long-running traffic is sharing the same deployment as interactive chat. Adding replicas may eventually be needed, but the evidence says active requests are filling cache capacity before the GPU is doing consistently useful compute. A shorter context policy, separate traffic tier, or safer sequence limit may recover capacity at lower cost.
</details>

### Question 2

A four-GPU vLLM pod is pending, but the cluster dashboard shows four idle GPUs across four different nodes. The application team asks why Kubernetes cannot just use all four. How do you explain the issue and propose a fix?

<details>
<summary>Show Answer</summary>

A pod's GPU resource request must be satisfied on one node, so a single tensor-parallel vLLM replica that requests four GPUs needs one node with four compatible allocatable GPUs. Four one-GPU nodes cannot satisfy that pod. The fix is to use a node pool with sufficiently large GPU nodes, choose a smaller or quantized model that fits on fewer GPUs, or run separate one-GPU replicas for a model that can load independently.
</details>

### Question 3

An application uses the same long system prompt for every request, but prefix caching does not appear to improve latency. A review shows the client prepends a timestamp and request ID before the system prompt. What design change would you recommend?

<details>
<summary>Show Answer</summary>

Move variable metadata out of the shared prefix path, or place stable instructions before request-specific values if those values must be in the prompt. Prefix caching depends on identical leading tokens, so putting timestamps or request IDs first prevents reuse across requests. The platform should publish a stable prompt template and keep variable data later in the message structure or outside the model input when possible.
</details>

### Question 4

A product team asks to raise `max_tokens` for every chat request because a few users need longer answers. After the change, average latency is acceptable, but p99 latency and queue depth worsen during traffic spikes. How would you redesign the serving policy?

<details>
<summary>Show Answer</summary>

Do not make the rare long-output case the default for every request. Create task-specific output caps, route long-generation workflows to a separate tier, and require the client to request larger budgets only when the product flow needs them. This protects scheduler slots and KV cache for normal chat while still supporting long answers through an explicit policy. The assessment should compare p99 time to first token, total latency, queue depth, and user success rate after the change.
</details>

### Question 5

A vLLM rollout takes many minutes and sometimes fails when several pods restart together. Logs show repeated downloads from the model registry, but the old pod served traffic normally before the rollout. What Kubernetes design issue should you fix?

<details>
<summary>Show Answer</summary>

Fix model artifact caching and rollout behavior. Mount a persistent cache, node-local cache, or other approved model storage strategy so restarted pods do not download weights from scratch every time. Also review readiness probe timing and rolling update settings so Kubernetes does not send traffic before the model is loaded. The serving engine may be healthy once started; the incident is caused by startup dependency and rollout design.
</details>

### Question 6

A direct `kubectl port-forward` test streams tokens smoothly, but users accessing the same endpoint through the ingress receive tokens in large bursts. The vLLM metrics do not show unusual queue depth or cache pressure. What should you check next?

<details>
<summary>Show Answer</summary>

Check the network and proxy path before tuning vLLM. Ingress controllers, service mesh proxies, or load balancers can buffer streaming responses or enforce timeouts that change the user experience. Compare response headers, buffering settings, idle timeouts, and streaming support between the direct path and the ingress path. The evidence suggests vLLM is generating tokens, but the delivery path is not flushing them as expected.
</details>

### Question 7

A team wants to serve a large model that barely loads on a four-GPU node. After startup, even modest traffic causes out-of-memory failures. Why can a model fit at startup but still fail under user traffic?

<details>
<summary>Show Answer</summary>

Startup mostly proves that model weights fit with the configured runtime overhead. User traffic adds KV cache growth for active prompts and generated tokens, so the remaining memory may be too small for the request mix. The team should evaluate context length, output caps, `--gpu-memory-utilization`, quantization, tensor parallel layout, and whether the selected model tier is too large for the desired concurrency. Loading the model is only the first memory test.
</details>

### Question 8

Your platform has one vLLM deployment serving short interactive chat and offline document summarization. Chat users report slow first tokens whenever summarization jobs run. Which architecture change best addresses the conflict?

<details>
<summary>Show Answer</summary>

Separate the traffic classes or enforce strong routing and budget policies. Offline summarization can use long prompts and long generations that consume prompt prefill time, KV cache, and scheduler slots, while chat needs predictable time to first token. Running separate deployments, queues, or model tiers lets each workload use appropriate context limits, output caps, autoscaling signals, and service objectives. Simply raising global limits makes the shared contention worse.
</details>

## Hands-On Exercise: Deploy, Test, and Tune a vLLM Endpoint

**Objective**: Deploy a small vLLM endpoint on Kubernetes, test the OpenAI-compatible API, observe serving metrics, and make one evidence-based tuning recommendation from the results.

### Task 1: Prepare the namespace and confirm GPU scheduling

Begin by creating an isolated namespace and checking that the cluster exposes GPU resources. This step prevents a common failure where the learner writes a correct Deployment manifest but the cluster cannot schedule it because the GPU device plugin or node pool is missing.

```bash
alias k=kubectl

k create namespace llm-demo

k get nodes -o custom-columns=NAME:.metadata.name,GPUS:.status.allocatable.nvidia\\.com/gpu
```

Success criteria:

- [ ] The `llm-demo` namespace exists.
- [ ] At least one node reports allocatable `nvidia.com/gpu`.
- [ ] If no GPU is shown, you can explain whether the issue is node capacity, GPU operator setup, or device plugin exposure.

### Task 2: Deploy vLLM with a persistent cache and shared memory

Apply the following manifest. It uses a small demonstration model so the exercise focuses on serving mechanics rather than large-model procurement. If your environment uses a different storage class or approved model, adjust those fields while preserving the same design intent.

```bash
k apply -f - <<'EOF'
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: model-cache-pvc
  namespace: llm-demo
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 80Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vllm-server
  namespace: llm-demo
  labels:
    app: vllm-server
spec:
  replicas: 1
  selector:
    matchLabels:
      app: vllm-server
  template:
    metadata:
      labels:
        app: vllm-server
    spec:
      containers:
        - name: vllm
          image: vllm/vllm-openai:latest
          args:
            - --model
            - microsoft/phi-2
            - --host
            - 0.0.0.0
            - --port
            - "8000"
            - --max-model-len
            - "2048"
            - --gpu-memory-utilization
            - "0.88"
          ports:
            - name: http
              containerPort: 8000
          resources:
            requests:
              cpu: "4"
              memory: 24Gi
              nvidia.com/gpu: "1"
            limits:
              memory: 32Gi
              nvidia.com/gpu: "1"
          readinessProbe:
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 120
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 18
          volumeMounts:
            - name: model-cache
              mountPath: /root/.cache/huggingface
            - name: shm
              mountPath: /dev/shm
      volumes:
        - name: model-cache
          persistentVolumeClaim:
            claimName: model-cache-pvc
        - name: shm
          emptyDir:
            medium: Memory
            sizeLimit: 8Gi
---
apiVersion: v1
kind: Service
metadata:
  name: vllm-server
  namespace: llm-demo
  labels:
    app: vllm-server
spec:
  selector:
    app: vllm-server
  ports:
    - name: http
      port: 8000
      targetPort: http
EOF
```

Watch the rollout and inspect failures rather than waiting silently. If the pod stays pending, describe it and look for GPU scheduling messages. If the pod starts and exits, read logs and identify whether the problem is model download, memory, image compatibility, or startup flags.

```bash
k rollout status deployment/vllm-server -n llm-demo --timeout=15m

k get pods -n llm-demo -l app=vllm-server

POD_NAME="$(k get pod -n llm-demo -l app=vllm-server -o jsonpath='{.items[0].metadata.name}')"
k describe pod -n llm-demo "$POD_NAME" | sed -n '/Events:/,$p'
```

Success criteria:

- [ ] The Deployment reaches available status.
- [ ] You can identify where model cache and `/dev/shm` are mounted.
- [ ] If the pod does not become ready, you can name the failing layer instead of saying only that "vLLM failed."

### Task 3: Test the OpenAI-compatible API

Forward the service to your workstation and send one completion request. Keep this terminal running while you test from another shell.

```bash
k port-forward -n llm-demo svc/vllm-server 8000:8000
```

In another shell, run:

```bash
curl -sS http://127.0.0.1:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "microsoft/phi-2",
    "prompt": "Kubernetes schedules GPU workloads by",
    "max_tokens": 80,
    "temperature": 0.2
  }'
```

Success criteria:

- [ ] The API returns a JSON response rather than a transport error.
- [ ] The response includes generated text for the requested model.
- [ ] You can explain why a local `api_key` is not required by default and why production should still add authentication.

### Task 4: Run a small concurrent load test

Create a local test file that sends several realistic requests at once. The goal is not to produce a benchmark worthy of publication; the goal is to create enough activity that queue, cache, and latency metrics become meaningful.

```python
import asyncio
import statistics
import time

import aiohttp

URL = "http://127.0.0.1:8000/v1/completions"
MODEL = "microsoft/phi-2"

PROMPTS = [
    "Explain why a Kubernetes GPU pod can remain pending.",
    "Summarize the operational purpose of vLLM PagedAttention.",
    "Describe how prefix caching affects prompt template design.",
    "Give a troubleshooting plan for high time to first token.",
    "Compare adding replicas with reducing maximum context length.",
    "Explain why model cache persistence matters during rollouts.",
    "Recommend metrics for autoscaling a vLLM deployment.",
    "Describe the risk of mixing batch summarization with chat traffic.",
]

async def send_request(session: aiohttp.ClientSession, prompt: str) -> float:
    start = time.perf_counter()
    async with session.post(
        URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "max_tokens": 100,
            "temperature": 0.2,
        },
        timeout=120,
    ) as response:
        response.raise_for_status()
        await response.json()
    return time.perf_counter() - start

async def main() -> None:
    async with aiohttp.ClientSession() as session:
        start = time.perf_counter()
        latencies = await asyncio.gather(
            *(send_request(session, prompt) for prompt in PROMPTS)
        )
        elapsed = time.perf_counter() - start

    sorted_latencies = sorted(latencies)
    p95_index = max(0, int(len(sorted_latencies) * 0.95) - 1)

    print(f"requests={len(PROMPTS)}")
    print(f"elapsed_seconds={elapsed:.2f}")
    print(f"requests_per_second={len(PROMPTS) / elapsed:.2f}")
    print(f"mean_latency_seconds={statistics.mean(latencies):.2f}")
    print(f"p95_latency_seconds={sorted_latencies[p95_index]:.2f}")

if __name__ == "__main__":
    asyncio.run(main())
```

Run the script from an environment with `aiohttp` installed:

```bash
python load_test.py
```

Success criteria:

- [ ] The script completes without HTTP errors.
- [ ] You record mean latency, p95 latency, elapsed time, and request throughput.
- [ ] You can explain why this is a functional load test, not a full production benchmark.

### Task 5: Inspect metrics and make a tuning recommendation

While the load test runs or immediately after it, inspect vLLM metrics. The exact set of metrics can vary by version, so use filtering to find queue, cache, and throughput signals.

```bash
curl -sS http://127.0.0.1:8000/metrics | grep -E 'vllm:.*(requests|cache|throughput|time)'
```

Write a short recommendation using this structure:

- [ ] **Observed signal**: name the metric or symptom you saw.
- [ ] **Interpretation**: state whether the likely pressure is cache, compute, startup, or network path.
- [ ] **Change**: recommend one specific change, such as reducing `--max-model-len`, separating traffic, changing output caps, tuning `--max-num-seqs`, or adding replicas.
- [ ] **Validation**: state which metric should improve if your recommendation is correct.

A good answer is evidence-based even if the lab traffic is small. For example, "I would add GPUs" is weak because it does not identify a bottleneck. "The queue rose while cache usage was high, so I would first test a lower context limit and expect waiting requests and p99 TTFT to fall" is stronger because it connects signal, mechanism, action, and validation.

### Task 6: Clean up the lab

Remove the namespace after you finish so GPU resources are released. This matters on shared clusters because idle model-serving pods can hold scarce accelerators even after the exercise is complete.

```bash
k delete namespace llm-demo
```

Success criteria:

- [ ] The namespace is deleted.
- [ ] No vLLM pod from the exercise continues to hold a GPU.
- [ ] Your notes include one deployment lesson, one metric lesson, and one tuning lesson.

## Next Module

Continue to [Module 9.5: Ray Serve](../module-9.5-ray-serve/) to learn about distributed inference and scaling LLM serving across multiple nodes.

## Sources

- [Efficient Memory Management for Large Language Model Serving with PagedAttention](https://arxiv.org/abs/2309.06180) — Primary research source for PagedAttention, KV-cache sharing, and the paper's reported throughput gains.
- [vLLM OpenAI-Compatible Server](https://raw.githubusercontent.com/vllm-project/vllm/main/docs/serving/openai_compatible_server.md) — Upstream documentation for vLLM's OpenAI-compatible APIs, including completions, chat, and embeddings endpoints.
- [vLLM Parallelism and Scaling](https://github.com/vllm-project/vllm/blob/main/docs/serving/parallelism_scaling.md) — Upstream guidance on tensor parallelism, multi-GPU deployment, and `/dev/shm` considerations for serving.
- [Schedule GPUs](https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/) — Authoritative Kubernetes documentation for requesting GPU resources in Pods and deployments.
- [raw.githubusercontent.com: README.md](https://raw.githubusercontent.com/vllm-project/vllm/main/README.md) — The upstream README lists continuous batching among vLLM's serving features.
- [raw.githubusercontent.com: automatic prefix caching.md](https://raw.githubusercontent.com/vllm-project/vllm/main/docs/features/automatic_prefix_caching.md) — The upstream APC documentation says shared-prefix requests can reuse KV cache and notes that APC reduces query processing/prefill rather than generation/decoding.
- [raw.githubusercontent.com: metrics.md](https://raw.githubusercontent.com/vllm-project/vllm/main/docs/design/metrics.md) — The upstream metrics design document lists the v1 Prometheus metrics and their meanings.
- [raw.githubusercontent.com: parallelism scaling.md](https://raw.githubusercontent.com/vllm-project/vllm/main/docs/serving/parallelism_scaling.md) — The upstream parallelism and scaling guide explicitly shows a Kubernetes /dev/shm emptyDir mount for vLLM shared memory and IPC.
- [raw.githubusercontent.com: arg utils.py](https://raw.githubusercontent.com/vllm-project/vllm/main/vllm/engine/arg_utils.py) — The upstream argument parser defines these vLLM CLI arguments.
- [raw.githubusercontent.com: cli args.py](https://raw.githubusercontent.com/vllm-project/vllm/main/vllm/entrypoints/openai/cli_args.py) — The upstream OpenAI server CLI arguments define api_key as optional and say provided keys are then required in headers.

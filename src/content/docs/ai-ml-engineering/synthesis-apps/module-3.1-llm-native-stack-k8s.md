---
title: "LLM-Native Stack: Inference and Memory on Kubernetes"
slug: ai-ml-engineering/synthesis-apps/module-3.1-llm-native-stack-k8s
sidebar:
  order: 1
---
> **Complexity**: Advanced
>
> **Time to Complete**: 90-120 min
>
> **Prerequisites**: [High-Performance LLM Inference: vLLM and sglang](../ai-infrastructure/module-1.3-vllm-sglang-inference/), [Vector Databases Deep Dive](../vector-rag/module-1.1-vector-databases-deep-dive/), [GPU Scheduling](../../platform/toolkits/data-ai-platforms/ml-platforms/module-9.7-gpu-scheduling/)

---

## What You'll Be Able to Do

Learning outcome: you can deploy vLLM and Qdrant as coordinated Kubernetes
services, configure their internal networking and resource boundaries with
NetworkPolicy and ResourceQuota, verify the stack is healthy with `kubectl exec`
probes, and observe failure modes through controlled pod-delete injection.

By the end of this module, you will be able to:

- **Design** a four-layer LLM-native stack that separates GPU substrate,
  inference backend, vector memory, and orchestration responsibilities.
- **Deploy** vLLM and Qdrant as Kubernetes services with persistent storage,
  health probes, resource boundaries, and internal-only networking.
- **Compare** full-GPU, MIG-slice, and time-shared GPU allocation choices for
  inference workloads in a teaching or team cluster.
- **Verify** OpenAI-compatible inference, Qdrant health, and namespace-level
  NetworkPolicy behavior using `kubectl exec` and `curl`.
- **Diagnose** backend restart behavior by deleting vLLM and Qdrant pods,
  observing what clients see, and mapping the symptoms to retry logic that
  Module 3.2 will implement.

## Why This Module Matters

Exercise scenario: a platform team has a working notebook demo that retrieves
documentation chunks from a local vector database and sends the prompt to a
self-hosted Llama model. The demo impresses everyone because it answers a few
questions correctly, but the first Kubernetes deployment is brittle: the
inference pod starts before the model is loaded, Qdrant restarts while its index
is still hydrating, the application namespace can reach every service in the
cluster, and nobody can say whether a failed user request came from retrieval,
generation, or networking.

That situation is common because LLM applications are easy to sketch and hard
to operate. A single user-facing answer crosses several services with different
resource shapes. vLLM wants GPU memory, predictable model files, and probes that
do not send traffic before the model is ready. Qdrant wants persistent storage,
fast enough disk for index loading, and a readiness signal that reflects whether
search can actually serve. The application layer wants stable DNS names and
clear errors rather than a maze of transient pod IPs and ambiguous timeouts.

This module builds the substrate before any orchestration code appears. That
ordering is deliberate. If you cannot prove that the inference and memory
services are independently healthy, internally reachable, isolated from the
wrong namespaces, and understandable under restart, Module 3.2's application
retry code will be guesswork. The goal here is not to memorize vLLM or Qdrant
YAML. The goal is to learn the operating boundaries that make an LLM-native
application a system rather than a pile of containers.

## Architecture First, Tools Second

The stack starts with a question that sounds simple but decides everything
downstream: which layer owns each failure? A GPU allocation problem is not an
application bug. A model still loading is not a vector database outage. A
NetworkPolicy rejection is not an inference saturation event. When those
responsibilities blur, every incident becomes a generic "the AI app is down"
complaint, which is too vague for useful debugging.

Use this four-layer diagram as the vocabulary for the whole mini-arc. The
arrows represent internal calls, not ownership. The orchestration layer calls
memory and inference, but it does not own GPU device plugins, model file
placement, or Qdrant shard recovery. Kubernetes gives each layer a place to
declare its needs, and your job is to keep those declarations aligned.

```text
+--------------------------------------------------------------------------+
|                         Orchestration layer                              |
|  App Deployment, prompt assembly, retrieval calls, retries, state budget  |
|  Examples later in arc: LangGraph service, Redis checkpointing, eval gate |
+------------------------------------+-------------------------------------+
                                     |
                   internal Service DNS + NetworkPolicy boundary
                                     |
+------------------------------------v-------------------------------------+
|                           Vector memory layer                            |
|  Qdrant StatefulSet/Helm release, persistent index, payload filters,      |
|  readiness while indexes hydrate, metrics for search and storage health   |
+------------------------------------+-------------------------------------+
                                     |
                         retrieved context joins prompt
                                     |
+------------------------------------v-------------------------------------+
|                         Inference backend layer                          |
|  vLLM OpenAI-compatible API, model weights, KV cache, GPU memory budget,  |
|  liveness/readiness probes, ClusterIP service for internal callers        |
+------------------------------------+-------------------------------------+
                                     |
                         scheduled onto GPU-capable nodes
                                     |
+------------------------------------v-------------------------------------+
|                            GPU substrate layer                           |
|  NVIDIA GPU Operator, device plugin, DCGM exporter, ResourceQuota,        |
|  MIG/time-slicing policy, node labels, tolerations, and runtime classes   |
+--------------------------------------------------------------------------+
```

The GPU substrate layer answers "can this namespace consume an accelerator, and
which nodes can provide it?" The NVIDIA GPU Operator normally installs the
device plugin, DCGM exporter, node feature discovery integration, and related
components. This module assumes that work is already complete because GPU
Operator installation belongs in the platform toolkit. Here you consume the
resource from an application namespace and put a quota around that consumption.

The inference backend layer answers "can the model serve an inference request
now?" vLLM is the concrete engine in this module because it exposes an
OpenAI-compatible API and is widely used for high-throughput open-model serving.
Other shapes exist. KServe is the mature Kubernetes platform endpoint that
hides much of this YAML behind `InferenceService` resources, Ray Serve is a
pipeline-serving option reserved for Module 3.2 vocabulary, and BentoML can
package model services as a more opinionated deployment unit. Those tools are
useful, but using them well is easier after you understand what they abstract.

The vector memory layer answers "can retrieval return the right stored context
under the application's latency and persistence needs?" Qdrant is the concrete
memory backend in this module because it has an official Helm chart, persistent
storage support, REST and gRPC APIs, and Prometheus-style metrics. The vector
database is not just a library. It has startup time, disk pressure, payload
indexing behavior, and readiness semantics that matter to the user-facing app.

The orchestration layer answers "how does a user request become retrieval,
prompt assembly, inference, state updates, and an answer?" This module does not
write that application yet. It only prepares the endpoints that the application
will consume. Module 3.2 will add the orchestration service and retry code.
Module 3.3 will add DeepEval, Promptfoo, and LangFuse-style quality and
traceability gates. For now, the skill is to make the backing services
observable enough that the later code can make informed decisions.

Pause and predict: before reading the next section, mark which layer enforces
the per-namespace GPU quota. Then mark which layer should answer "the model is
loaded and traffic can be routed." If you picked the same layer for both, slow
down. Quota is a Kubernetes resource governance concern in the GPU substrate
layer, while model readiness belongs to the inference backend layer.

## GPU Provisioning For Inference Workloads

GPU provisioning in this module starts after the cluster already advertises
GPU resources. On a correctly prepared node, `kubectl describe node` shows an
extended resource such as `nvidia.com/gpu`. If the cluster uses MIG, you may
see resources such as `nvidia.com/mig-1g.10gb`. If the platform team enabled
time-slicing, the advertised resource may still look like a GPU while the
operator multiplexes work underneath. Those choices are platform decisions, but
application teams still need to request the right shape and stay inside quota.

For a teaching cluster, use one namespace for the backing services and one
namespace for the future application. That separation lets NetworkPolicy prove
which calls are intended. It also lets ResourceQuota keep a learner from
accidentally scheduling several GPU pods while experimenting with probes. The
commands below create the namespaces and label the application namespace so a
NetworkPolicy can refer to it later.

```bash
kubectl create namespace llm-system
kubectl create namespace llm-apps
kubectl label namespace llm-apps kubedojo.dev/role=llm-apps
```

Many engineers use `k` as an interactive shorthand for `kubectl` after setting
an alias in their shell. The examples in this module keep the full command name
inside runnable blocks so they remain copy-pasteable in non-interactive shells,
CI jobs, and classroom notes.

ResourceQuota for GPUs uses the request form of the extended resource because
Kubernetes does not overcommit accelerators the way it may overcommit CPU.
Pods commonly specify the GPU under `limits`, and Kubernetes treats the request
as equal to the limit for that extended resource. The quota object below says
the namespace can consume one GPU, a bounded amount of CPU and memory, a bounded
number of pods, and a bounded amount of persistent storage.

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: llm-system-quota
  namespace: llm-system
spec:
  hard:
    requests.nvidia.com/gpu: "1"
    requests.cpu: "4"
    requests.memory: 32Gi
    limits.cpu: "12"
    limits.memory: 96Gi
    requests.storage: 400Gi
    persistentvolumeclaims: "4"
    pods: "8"
```

Keep the quota aligned with workload storage demands: verify that `sum(PVC requests) <= requests.storage` so namespace storage admission is predictable and not stuck by a manifest mismatch.

This quota is intentionally conservative. It gives one inference pod enough
room to load a modest instruction model and leaves space for Qdrant, monitoring
sidecars, and temporary debug pods. In a shared teaching cluster, the goal is
not maximum throughput. The goal is predictable access, clean failure signals,
and a cost boundary that prevents idle GPU experiments from consuming every
accelerator on the node pool.

The next choice is whether the vLLM pod should request a full GPU, a MIG slice,
or a time-shared GPU. That choice changes scheduling, latency stability, and
the kinds of failures a learner sees. Full GPUs are easiest to reason about,
MIG slices provide stronger hardware isolation on supported NVIDIA GPUs, and
time-sharing gives more users a chance to experiment but makes latency noisier.

Cost enters this decision earlier than many learners expect. A GPU pod that is
Running but unused is still occupying the accelerator, and the scheduler cannot
offer that device to another namespace while the pod holds it. On a cloud node
pool, that often means the team is paying for the node even when no one is
actively testing. On a private cluster, the price may not appear as a bill, but
the opportunity cost is still real because another learner, CI job, or model
experiment cannot use the same device. Quota is therefore not only a fairness
tool; it is a cost and capacity control.

| Allocation shape | Kubernetes request example | Best fit | Trade-off |
|------------------|----------------------------|----------|-----------|
| Full GPU | `nvidia.com/gpu: 1` | One learner or one small team serving a model where latency should be easy to explain. | Simple and predictable, but a small model may leave expensive VRAM idle. |
| MIG slice | `nvidia.com/mig-1g.10gb: 1` | Multi-tenant clusters where hardware partitioning matters and the model fits the slice. | Stronger isolation, but setup and model sizing become more complex. |
| Time-shared GPU | `nvidia.com/gpu: 1` with operator time-slicing policy | Workshops where many learners need short inference experiments. | Better access, but requests compete for the same hardware and tail latency is harder to teach. |

For this module, full GPU is the right default. MIG is often overkill for a
single learner because the partitioning policy becomes the lesson instead of
the LLM stack. Time-sharing is useful in a classroom with scarce hardware, but
it can make failure injection confusing because a slow request may reflect
neighbor activity rather than your own pod state. Start with full GPU, learn
the service boundaries, and revisit MIG or time-slicing when multi-tenancy is
the actual problem.

The hidden cost spike in inference labs is usually idle retention rather than
one expensive request. A learner applies a Deployment, verifies one chat
completion, walks away, and leaves the GPU allocated for hours. The quota above
does not delete idle pods, but it prevents the namespace from multiplying the
mistake. In a real teaching environment, pair quota with a simple cleanup
policy, a scheduled scale-down, or a dashboard that shows which namespaces are
holding GPU resources. Those operational habits matter because LLM serving
costs are dominated by reserved accelerators and loaded model memory, not by
the few tokens in a smoke test.

The minimal inference pod request looks like this. The image tag is shown as
`latest` to keep the curriculum example readable, but production deployments
should pin an immutable digest after validating the chosen vLLM version, model
format, CUDA runtime, and health endpoints together.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gpu-request-smoke
  namespace: llm-system
spec:
  replicas: 1
  selector:
    matchLabels:
      app: gpu-request-smoke
  template:
    metadata:
      labels:
        app: gpu-request-smoke
    spec:
      restartPolicy: Always
      containers:
        - name: vllm
          image: vllm/vllm-openai:latest
          command: ["vllm"]
          args:
            - "serve"
            - "meta-llama/Llama-3.1-8B-Instruct"
            - "--served-model-name"
            - "meta-llama/Llama-3.1-8B-Instruct"
            - "--max-model-len"
            - "4096"
          resources:
            limits:
              nvidia.com/gpu: "1"
              cpu: "10"
              memory: 64Gi
            requests:
              cpu: "2"
              memory: 24Gi
          ports:
            - containerPort: 8000
              name: http
```

Do not apply the smoke Deployment if you are about to apply the complete vLLM
manifest in the next section. It is shown to isolate the resource request
mechanic. In real work, you would apply the quota first, then the full vLLM
Deployment, and then inspect scheduling with `kubectl describe pod` if the pod
remains Pending. A Pending pod with a quota error is different from a Pending
pod with no GPU-capable node, and that distinction saves a lot of wasted model
debugging.

One useful debugging habit is to translate every Pending pod into a scheduling
question before treating it as an application problem. If the event says quota
was exceeded, reduce the request or remove another workload from the namespace.
If the event says insufficient `nvidia.com/gpu`, inspect allocatable devices,
node taints, and whether another pod already holds the accelerator. If the pod
is scheduled but then crashes, move up one layer and inspect container logs,
model cache permissions, and probe paths. That layer-by-layer discipline keeps
you from changing model flags when the scheduler never placed the pod.

## vLLM As A Kubernetes Service

The isolated vLLM Deployment from an inference module is useful for learning
PagedAttention, batching, and the OpenAI-compatible API. A Kubernetes service
that an application can depend on needs a wider shape. It needs configuration
separated from the pod template, a persistent model cache, probes that avoid
routing traffic during model load, an internal DNS name, and a NetworkPolicy
that rejects callers outside the intended application namespace.

The probe wording deserves care because inference containers often have more
than one "healthy" state. A process can be alive while the model is still
loading. A TCP port can accept a connection while the engine is not ready to
generate tokens. Ideally you would have separate "is the process alive?" and
"is the model ready to take requests?" endpoints, and many production stacks
build that split with a sidecar proxy or wrapper around the inference server.
The stock `vllm/vllm-openai` image, however, exposes exactly one health route:
`/health`. The router returns `200 OK` only after the model loads and the
serving path is ready to generate tokens, so the same endpoint serves as the
liveness *and* readiness signal — there is no separate `/health/live` or
`/health/ready` in the upstream code. The manifest below uses `/health` for
all three probes, and the *durations* — not the paths — are how we separate
"should Kubernetes restart this container?" from "should the Service route
user traffic here?".

The important teaching point is the duration discipline, not the literal path
string. Liveness should answer "should Kubernetes restart this container?";
readiness should answer "should the Service route user traffic here?". For
vLLM, the model load takes roughly 30-60 seconds for modest models and much
longer if weights are fetched over the network. A naive liveness probe with
the default `failureThreshold: 3` and `periodSeconds: 10` will kill the
container before the model finishes loading — that is the textbook crash
loop. The startup probe below buys the model up to six minutes
(`failureThreshold: 36 × periodSeconds: 10s`) before the liveness probe
takes over. Until the startup probe succeeds, liveness and readiness are
suppressed; once it succeeds, readiness gates traffic on a tight 10-second
loop while liveness only restarts the pod after three consecutive 30-second
failures. That difference in *cadence* against the *same* endpoint is what
gives vLLM the load window it needs without sacrificing crash detection.

Apply these five resources together after the `llm-system` namespace and quota
exist. The PVC caches model weights under `HF_HOME`; the ConfigMap holds model
parameters that change more often than the pod shape; the Deployment mounts the
PVC, requests a GPU, and exposes probes; the Service gives application pods a
stable DNS name; and the NetworkPolicy allows only the labelled application
namespace to reach the inference port.

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: vllm-model-config
  namespace: llm-system
data:
  MODEL_ID: "meta-llama/Llama-3.1-8B-Instruct"
  SERVED_MODEL_NAME: "meta-llama/Llama-3.1-8B-Instruct"
  MAX_MODEL_LEN: "4096"
  GPU_MEMORY_UTILIZATION: "0.88"
  MAX_NUM_SEQS: "16"
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: vllm-model-cache
  namespace: llm-system
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: fast-nvme
  resources:
    requests:
      storage: 120Gi
```

Llama-3.1-8B-Instruct is a gated model on HuggingFace; you must accept the licence on huggingface.co/meta-llama/Llama-3.1-8B-Instruct and create a Secret with your access token before the pod will start.

```bash
kubectl -n llm-system create secret generic huggingface-token \
  --from-literal=token=$HF_TOKEN
```

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vllm
  namespace: llm-system
  labels:
    app: vllm
spec:
  replicas: 1
  selector:
    matchLabels:
      app: vllm
  strategy:
    type: Recreate
  template:
    metadata:
      labels:
        app: vllm
    spec:
      terminationGracePeriodSeconds: 60
      containers:
        - name: vllm
          image: vllm/vllm-openai:latest
          imagePullPolicy: IfNotPresent
          command: ["vllm"]
          args:
            - "serve"
            - "$(MODEL_ID)"
            - "--host"
            - "0.0.0.0"
            - "--port"
            - "8000"
            - "--served-model-name"
            - "$(SERVED_MODEL_NAME)"
            - "--max-model-len"
            - "$(MAX_MODEL_LEN)"
            - "--gpu-memory-utilization"
            - "$(GPU_MEMORY_UTILIZATION)"
            - "--max-num-seqs"
            - "$(MAX_NUM_SEQS)"
          envFrom:
            - configMapRef:
                name: vllm-model-config
          env:
            - name: HF_HOME
              value: /models/huggingface
            - name: HF_TOKEN
              valueFrom:
                secretKeyRef:
                  name: huggingface-token
                  key: token
          ports:
            - name: http
              containerPort: 8000
          volumeMounts:
            - name: model-cache
              mountPath: /models
          startupProbe:
            httpGet:
              path: /health
              port: http
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 36
          livenessProbe:
            httpGet:
              path: /health
              port: http
            periodSeconds: 30
            timeoutSeconds: 5
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /health
              port: http
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 3
          resources:
            requests:
              cpu: "2"
              memory: 24Gi
            limits:
              cpu: "10"
              memory: 64Gi
              nvidia.com/gpu: "1"
      volumes:
        - name: model-cache
          persistentVolumeClaim:
            claimName: vllm-model-cache
---
apiVersion: v1
kind: Service
metadata:
  name: vllm
  namespace: llm-system
  labels:
    app: vllm
spec:
  type: ClusterIP
  selector:
    app: vllm
  ports:
    - name: http
      port: 8000
      targetPort: http
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: vllm-ingress-from-llm-apps
  namespace: llm-system
spec:
  podSelector:
    matchLabels:
      app: vllm
  policyTypes:
    - Ingress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              kubedojo.dev/role: llm-apps
      ports:
        - protocol: TCP
          port: 8000
```

The `Recreate` strategy is intentional for the one-GPU teaching cluster. A
rolling update of a one-replica, one-GPU Deployment often cannot schedule the
new pod until the old pod releases the GPU. A production cluster with enough
accelerators, a warm model cache, and traffic management may choose rolling
updates or a serving platform, but that is not the first lesson. Here the
learner should see one pod leave readiness and another pod enter readiness.

The PVC is equally deliberate. Model weights are large enough that downloading
them on every restart turns a normal pod replacement into an avoidable outage.
A warm cache does not remove model-load time, because the engine still has to
map weights and allocate GPU memory, but it prevents network download time from
becoming part of every failure. The explicit `storageClassName` also prevents a
surprise default storage class from placing model files on slow disks. If your
cluster has separate classes for network storage and local NVMe, model cache
latency is one of the places where that difference becomes visible.

The ConfigMap exists because model parameters are application-facing policy,
not just container startup trivia. `MAX_MODEL_LEN` changes the context window
and therefore the KV-cache pressure. `GPU_MEMORY_UTILIZATION` changes how
aggressively vLLM fills device memory. `MAX_NUM_SEQS` influences concurrency
and queueing. Keeping those values in a ConfigMap makes review easier and lets
the future orchestration module talk about context budgets using names the
cluster already exposes. It also helps a reviewer see whether an outage was
caused by a code change or by a serving-parameter change.

The Service gives the future application a stable name, but it should not be
treated as a public API boundary. It is a cluster-internal endpoint whose
callers are controlled by namespace policy and, in more mature environments,
service identity. That distinction matters when learners later add an
orchestrator. The app should call `vllm.llm-system.svc.cluster.local` from
inside the cluster, not a pod IP, not an Ingress hostname meant for users, and
not a manually copied node address. Stable service discovery is part of the
reason Kubernetes is useful for this stack.

The NetworkPolicy assumes the cluster CNI enforces Kubernetes NetworkPolicy.
Calico, Cilium, and several managed-provider CNIs do; a minimal local cluster
may not. If the rejection test later succeeds from the wrong namespace, do not
debug vLLM. First check whether NetworkPolicy enforcement exists. A policy
object stored by the API server is only useful when the data-plane plugin
actually enforces it.

There is one more practical boundary to keep in mind: this module does not add
end-user authentication to vLLM. The policy keeps the service internal to the
future application namespace, but it does not make the inference server safe to
expose directly to users. That is intentional because the first substrate layer
should prove network reachability and readiness without mixing in user identity,
rate limits, or request authorization. Module 3.2 can then place those concerns
in the orchestration service, where request context and product rules are
available.

Pause and predict: when the vLLM pod starts, should the Service immediately
route traffic to it? The answer should be no. The pod may be Running while it
downloads or loads weights, and the Service should wait until readiness passes.
That single difference is why readiness probes exist.

## Qdrant On Kubernetes

Qdrant belongs in the stack as a stateful dependency, not a sidecar hidden
inside the application pod. The application needs retrieval even when the
orchestrator restarts, and the index needs storage that survives container
replacement. Helm is a reasonable deployment path here because the official
chart already understands StatefulSet storage, service ports, probes, and a
Prometheus ServiceMonitor option. The lesson is not "Helm is magic"; the lesson
is to make the persistence, readiness, and metrics choices explicit.

The operational reality is simple: index size determines startup time. A tiny
collection may be ready seconds after the process starts. A large collection
with payload indexes, many segments, or restored snapshots may take much
longer before search latency is acceptable. Qdrant's current documentation
describes `/healthz`, `/livez`, and `/readyz` endpoints for server status, and
the Helm chart uses `/readyz` for newer Qdrant versions. Some older examples
and wrappers refer to a readiness path generically as `/readiness`; read the
chart template for the image version you deploy and test the exact route before
you turn it into a gate.

Use single replica for the teaching path. The chart can run with
`config.cluster.enabled: true`, and that is the production direction when you
need replication, shard transfer, and node-to-node coordination. In a single
learner cluster, cluster mode adds peer ports, consensus settings, and failure
states before the learner has seen the basic memory service. Start with one
replica, a real PVC, and probes. Scale out after you can explain restart
behavior for one node.

Persistence sizing should start from the collection, not from a generic number
copied out of a sample file. Vector count, vector dimension, payload size,
on-disk indexing, snapshots, and segment compaction all influence disk needs.
The `200Gi` value below is intentionally roomy for a teaching module, but it is
not a universal recommendation. A small document assistant may need far less,
while a production RAG corpus with snapshots can exceed it quickly. The right
habit is to record expected vector count and snapshot policy next to the Helm
values so storage growth is reviewed with the deployment.

Qdrant also has a different cost profile from vLLM. It usually does not need a
GPU, but it can become expensive through persistent high-performance storage,
memory for indexes and caches, and replicas that multiply data. That means the
cost knobs are different: reduce unused collections, tune payload indexes,
choose storage classes deliberately, set snapshot retention, and avoid enabling
cluster mode before availability requirements justify it. Treating all LLM
stack cost as GPU cost misses the memory layer's quieter but persistent spend.

```yaml
# qdrant-values.yaml
replicaCount: 1

image:
  repository: docker.io/qdrant/qdrant
  tag: "v1.15.3"

service:
  type: ClusterIP
  ports:
    - name: http
      port: 6333
      targetPort: 6333
      protocol: TCP
      checksEnabled: true
    - name: grpc
      port: 6334
      targetPort: 6334
      protocol: TCP
      checksEnabled: false
    - name: p2p
      port: 6335
      targetPort: 6335
      protocol: TCP
      checksEnabled: false

persistence:
  accessModes:
    - ReadWriteOnce
  storageClassName: fast-nvme
  size: 200Gi

resources:
  requests:
    cpu: "1"
    memory: 4Gi
  limits:
    cpu: "4"
    memory: 16Gi

readinessProbe:
  enabled: true
  initialDelaySeconds: 10
  periodSeconds: 10
  timeoutSeconds: 2
  failureThreshold: 18

livenessProbe:
  enabled: true
  initialDelaySeconds: 30
  periodSeconds: 30
  timeoutSeconds: 2
  failureThreshold: 4

startupProbe:
  enabled: true
  initialDelaySeconds: 10
  periodSeconds: 10
  timeoutSeconds: 2
  failureThreshold: 60

metrics:
  serviceMonitor:
    enabled: true
    additionalLabels:
      release: kube-prometheus-stack
    scrapeInterval: 30s
    scrapeTimeout: 10s
    targetPort: http
    targetPath: "/metrics"

config:
  cluster:
    enabled: false
  service:
    enable_tls: false
```

Install the chart with explicit namespace and values. The namespace is the same
`llm-system` namespace as vLLM because both are backing services. The future
application namespace will call them through Services but will not host their
stateful storage.

```bash
helm repo add qdrant https://qdrant.github.io/qdrant-helm
helm repo update
helm upgrade --install qdrant qdrant/qdrant \
  --namespace llm-system \
  --values qdrant-values.yaml
```

The Qdrant ServiceMonitor covers Qdrant's own `/metrics` endpoint. GPU metrics
usually come from the DCGM exporter that the NVIDIA GPU Operator installs. If
your Prometheus operator does not already discover that exporter, create a
separate ServiceMonitor for the exporter service labels used in your cluster.
The exact labels vary by installation, so treat the selector below as a pattern
to align with `kubectl get svc -A --show-labels | grep dcgm`.

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: dcgm-exporter
  namespace: gpu-operator
  labels:
    release: kube-prometheus-stack
spec:
  namespaceSelector:
    matchNames:
      - gpu-operator
  selector:
    matchLabels:
      app.kubernetes.io/name: dcgm-exporter
  endpoints:
    - port: metrics
      path: /metrics
      interval: 30s
      scrapeTimeout: 10s
```

The reason to mention DCGM in this backing-service module is not to teach
autoscaling yet. Module 3.3 will handle scaling signals. Here you only need the
metrics surface to exist so later modules can observe GPU utilization, memory
pressure, and inference-side symptoms next to Qdrant request metrics. Without
that shared metrics substrate, an application timeout becomes guesswork.

Metrics also help separate warm-up from failure. A Qdrant pod that is not ready
but steadily reading segments from disk is different from a pod with repeated
crashes. A vLLM pod with high GPU memory use and no ready endpoint during model
load is different from a pod whose process is dead. Prometheus will not fix the
stack, but it gives the future operator enough evidence to decide whether to
wait, restart, resize, or roll back. This evidence is the bridge between a
classroom exercise and a production incident review.

Worked example: suppose Qdrant restarts after a node drain. The process may be
alive quickly, but `/readyz` can still return a non-success status while the
index is not ready to serve search. During that period, Kubernetes should keep
the pod out of Service endpoints. The orchestrator should see retrieval errors
or timeouts if it bypasses readiness, but a normal Service call should recover
once the pod becomes ready again. That behavior is exactly what the failure
injection section will teach you to observe.

## Verifying The Stack End To End

Verification starts from inside the cluster because these are internal
services. Do not begin with an Ingress, a browser, or a public endpoint. The
application will eventually run as a pod, so use temporary pods to test the same
DNS names and network boundaries the application will use. This catches the
mistakes that local port-forward testing hides: wrong namespace labels,
NetworkPolicy gaps, Service selectors with no endpoints, and readiness delays.

First confirm that both backing services have ready endpoints. This is a
Kubernetes-level check, not a model-level check. It tells you whether the
Service has pods that passed readiness and can receive traffic.

This first check is intentionally boring. Boring checks are valuable because
they remove entire classes of possibility before you spend time on model
behavior. If `kubectl get endpoints` shows no addresses for `vllm`, a chat
completion failure is not a prompt problem. If Qdrant has no ready endpoint, a
retrieval failure is not an embedding-quality problem. Always prove the Service
endpoint layer before interpreting application errors, because Kubernetes will
not route traffic to pods that are outside the Service selector or failing
readiness.

```bash
kubectl get pods -n llm-system -o wide
kubectl get endpoints -n llm-system vllm qdrant
kubectl rollout status deployment/vllm -n llm-system --timeout=10m
kubectl rollout status statefulset/qdrant -n llm-system --timeout=10m
```

Next create a temporary curl pod in the allowed application namespace. The pod
uses the `curlimages/curl` image because it contains the HTTP client needed for
the tests and keeps the probe environment small.

```bash
kubectl run curl-client \
  --namespace llm-apps \
  --image=curlimages/curl:8.11.1 \
  --restart=Never \
  --command -- sleep 3600

kubectl wait pod/curl-client \
  --namespace llm-apps \
  --for=condition=Ready \
  --timeout=90s
```

Probe vLLM's readiness and model API through the internal Service name. If your
chosen vLLM image exposes `/health` rather than split live/ready endpoints,
adjust this command to the path you configured in the Deployment. The point is
to test the same readiness route Kubernetes uses, from the same namespace the
application will use.

```bash
kubectl exec -n llm-apps curl-client -- \
  curl -fsS http://vllm.llm-system.svc.cluster.local:8000/health
```

Now send a minimal OpenAI-compatible chat request. The small token budget keeps
the smoke test cheap and avoids confusing a slow generation with a broken
Service. The model name must match the `SERVED_MODEL_NAME` configured for vLLM.

```bash
kubectl exec -n llm-apps curl-client -- \
  curl -fsS -X POST \
    http://vllm.llm-system.svc.cluster.local:8000/v1/chat/completions \
    -H 'Content-Type: application/json' \
    -d '{
      "model": "meta-llama/Llama-3.1-8B-Instruct",
      "messages": [
        {
          "role": "system",
          "content": "You are a concise Kubernetes assistant."
        },
        {
          "role": "user",
          "content": "In one sentence, what does a Kubernetes Service do?"
        }
      ],
      "temperature": 0.1,
      "max_tokens": 64
    }'
```

The exact text will vary, but the response shape should look like this. The
fields that matter for the smoke test are `object`, `model`, `choices`, and a
message body. Do not assert the natural-language answer byte-for-byte in a
health check; assert the API shape, status code, and whether the answer is
present.

A smoke test should be cheap, deterministic enough to detect wiring problems,
and modest about what it proves. The request above does not prove answer
quality, safety, or retrieval correctness. It proves that the application
namespace can reach the inference Service, that the model name is accepted, and
that the OpenAI-compatible route returns a valid chat response. Module 3.3 will
teach quality gates; using a smoke test as an eval gate creates false
confidence because a fluent sentence can still be wrong or ungrounded.

```json
{
  "id": "chatcmpl-kubedojo-demo",
  "object": "chat.completion",
  "created": 1779210000,
  "model": "meta-llama/Llama-3.1-8B-Instruct",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "A Kubernetes Service gives pods a stable network endpoint and load-balances traffic to ready backends."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 32,
    "completion_tokens": 20,
    "total_tokens": 52
  }
}
```

Probe Qdrant from the same allowed namespace. Qdrant exposes health and metrics
surfaces separately; health answers whether the service is alive, while metrics
feeds Prometheus. A readiness check should use the path configured by the chart,
which is `/readyz` for current chart versions with modern Qdrant images.

The Qdrant probes should stay separate from a real semantic retrieval test. A
health endpoint can say the server is ready while your collection is empty,
indexed with the wrong vector dimension, or missing the payload fields the
application expects. Those are application-data problems, not substrate
problems. The substrate test says "can the memory service answer?" A later RAG
test says "does the memory service contain the right material and retrieve it
well?" Mixing those questions makes failures harder to triage.

```bash
kubectl exec -n llm-apps curl-client -- \
  curl -fsS http://qdrant.llm-system.svc.cluster.local:6333/healthz

kubectl exec -n llm-apps curl-client -- \
  curl -fsS http://qdrant.llm-system.svc.cluster.local:6333/readyz

kubectl exec -n llm-apps curl-client -- \
  curl -fsS http://qdrant.llm-system.svc.cluster.local:6333/metrics | head
```

Finally prove the NetworkPolicy boundary. Create a second namespace that does
not carry the allowed label, then run the same curl image there. The vLLM call
from `llm-apps` should succeed. The call from the outside namespace should time
out or be rejected, depending on your CNI's enforcement behavior. A fast success
from the outside namespace means the policy is not enforced or the namespace
selector is too broad.

Exit 28 (timeout) means packets are being silently dropped; exit 7 (connection refused) means the CNI is sending TCP RST. Both confirm the policy is enforced — the difference is purely a CNI implementation detail (Cilium and weave-net default to drop; Calico and eBPF data planes often default to RST). A 4xx/5xx HTTP response means the traffic reached the server and the NetworkPolicy is NOT blocking it.

```bash
kubectl create namespace outside-llm-test

kubectl run outside-probe \
  --namespace outside-llm-test \
  --image=curlimages/curl:8.11.1 \
  --restart=Never \
  --command -- sleep 3600

kubectl wait pod/outside-probe \
  --namespace outside-llm-test \
  --for=condition=Ready \
  --timeout=90s

kubectl exec -n outside-llm-test outside-probe -- \
  curl -m 5 -fsS http://vllm.llm-system.svc.cluster.local:8000/health
```

If the outside call fails, keep the failed command in your notes. It is a
positive test result: the stack rejects a caller outside the application
namespace. If the outside call succeeds, inspect `kubectl describe networkpolicy
-n llm-system vllm-ingress-from-llm-apps`, the namespace labels, and the CNI
documentation before changing vLLM. The inference container cannot enforce a
Kubernetes NetworkPolicy by itself.

This deny test is worth running even in a small lab because it trains the habit
of proving negative space. Many tutorials only show the happy path from an
allowed client, but production access boundaries fail when an unintended client
also works. By testing from a namespace with no allow label, you confirm that
the policy is selective rather than decorative. That pattern will matter again
when Module 3.2 adds an orchestration service that should be the only caller
with direct access to inference and memory.

## Failure Injection

Failure injection turns the previous verification steps into operational
vocabulary. You are not trying to create chaos for its own sake. You are
learning what each backend looks like when it disappears, restarts, and returns
to readiness. Module 3.2 will turn these observations into retry and fallback
logic. If you skip this step, you may still write code that retries, but you
will not know which symptoms the code is handling.

Start with vLLM. In one terminal, run a chat request with a slightly larger
token budget so the request stays in flight long enough to observe disruption.
In another terminal, delete the vLLM pod by label. Kubernetes will create a new
pod because the Deployment still desires one replica.

```bash
kubectl exec -n llm-apps curl-client -- \
  curl -v -X POST \
    http://vllm.llm-system.svc.cluster.local:8000/v1/chat/completions \
    -H 'Content-Type: application/json' \
    -d '{
      "model": "meta-llama/Llama-3.1-8B-Instruct",
      "messages": [
        {
          "role": "user",
          "content": "Explain why readiness is different from liveness in Kubernetes."
        }
      ],
      "temperature": 0.2,
      "max_tokens": 256
    }'
```

```bash
kubectl delete pod -n llm-system -l app=vllm
kubectl get pods -n llm-system -w
```

The client may see a connection reset, a connection refused error, an empty
reply, or a 502 if you have a gateway in front of the Service. Qdrant should
remain unchanged because the memory layer did not fail. During the new vLLM
pod's startup, the pod can be Running while readiness still fails. That is the
correct behavior. The Service should not route normal traffic until the
readiness probe passes and the endpoint returns.

Record the symptom using the client's words and the cluster's words. The
client might say "connection refused" while Kubernetes says "no ready
endpoints" and the pod event says "readiness probe failed." Those are three
views of the same restart window. A future retry helper should care about the
client-visible symptom, while an operator should care about the endpoint and
probe state. Keeping both views prevents a common mistake: writing application
retries that mask a persistent deployment problem instead of surfacing it.

Observe the difference with these commands. The first command watches endpoint
availability. The second inspects events if the pod takes longer than expected.
The third confirms that Qdrant remained available while vLLM restarted.

```bash
kubectl get endpoints -n llm-system vllm -w
kubectl describe pod -n llm-system -l app=vllm
kubectl exec -n llm-apps curl-client -- \
  curl -fsS http://qdrant.llm-system.svc.cluster.local:6333/readyz
```

Now delete Qdrant. This time vLLM should stay healthy because inference does
not depend on retrieval. A future orchestration service, however, will fail its
retrieval step before it builds the final prompt. That difference is important:
do not restart vLLM when memory is unavailable, and do not blame Qdrant when a
raw inference-only call succeeds without retrieved context.

```bash
kubectl delete pod -n llm-system -l app.kubernetes.io/name=qdrant
kubectl get pods -n llm-system -w
```

While Qdrant restarts, direct vLLM chat completions should still work if the
model pod is ready. Qdrant readiness may fail until the process and indexes are
ready to serve. An orchestrator that performs retrieval should treat this as a
retrieval failure and decide whether to retry, return a degraded answer, or ask
the user to try again. Module 3.2 will implement that decision in application
code.

This is the first place where the stack starts to feel like an LLM-native
application instead of two unrelated services. A user-facing RAG answer depends
on retrieval and generation, but those dependencies fail differently. If memory
is down and inference is up, the app might still answer from the model alone,
but the answer may be less grounded. If inference is down and memory is up, the
app may retrieve excellent context and still be unable to produce a response.
Those are different user experiences and should not collapse into one generic
error message.

The following helper is a small worked example of the backoff shape the future
orchestrator will need. It is not a complete client. It demonstrates the timing
and exception boundary: transient connection and timeout failures get retried
with exponential backoff and jitter; exhausted retries become a clear
application error that the caller can log or return.

```python
from __future__ import annotations

import random
import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


class BackendUnavailable(RuntimeError):
    """Raised when a backend stays unavailable after bounded retries."""


def call_with_backoff(
    operation_name: str,
    call: Callable[[], T],
    *,
    attempts: int = 5,
    base_delay_seconds: float = 0.5,
    max_delay_seconds: float = 8.0,
) -> T:
    last_error: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            return call()
        except (ConnectionError, TimeoutError) as exc:
            last_error = exc
            if attempt == attempts:
                break
            delay = min(max_delay_seconds, base_delay_seconds * (2 ** (attempt - 1)))
            jitter = random.uniform(0, delay * 0.25)
            time.sleep(delay + jitter)

    raise BackendUnavailable(
        f"{operation_name} unavailable after {attempts} attempts"
    ) from last_error
```

The helper intentionally does not retry every exception. A 400-level validation
error from a backend, a malformed request, or an authentication failure should
not be hidden behind exponential backoff. Retrying those errors adds latency
without improving correctness. The point of this module's failure injection is
to let you distinguish transient backend unavailability from bugs that should
fail fast.

Bounded backoff also protects the backend during recovery. When a pod becomes
ready after restart, many clients may retry at once. Immediate tight-loop
retries can create a burst that slows the recovering service or fills the
inference queue before the first useful request completes. Exponential backoff
with jitter spreads retries across time, giving Kubernetes, the Service, and
the backend a chance to converge. That is why this small helper belongs in the
substrate module even though the real orchestrator code appears next.

## Did You Know?

1. vLLM's OpenAI-compatible server lets an application keep the same endpoint
   style for hosted APIs and self-hosted inference, which is why swapping a
   prototype from a hosted API to a private cluster can be mostly a base-URL
   and model-name change.
2. Kubernetes extended resources such as `nvidia.com/gpu` are not overcommitted
   like CPU can be, so a pod that requests one GPU needs the scheduler to find
   an allocatable device rather than a fractional share by default.
3. Qdrant's official Helm chart enables HTTP readiness checks by default and,
   for newer image versions, renders the readiness path as `/readyz` rather
   than assuming the root path proves search readiness.
4. Prometheus ServiceMonitor is not a Kubernetes core object; it is a custom
   resource from the Prometheus Operator, so a cluster without that operator
   will reject the ServiceMonitor YAML even if Prometheus itself exists.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|----------------|---------------|
| Routing traffic to vLLM as soon as the pod is Running. | The container process starts before model weights are loaded and before the engine can serve generation requests. | Use a readiness probe tied to model-serving readiness and give startup enough time for weight loading. |
| Treating Qdrant like a stateless sidecar. | A local demo stores vectors in memory or on a container filesystem, so restart behavior is invisible. | Deploy Qdrant with a PVC, verify readiness after restart, and size storage for index and snapshot growth. |
| Putting every component in one namespace. | It feels simpler during setup, but it removes the ability to test namespace-scoped access boundaries. | Use a backing-service namespace and an application namespace, then prove NetworkPolicy behavior with temporary pods. |
| Choosing MIG before the learner understands the basic stack. | Hardware partitioning sounds professional, but it adds scheduling and model-sizing complexity to the first exercise. | Start with a full GPU for one learner; introduce MIG when multi-tenant isolation is the actual learning goal. |
| Using a liveness probe to check dependencies. | Teams want one health endpoint to answer every question, so dependency failures trigger unnecessary restarts. | Keep liveness narrow and use readiness to remove a pod from Service endpoints when it cannot serve traffic. |
| Assuming NetworkPolicy exists because the object applied successfully. | The Kubernetes API stores the object even when the cluster CNI does not enforce it. | Test from an allowed namespace and a denied namespace, then verify the CNI supports NetworkPolicy enforcement. |
| Retrying every backend error in the future orchestrator. | Backoff is added as a generic fix for failures without classifying the cause. | Retry transient connection, timeout, and readiness windows; fail fast on malformed requests, auth errors, and validation failures. |

## Quiz

<details>
<summary>Your vLLM pod is Running, but the Service has no endpoints and chat requests time out. What should you check first?</summary>

Check the readiness probe and pod events before debugging the model API client.
A Running pod only means the container process exists; it does not mean the
model is loaded or that Kubernetes considers the pod ready for Service traffic.
Use `kubectl describe pod -n llm-system -l app=vllm` and inspect readiness
failures, startup timing, and the configured health path.

</details>

<details>
<summary>A learner can reach vLLM from `outside-llm-test`, even though the NetworkPolicy only allows `llm-apps`. What is the likely failure class?</summary>

The likely failure class is policy enforcement or selector mismatch, not an
inference problem. Confirm the `llm-apps` namespace label, inspect the
NetworkPolicy namespace selector, and verify the CNI plugin enforces Kubernetes
NetworkPolicy. If the CNI does not enforce it, the policy object can exist while
traffic still flows.

</details>

<details>
<summary>Qdrant restarts during a request. vLLM remains ready, but the user-facing RAG answer fails. Which layer should Module 3.2 handle?</summary>

Module 3.2 should handle this in the orchestration layer because the retrieval
step failed while inference stayed available. Restarting vLLM would not fix a
memory-layer outage. The application should classify the retrieval call as
transient if Qdrant is restarting, apply bounded retry, and decide whether a
degraded answer is acceptable.

</details>

<details>
<summary>Your teaching cluster has one GPU and twenty learners. Should the first version of this module use MIG, time-sharing, or a full GPU per learner?</summary>

If all twenty learners must experiment at the same time, time-sharing may be the
pragmatic workshop choice, but it makes latency less predictable. For the
clearest individual learning path, a full GPU per active learner is easier to
explain. MIG is useful when hardware partitioning and tenant isolation are the
lesson, but it is usually too much complexity for the first substrate module.

</details>

<details>
<summary>After a node drain, Qdrant is alive but readiness keeps failing for several minutes. Why might this be correct?</summary>

The process can be alive before the index is ready to serve search traffic.
Large indexes, payload indexes, or restored snapshots can extend startup time.
Readiness should stay failed until the service can answer retrieval requests
reliably; otherwise the application may receive errors from a pod that only
looks healthy at the process level.

</details>

<details>
<summary>A future orchestrator receives a 400 response from vLLM because the model name is wrong. Should it use exponential backoff?</summary>

No. A wrong model name is a request or configuration error, not a transient
backend restart. Retrying it wastes time and hides the real fix. Backoff should
be reserved for errors that may improve with time, such as connection resets,
timeouts, and readiness windows during pod replacement.

</details>

<details>
<summary>The vLLM pod stays Pending after you apply the Deployment. What two boundaries should you inspect before changing model parameters?</summary>

Inspect ResourceQuota and node allocatable GPU capacity. A namespace quota can
reject or block the pod even when the YAML is valid, and the scheduler may have
no GPU-capable node that matches the request. Only after quota and scheduling
are clear should you tune model length, memory utilization, or CPU and memory
requests.

</details>

## Hands-On Exercise

In this exercise, you will assemble the service substrate and prove the
boundaries. Use a Kubernetes 1.35+ cluster with NVIDIA GPU Operator already
installed, a NetworkPolicy-enforcing CNI, Helm, and access to a storage class
that can back the model and Qdrant PVCs. Replace `fast-nvme` with your actual
storage class if needed.

### Task 1: Create namespaces and quota

Create `llm-system` and `llm-apps`, label `llm-apps`, and apply the
ResourceQuota from the GPU provisioning section.

<details>
<summary>Solution</summary>

```bash
kubectl create namespace llm-system
kubectl create namespace llm-apps
kubectl label namespace llm-apps kubedojo.dev/role=llm-apps
kubectl apply -f llm-system-quota.yaml
kubectl describe resourcequota -n llm-system llm-system-quota
```

</details>

### Task 2: Deploy vLLM as an internal service

Apply the five vLLM resources, wait for rollout, and confirm that the Service
has at least one ready endpoint after model load. If your image exposes only
`/health`, adjust the probe paths consistently before applying the manifest.

<details>
<summary>Solution</summary>

```bash
kubectl apply -f vllm-service.yaml
kubectl rollout status deployment/vllm -n llm-system --timeout=10m
kubectl get endpoints -n llm-system vllm
kubectl describe pod -n llm-system -l app=vllm
```

</details>

### Task 3: Deploy Qdrant with persistent storage and metrics

Install Qdrant with the Helm values from this module, then confirm the
StatefulSet and ServiceMonitor resources exist. If your Prometheus operator
uses a different release label, update the `metrics.serviceMonitor` labels
before installing.

<details>
<summary>Solution</summary>

```bash
helm repo add qdrant https://qdrant.github.io/qdrant-helm
helm repo update
helm upgrade --install qdrant qdrant/qdrant \
  --namespace llm-system \
  --values qdrant-values.yaml
kubectl rollout status statefulset/qdrant -n llm-system --timeout=10m
kubectl get pvc -n llm-system
kubectl get servicemonitor -A | grep qdrant
```

</details>

### Task 4: Verify allowed application access

Create the `curl-client` pod in `llm-apps`, call vLLM's chat completion
endpoint, and call Qdrant's health and readiness endpoints through Service DNS.

<details>
<summary>Solution</summary>

```bash
kubectl run curl-client \
  --namespace llm-apps \
  --image=curlimages/curl:8.11.1 \
  --restart=Never \
  --command -- sleep 3600
kubectl wait pod/curl-client -n llm-apps --for=condition=Ready --timeout=90s
kubectl exec -n llm-apps curl-client -- \
  curl -fsS http://qdrant.llm-system.svc.cluster.local:6333/readyz
kubectl exec -n llm-apps curl-client -- \
  curl -fsS http://vllm.llm-system.svc.cluster.local:8000/health
```

</details>

### Task 5: Verify denied namespace access

Create a temporary pod in an unlabelled namespace and prove that the vLLM
NetworkPolicy rejects traffic from outside the application namespace.

<details>
<summary>Solution</summary>

```bash
kubectl create namespace outside-llm-test
kubectl run outside-probe \
  --namespace outside-llm-test \
  --image=curlimages/curl:8.11.1 \
  --restart=Never \
  --command -- sleep 3600
kubectl wait pod/outside-probe -n outside-llm-test --for=condition=Ready --timeout=90s
kubectl exec -n outside-llm-test outside-probe -- \
  curl -m 5 -fsS http://vllm.llm-system.svc.cluster.local:8000/health
```

The final command should fail by timeout or rejection. If it succeeds, inspect
namespace labels, NetworkPolicy selectors, and CNI enforcement.

</details>

### Task 6: Inject backend failure and record symptoms

Delete the vLLM pod, then delete the Qdrant pod. For each deletion, record what
the client sees, which Service endpoints change, and which backend remains
healthy.

<details>
<summary>Solution</summary>

```bash
kubectl delete pod -n llm-system -l app=vllm
kubectl get endpoints -n llm-system vllm -w
kubectl delete pod -n llm-system -l app.kubernetes.io/name=qdrant
kubectl get endpoints -n llm-system qdrant -w
```

</details>

Success criteria:

- [ ] `llm-system` has a ResourceQuota limiting GPU, storage, pod, CPU, and memory consumption.
- [ ] vLLM is reachable from `llm-apps` through the `vllm.llm-system.svc.cluster.local` Service name after readiness passes.
- [ ] Qdrant is deployed with a PVC, reports readiness through the chart's readiness path, and exposes metrics for Prometheus scraping.
- [ ] A pod in an unlabelled namespace cannot reach the vLLM inference Service when NetworkPolicy is enforced.
- [ ] Deleting the vLLM pod interrupts inference while Qdrant stays ready.
- [ ] Deleting the Qdrant pod interrupts retrieval readiness while direct vLLM inference remains available.

## Sources

- https://github.com/vllm-project/vllm
- https://docs.vllm.ai
- https://docs.vllm.ai/en/latest/serving/openai_compatible_server.html
- https://github.com/bentoml/BentoML
- https://github.com/kserve/kserve
- https://github.com/ray-project/ray
- https://github.com/NVIDIA/gpu-operator
- https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/index.html
- https://github.com/qdrant/qdrant
- https://github.com/qdrant/qdrant-helm
- https://qdrant.tech/documentation/guides/monitoring/
- https://github.com/prometheus-operator/prometheus-operator
- https://kubernetes.io/docs/concepts/policy/resource-quotas/
- https://kubernetes.io/docs/concepts/services-networking/network-policies/
- https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/

## Next Module

The backing services are healthy — now build the application that drives them.
[Wiring the LLM App: The Orchestration Layer](../module-3.2-orchestration-layer/)
adds the orchestration service that calls vLLM and Qdrant, persists state, and
handles backend failure explicitly.

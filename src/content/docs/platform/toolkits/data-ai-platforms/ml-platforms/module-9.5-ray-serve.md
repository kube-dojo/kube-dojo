---
citations_verified: true
title: "Module 9.5: Ray Serve - Distributed Model Serving"
slug: platform/toolkits/data-ai-platforms/ml-platforms/module-9.5-ray-serve
sidebar:
  order: 6
---

## Complexity: `[COMPLEX]`

**Time to Complete**: 90 minutes  
**Prerequisites**: Module 9.4 (vLLM), Basic Python, Kubernetes workload fundamentals, familiarity with CPU and GPU resource requests

## Learning Outcomes

After completing this module, you will be able to:

- **Design** a Ray Serve deployment that separates cluster lifecycle, model lifecycle, and request routing concerns on Kubernetes.
- **Configure** KubeRay `RayCluster` and `RayService` resources with CPU, GPU, autoscaling, and health-check settings that match inference workload behavior.
- **Implement** a Ray Serve application that composes multiple model stages into a production-style inference pipeline.
- **Debug** common Ray Serve failures by tracing symptoms through Kubernetes resources, Ray actors, Serve replicas, and application logs.
- **Evaluate** when Ray Serve is a better fit than KServe, Triton, Seldon Core, or a plain HTTP service for distributed AI workloads.

## Why This Module Matters

A platform team is asked to productionize a document-intelligence system that worked during a demo. The demo ran on one large GPU machine with a notebook, a local vector store, and a few helper functions. Production is different: OCR needs CPU replicas, embedding needs smaller GPU slices, generation needs larger GPU allocations, and the business wants every customer request to pass through the same API without learning which model lives where.

The first attempt uses separate Kubernetes Deployments for every model stage. It looks familiar to the platform team, but the system becomes hard to operate. The OCR pods scale on CPU load, the embedding pods sit idle between bursts, the generation pods queue requests during traffic spikes, and every retry rule is duplicated in application code. The team can scale each service, yet the pipeline itself has no shared view of work in flight.

Ray Serve changes the shape of the problem. Instead of treating every model as a separate web service, Ray Serve treats each model stage as a distributed deployment inside a Ray application. KubeRay then gives Kubernetes a native way to manage the Ray runtime, the worker pods, and the Serve application. This is not a replacement for Kubernetes; it is a compute layer that lets Kubernetes host a distributed Python serving system.

Ray Serve matters because many AI platforms are no longer serving one model behind one endpoint. They are serving chains of models, preprocessors, rankers, retrievers, safety filters, and generators with different resource profiles. A senior platform engineer needs to decide where Kubernetes should own scheduling, where Ray should own distributed execution, and where application code should own model behavior. This module teaches that boundary.

## Ray Serve in the Serving Stack

[Ray Serve is an HTTP serving framework built on top of Ray](https://raw.githubusercontent.com/ray-project/ray/ray-2.9.0/doc/source/serve/index.md). Ray provides distributed actors, tasks, scheduling, and resource accounting. Serve adds long-running deployments, request routing, autoscaling, health checks, and composition for online inference. KubeRay adds Kubernetes custom resources so that platform teams can manage Ray clusters and Serve applications through normal cluster workflows.

A beginner mistake is to think of Ray Serve as just another Python web framework. That mental model misses the most important part. A Flask or FastAPI service usually runs inside one process per pod, while Ray Serve can route one request across multiple distributed actors that may live on different pods and nodes. The HTTP endpoint is only the front door; the useful work happens inside a distributed graph of deployments.

A senior mistake is to assume Ray Serve replaces all other serving tools. It does not. Triton may be stronger for tightly optimized low-latency GPU inference of supported model formats. KServe may be a better fit when an organization standardizes on Knative-based model serving. Ray Serve is strongest when Python-native composition, heterogeneous resource allocation, and distributed orchestration are the hard parts.

```ascii
┌────────────────────────────────────────────────────────────────────────────┐
│                         Ray Serve on Kubernetes                            │
│                                                                            │
│  Client Request                                                             │
│       │                                                                    │
│       ▼                                                                    │
│  ┌────────────────────┐        ┌────────────────────────────────────────┐   │
│  │ Kubernetes Service │───────▶│ Ray Serve HTTP Proxy                   │   │
│  └────────────────────┘        └────────────────────────────────────────┘   │
│                                            │                               │
│                                            ▼                               │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ Ray Serve Application                                                │   │
│  │                                                                      │   │
│  │  ┌──────────────┐     ┌──────────────┐     ┌────────────────────┐   │   │
│  │  │ Preprocessor │────▶│ Retriever    │────▶│ Generator          │   │   │
│  │  │ CPU actors   │     │ CPU/GPU      │     │ GPU actors         │   │   │
│  │  └──────────────┘     └──────────────┘     └────────────────────┘   │   │
│  │                                                                      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                            │                               │
│                                            ▼                               │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ Ray Runtime: scheduling, object refs, actor placement, resources      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                            │                               │
│                                            ▼                               │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ Kubernetes: pods, nodes, GPUs, services, namespaces, operator control │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────┘
```

The diagram is intentionally layered. Kubernetes still owns pods, nodes, services, and GPU devices. Ray owns distributed execution inside the cluster. Ray Serve owns request routing and deployment lifecycle inside Ray. Your application code owns model initialization, input validation, model calls, and response shape. Keeping those boundaries clear prevents many production incidents.

**Pause and predict:** If a request passes through three Ray Serve deployments and the middle deployment is slow, which part should scale first: the Kubernetes Service, the Ray head pod, the slow Serve deployment, or every worker pod? Write down your answer before continuing. The best first move is usually to scale the slow Serve deployment, because the queue forms at the stage that cannot consume work quickly enough. Scaling the Service does not add model capacity, and scaling every pod may waste resources.

| Layer | Owns | Common configuration | Failure symptom |
|---|---|---|---|
| Kubernetes | Pods, services, GPU devices, namespaces | `resources`, `nodeSelector`, tolerations, Services | Pod pending, image pull errors, GPU unavailable |
| KubeRay | Ray cluster and Ray service lifecycle | `RayCluster`, `RayService`, worker groups | Ray head unavailable, workers not joining |
| Ray runtime | Actors, tasks, object refs, placement | `num_cpus`, `num_gpus`, placement behavior | Actor pending, resource deadlock, worker crash |
| Ray Serve | HTTP routing, deployments, replicas, autoscaling | `num_replicas`, `autoscaling_config`, route prefix | Request queueing, replica unhealthy, route missing |
| Application code | Model loading, validation, inference logic | Python classes, request handlers, model clients | Exceptions, bad responses, slow model calls |

The practical lesson is that platform debugging follows the same layers. If the pod cannot start, look at Kubernetes first. If Ray workers do not join, inspect KubeRay and Ray startup logs. If a deployment has no healthy replicas, inspect Ray Serve state. If the replica is healthy but responses are wrong, inspect application code. Randomly changing autoscaling settings before locating the failing layer usually creates more noise.

## Ray Architecture and KubeRay Resources

[A Ray cluster has one head node and zero or more worker nodes](https://raw.githubusercontent.com/ray-project/ray/master/doc/source/cluster/key-concepts.rst). The head node runs coordination components, including the Global Control Store, the dashboard, and often the Serve controller. Worker nodes run Ray workers that execute tasks and actors. In Kubernetes, these nodes are represented by pods managed by KubeRay custom resources.

The head node should be treated as control-plane-like infrastructure for the Ray cluster. It is not the place to pack all expensive inference work unless the deployment is tiny. For production serving, the head pod normally exposes dashboard, client, and Serve ports while worker pods provide the CPU and GPU capacity for model replicas. This separation makes failures easier to reason about and keeps model resource pressure away from coordination.

```ascii
┌────────────────────────────────────────────────────────────────────────────┐
│                              Ray Cluster                                   │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ Head Pod                                                             │  │
│  │                                                                      │  │
│  │  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────┐ │  │
│  │  │ Global Control     │  │ Ray Dashboard      │  │ Serve          │ │  │
│  │  │ Store              │  │ port 8265          │  │ Controller     │ │  │
│  │  └────────────────────┘  └────────────────────┘  └────────────────┘ │  │
│  │             │                         │                    │          │  │
│  │             └─────────────────────────┼────────────────────┘          │  │
│  │                                       ▼                               │  │
│  │                              ┌────────────────┐                       │  │
│  │                              │ Head Raylet    │                       │  │
│  │                              └────────────────┘                       │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────┐ │
│  │ Worker Pod A         │  │ Worker Pod B         │  │ Worker Pod C     │ │
│  │                      │  │                      │  │                  │ │
│  │ ┌──────────────────┐ │  │ ┌──────────────────┐ │  │ ┌──────────────┐ │ │
│  │ │ Raylet           │ │  │ │ Raylet           │ │  │ │ Raylet       │ │ │
│  │ └──────────────────┘ │  │ └──────────────────┘ │  │ └──────────────┘ │ │
│  │ ┌──────────────────┐ │  │ ┌──────────────────┐ │  │ ┌──────────────┐ │ │
│  │ │ CPU actors       │ │  │ │ GPU actors       │ │  │ │ GPU actors   │ │ │
│  │ └──────────────────┘ │  │ └──────────────────┘ │  │ └──────────────┘ │ │
│  └──────────────────────┘  └──────────────────────┘  └──────────────────┘ │
└────────────────────────────────────────────────────────────────────────────┘
```

KubeRay exposes several resources, but two matter most for serving. [`RayCluster` creates and manages a Ray runtime](https://raw.githubusercontent.com/ray-project/ray/ray-2.9.0/doc/source/cluster/kubernetes/getting-started.md). `RayService` manages both a Ray cluster configuration and a Ray Serve application configuration. A platform team that wants a stable online endpoint usually prefers `RayService`, because it gives the operator enough information to handle service health and application updates together.

A `RayCluster` is still useful when learners are experimenting, running jobs, or separating cluster provisioning from application deployment. In mature platforms, the decision is often organizational as much as technical. If one platform team owns shared Ray clusters and application teams deploy Serve apps separately, `RayCluster` may be managed by the platform. If each serving application needs its own isolated cluster lifecycle, `RayService` is simpler to reason about.

| Resource | Use it when | What it manages | What it does not solve by itself |
|---|---|---|---|
| `RayCluster` | You want an explicit Ray runtime to run jobs, notebooks, or manually deployed Serve apps | Head pod, worker groups, Ray startup parameters | Application rollout, Serve config health, route management |
| `RayService` | You want Kubernetes to manage a Ray Serve application and its backing Ray cluster together | Ray cluster plus Serve application config | Model correctness, data validation, business retry behavior |
| `RayJob` | You want to run batch or training work on Ray | Job submission and lifecycle | Long-running online inference endpoint behavior |
| Kubernetes `Service` | You need stable networking to the head or Serve proxy | Cluster IP and port access | Distributed scheduling, model composition, actor placement |

The distinction becomes important during upgrades. Updating a `RayCluster` changes the runtime capacity or Ray version. Updating a `RayService` can change both runtime capacity and Serve application code. A careful rollout plan separates these concerns when the risk is high. For example, upgrade Ray images in a staging cluster before changing the model pipeline import path in production.

## Installing KubeRay and Deploying a Ray Cluster

The first operational step is installing the KubeRay operator. The operator watches Ray custom resources and reconciles the Kubernetes objects needed to run Ray. The commands below use `kubectl` for the first command and then introduce the common alias `k` for later commands. In this module, `k` means `kubectl`.

```bash
helm repo add kuberay https://ray-project.github.io/kuberay-helm/
helm repo update

helm install kuberay-operator kuberay/kuberay-operator \
  --namespace ray-system \
  --create-namespace

kubectl get pods -n ray-system
alias k=kubectl
```

The operator installation is cluster infrastructure, so it should usually be owned by a platform team rather than an application repository. Application teams can then own `RayService` manifests inside their normal deployment pipeline. This split matches the usual Kubernetes pattern: platform owns controllers and policy, product teams own workload declarations.

The following `RayCluster` is intentionally CPU-only. A CPU-only cluster is cheaper for learning and lets you debug the Ray and Serve control path before introducing GPU scheduling. The same pattern later extends to GPU worker groups by adding `nvidia.com/gpu` resource limits and a Ray actor option that requests GPUs.

```yaml
apiVersion: ray.io/v1
kind: RayCluster
metadata:
  name: ray-demo-cluster
  namespace: ray-serving
spec:
  rayVersion: "2.9.0"
  headGroupSpec:
    rayStartParams:
      dashboard-host: "0.0.0.0"
    template:
      spec:
        containers:
          - name: ray-head
            image: rayproject/ray:2.9.0-py310
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
              requests:
                cpu: "1"
                memory: "2Gi"
              limits:
                cpu: "2"
                memory: "4Gi"
  workerGroupSpecs:
    - groupName: cpu-workers
      replicas: 2
      minReplicas: 1
      maxReplicas: 4
      rayStartParams: {}
      template:
        spec:
          containers:
            - name: ray-worker
              image: rayproject/ray:2.9.0-py310
              resources:
                requests:
                  cpu: "1"
                  memory: "2Gi"
                limits:
                  cpu: "2"
                  memory: "4Gi"
```

Apply the cluster into its own namespace so that cleanup is safe and resource ownership is clear. In a shared environment, namespace isolation also helps separate RBAC, resource quotas, and network policy. For a production platform, you would add labels, tolerations, and node selectors that match your cluster standards.

```bash
k create namespace ray-serving
k apply -f ray-cluster.yaml
k get rayclusters -n ray-serving
k get pods -n ray-serving -l ray.io/cluster=ray-demo-cluster
```

**Active check:** If the worker pods stay `Pending`, do not change Ray Serve settings first. Inspect Kubernetes scheduling state with `k describe pod` and look for CPU, memory, node selector, taint, or GPU messages. Ray cannot schedule actors onto worker pods that Kubernetes never started.

A GPU worker group adds one more scheduling layer. [Kubernetes must allocate the GPU device to a pod](https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/), and Ray must allocate a GPU resource to an actor. Both sides must agree. If Kubernetes gives the pod one GPU but the Serve deployment asks Ray for two GPUs per replica, that replica will remain pending until enough Ray GPU resources exist.

```yaml
apiVersion: ray.io/v1
kind: RayCluster
metadata:
  name: ray-gpu-cluster
  namespace: ray-serving
spec:
  rayVersion: "2.9.0"
  headGroupSpec:
    rayStartParams:
      dashboard-host: "0.0.0.0"
    template:
      spec:
        containers:
          - name: ray-head
            image: rayproject/ray-ml:2.9.0-py310-gpu
            resources:
              requests:
                cpu: "2"
                memory: "8Gi"
              limits:
                cpu: "4"
                memory: "16Gi"
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
                requests:
                  cpu: "4"
                  memory: "16Gi"
                  nvidia.com/gpu: "1"
                limits:
                  cpu: "8"
                  memory: "32Gi"
                  nvidia.com/gpu: "1"
```

The safest way to learn GPU serving is to validate one layer at a time. First confirm the Kubernetes device plugin exposes GPUs to pods. Next confirm Ray sees GPU resources in the dashboard. Only then deploy a Serve replica that asks for `num_gpus`. This sequence reduces the search space when something fails.

## Building a Ray Serve Application

A Ray Serve application begins with one or more deployments. [A deployment is a Python class or function decorated with `@serve.deployment`](https://raw.githubusercontent.com/ray-project/ray/ray-2.9.0/doc/source/serve/key-concepts.md). Serve creates replicas of that deployment, routes requests to those replicas, and lets deployments call each other through handles. This lets you express a multi-stage inference pipeline without manually creating separate HTTP services for every stage.

The simplest deployment looks like a normal Python request handler. It receives a Starlette `Request`, reads JSON, and returns a JSON-serializable object. The difference is that Ray Serve owns the lifecycle of the class instances, not a standalone ASGI server that you wrote directly.

```python
from ray import serve
from starlette.requests import Request


@serve.deployment(num_replicas=2)
class TextNormalizer:
    async def __call__(self, request: Request) -> dict:
        body = await request.json()
        text = body.get("text", "")
        normalized = " ".join(text.lower().strip().split())
        return {"normalized": normalized}


app = TextNormalizer.bind()
```

Run this application locally in an environment with Ray installed. The command imports `app` from the module and starts a Serve application. In Kubernetes, `RayService` can load the same import path, which is why the final line matters.

```bash
serve run normalizer:app --host 0.0.0.0 --port 8000
```

Test it with a normal HTTP request. The API shape is intentionally boring because production inference endpoints should be easy for callers to use. Complexity belongs behind the endpoint, where Ray Serve can distribute work across replicas and actors.

```bash
curl http://127.0.0.1:8000 \
  -H "Content-Type: application/json" \
  -d '{"text": "  Ray Serve   Routes Requests  "}'
```

**Pause and predict:** What happens if you set `num_replicas=2` but send only one request at a time? You should not expect a speedup for a single synchronous request. Replicas improve concurrency and availability. They help when multiple requests arrive or when one replica is busy, not when one request must pass through one serial model call.

A more realistic application separates stages. The next example uses a normalizer, a retriever, and a generator. The retriever and generator are intentionally lightweight so the code can run without downloading a large model. The structure is the important part: each deployment can have different resource settings and can scale independently.

```python
from ray import serve
from starlette.requests import Request


DOCUMENTS = {
    "kubernetes": "Kubernetes schedules containers, manages desired state, and exposes services.",
    "ray": "Ray provides distributed Python tasks, actors, scheduling, and object references.",
    "serve": "Ray Serve adds HTTP routing, replicas, autoscaling, and deployment composition.",
}


@serve.deployment(ray_actor_options={"num_cpus": 0.25})
class Normalizer:
    def normalize(self, query: str) -> str:
        return " ".join(query.lower().strip().split())


@serve.deployment(ray_actor_options={"num_cpus": 0.5})
class Retriever:
    def retrieve(self, query: str) -> str:
        for key, value in DOCUMENTS.items():
            if key in query:
                return value
        return "No matching document was found."


@serve.deployment(ray_actor_options={"num_cpus": 0.5})
class Generator:
    def generate(self, query: str, context: str) -> str:
        return f"Question: {query}\nAnswer from context: {context}"


@serve.deployment
class RagPipeline:
    def __init__(self, normalizer, retriever, generator):
        self.normalizer = normalizer
        self.retriever = retriever
        self.generator = generator

    async def __call__(self, request: Request) -> dict:
        body = await request.json()
        query = body.get("query", "")

        clean_query = await self.normalizer.normalize.remote(query)
        context = await self.retriever.retrieve.remote(clean_query)
        answer = await self.generator.generate.remote(clean_query, context)

        return {
            "query": query,
            "normalized_query": clean_query,
            "context": context,
            "answer": answer,
        }


normalizer = Normalizer.bind()
retriever = Retriever.bind()
generator = Generator.bind()
app = RagPipeline.bind(normalizer, retriever, generator)
```

[The `.bind()` calls create the deployment graph](https://raw.githubusercontent.com/ray-project/ray/ray-2.9.0/doc/source/serve/model_composition.md). The `.remote()` calls execute methods through Ray handles and return awaitable object references inside the Serve application. This is where Ray Serve differs from a chain of HTTP microservices. You are composing distributed Python actors inside one serving application, not writing service discovery and serialization code for every internal hop.

A production version would add request validation, timeouts, model warmup, observability, and error handling. It might also use a real vector database and a real language model. The learning version keeps the model logic small so that the execution model is visible. When the serving graph is clear, replacing the toy generator with vLLM or another model backend becomes a controlled change.

## Worked Example: Choosing Resources for a Multi-Stage Pipeline

Consider a support-ticket assistant. It receives a customer ticket, strips noisy formatting, retrieves related runbooks, reranks the candidate documents, and asks a generator to draft a response. The stages do not have equal cost. Normalization is cheap CPU work. Retrieval is moderate CPU or network work. Reranking may use a small GPU model. Generation may need a larger GPU allocation.

The goal is not to give every stage the same replica count. The goal is to put capacity where the queue forms. If normalization takes ten milliseconds and generation takes two seconds, adding ten normalizer replicas will not fix generation latency. A good platform design starts with the bottleneck and assigns resources from there.

```ascii
┌────────────────────────────────────────────────────────────────────────────┐
│                         Support Ticket Assistant                           │
│                                                                            │
│  Incoming Ticket                                                            │
│       │                                                                    │
│       ▼                                                                    │
│  ┌──────────────────┐   cheap CPU    ┌──────────────────┐   network/CPU   │
│  │ Normalize Text   │───────────────▶│ Retrieve Docs    │────────────────┐ │
│  │ 2 replicas       │                │ 4 replicas       │                │ │
│  └──────────────────┘                └──────────────────┘                │ │
│                                                                           ▼ │
│  ┌──────────────────┐   small GPU    ┌──────────────────┐   larger GPU    │
│  │ Rerank Docs      │───────────────▶│ Generate Answer  │────────────────┘ │
│  │ 2 replicas       │                │ 1-3 replicas     │                  │
│  └──────────────────┘                └──────────────────┘                  │
│                                                                            │
│  Capacity decision: scale the stage whose queue grows under representative  │
│  traffic, then verify that upstream and downstream stages remain healthy.   │
└────────────────────────────────────────────────────────────────────────────┘
```

A worked allocation might begin with small CPU settings for normalization, more replicas for retrieval, fractional GPU for reranking, and full GPU for generation. This is not a universal recipe. It is a hypothesis that should be validated with load tests and dashboard metrics. The point is that Ray Serve lets you express different resource shapes inside one composed application.

```python
from ray import serve


@serve.deployment(
    num_replicas=2,
    ray_actor_options={"num_cpus": 0.25},
)
class TicketNormalizer:
    def normalize(self, ticket: str) -> str:
        return " ".join(ticket.replace("\n", " ").lower().split())


@serve.deployment(
    autoscaling_config={
        "min_replicas": 2,
        "max_replicas": 6,
        "target_num_ongoing_requests_per_replica": 8,
    },
    ray_actor_options={"num_cpus": 0.5},
)
class RunbookRetriever:
    def retrieve(self, ticket: str) -> list[str]:
        return [
            "Check recent deployment events.",
            "Compare failing namespace limits with requested resources.",
            "Inspect application logs around the first failing request.",
        ]


@serve.deployment(
    num_replicas=2,
    ray_actor_options={"num_gpus": 0.25},
)
class Reranker:
    def rerank(self, ticket: str, docs: list[str]) -> list[str]:
        return sorted(docs, key=len, reverse=True)


@serve.deployment(
    autoscaling_config={
        "min_replicas": 1,
        "max_replicas": 3,
        "target_num_ongoing_requests_per_replica": 2,
        "upscale_delay_s": 15,
        "downscale_delay_s": 120,
    },
    ray_actor_options={"num_gpus": 1},
)
class AnswerGenerator:
    def generate(self, ticket: str, docs: list[str]) -> str:
        joined = " ".join(docs)
        return f"Draft response for ticket '{ticket[:80]}': {joined}"
```

Now reason about the allocation. The retriever can scale wider because it is cheaper and has a higher concurrency target. The generator has a lower queue target because each request is expensive and user-visible latency rises quickly when generation queues grow. The reranker uses fractional GPU because a smaller model may not need an entire accelerator, but that choice must be verified under realistic traffic.

**Active check:** Suppose the dashboard shows generator replicas are healthy, GPU utilization is high, and `num_ongoing_requests` for the generator keeps rising. Which setting would you evaluate first? A strong answer is to increase `max_replicas` if the cluster has more GPU capacity, reduce per-request generation cost if it does not, or lower the queue target if latency is more important than throughput. Increasing retriever replicas would not address the bottleneck.

| Stage | Resource shape | Scaling signal | First tuning move |
|---|---|---|---|
| Normalizer | Small CPU | CPU saturation or request backlog | Add modest replicas only if it queues |
| Retriever | CPU plus network | Ongoing requests and external latency | Scale replicas and watch downstream pressure |
| Reranker | Fractional GPU | GPU utilization and method latency | Validate fractional packing under load |
| Generator | Full GPU | Queue depth, latency, GPU utilization | Tune `max_replicas`, batching, and output length |
| Pipeline router | Small CPU | HTTP errors and handler latency | Keep logic thin and avoid blocking calls |

The worked example also shows why application design and platform design must meet. If the generator accepts unlimited prompt length, no autoscaler can fully protect latency. If the retriever sometimes blocks on a slow external store, the pipeline needs timeouts and graceful error responses. Ray Serve gives the infrastructure tools, but the application must still behave like a production service.

## Deploying Ray Serve with RayService

A `RayService` packages the Ray cluster configuration and the Serve application configuration into one Kubernetes resource. This is usually the right abstraction for [a production endpoint that should survive restarts and be reconciled by the operator](https://raw.githubusercontent.com/ray-project/ray/ray-2.9.0/doc/source/cluster/kubernetes/user-guides/rayservice.md). [The `serveConfigV2` block describes the application name, route prefix, import path, runtime environment, and Serve deployment settings](https://raw.githubusercontent.com/ray-project/ray/ray-2.9.0/doc/source/cluster/kubernetes/user-guides/rayservice.md).

The example below assumes your application code is available to the Ray runtime. In production, that usually means building it into the image, using a versioned package, or pointing `runtime_env` at a controlled artifact. Copying files into a running pod is acceptable for a lab but not for repeatable production delivery.

```yaml
apiVersion: ray.io/v1
kind: RayService
metadata:
  name: support-assistant
  namespace: ray-serving
spec:
  serviceUnhealthySecondThreshold: 900
  deploymentUnhealthySecondThreshold: 300
  serveConfigV2: |
    applications:
      - name: support-assistant
        route_prefix: /
        import_path: support_app:app
        runtime_env:
          pip:
            - starlette
        deployments:
          - name: TicketNormalizer
            num_replicas: 2
            ray_actor_options:
              num_cpus: 0.25
          - name: RunbookRetriever
            autoscaling_config:
              min_replicas: 2
              max_replicas: 6
              target_num_ongoing_requests_per_replica: 8
            ray_actor_options:
              num_cpus: 0.5
          - name: Reranker
            num_replicas: 2
            ray_actor_options:
              num_gpus: 0.25
          - name: AnswerGenerator
            autoscaling_config:
              min_replicas: 1
              max_replicas: 3
              target_num_ongoing_requests_per_replica: 2
            ray_actor_options:
              num_gpus: 1
  rayClusterConfig:
    rayVersion: "2.9.0"
    headGroupSpec:
      rayStartParams:
        dashboard-host: "0.0.0.0"
      template:
        spec:
          containers:
            - name: ray-head
              image: rayproject/ray-ml:2.9.0-py310-gpu
              ports:
                - containerPort: 8265
                  name: dashboard
                - containerPort: 8000
                  name: serve
              resources:
                requests:
                  cpu: "2"
                  memory: "8Gi"
                limits:
                  cpu: "4"
                  memory: "16Gi"
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
                  requests:
                    cpu: "4"
                    memory: "16Gi"
                    nvidia.com/gpu: "1"
                  limits:
                    cpu: "8"
                    memory: "32Gi"
                    nvidia.com/gpu: "1"
```

The most important field in the Serve configuration is `import_path`. It tells Ray Serve what Python object to import and run. If the import path is wrong, Kubernetes may show healthy pods while Ray Serve has no healthy application. This is a common source of confusion because cluster health and application health are related but not identical.

Apply and inspect the resource through Kubernetes first. Then move inward to Ray-specific state. This outside-in debugging pattern keeps you from assuming Ray is broken when the manifest never reconciled, or assuming Kubernetes is broken when the Python import failed.

```bash
k apply -f support-assistant-rayservice.yaml
k get rayservices -n ray-serving
k describe rayservice support-assistant -n ray-serving
k get pods -n ray-serving -l ray.io/cluster=support-assistant-raycluster
```

After the pods are running, forward the Serve port and test the route. Use `127.0.0.1` for local testing so the command is explicit about the loopback address. In a real environment, you would expose the service through the platform's ingress, gateway, or internal service mesh policy.

```bash
k port-forward svc/support-assistant-head-svc 8000:8000 -n ray-serving

curl http://127.0.0.1:8000 \
  -H "Content-Type: application/json" \
  -d '{"ticket": "Deployment failed after a new image rollout. Pods restart repeatedly."}'
```

If the request fails, read the error at the right layer. A connection failure suggests Service, port-forward, or pod readiness. A route not found suggests Serve routing or application import. A JSON parsing error suggests request shape or application code. A long delay suggests model initialization, queueing, or insufficient replicas.

## Autoscaling, Batching, and GPU Allocation

[Ray Serve autoscaling is based on ongoing requests per replica](https://raw.githubusercontent.com/ray-project/ray/ray-2.9.0/doc/source/serve/autoscaling-guide.md). This matters because online inference often queues before CPU or GPU utilization looks obviously saturated. A replica running a large model may be fully committed with only a few active requests. A lightweight preprocessor may handle many concurrent requests before becoming the bottleneck.

The main autoscaling setting is `target_num_ongoing_requests_per_replica`. A lower target protects latency by scaling sooner, but it can consume more resources. A higher target improves resource efficiency, but it can increase tail latency. There is no perfect default; the right value depends on model cost, request size, latency objective, and cold-start behavior.

```python
from ray import serve


@serve.deployment(
    autoscaling_config={
        "min_replicas": 1,
        "max_replicas": 5,
        "target_num_ongoing_requests_per_replica": 4,
        "upscale_delay_s": 10,
        "downscale_delay_s": 90,
    },
    ray_actor_options={"num_cpus": 1},
)
class AutoscaledClassifier:
    def classify(self, text: str) -> dict:
        label = "urgent" if "outage" in text.lower() else "normal"
        return {"label": label}
```

Batching is a separate lever. Autoscaling adds replicas; [batching makes each replica process multiple compatible requests together](https://raw.githubusercontent.com/ray-project/ray/ray-2.9.0/doc/source/serve/advanced-guides/dyn-req-batch.md). Batching is useful when the model backend gains efficiency from larger batches, especially on GPUs. It is harmful when batching adds wait time without improving throughput, or when requests have highly variable sizes that cause one large request to delay many small ones.

```python
from ray import serve


@serve.deployment(ray_actor_options={"num_cpus": 1})
class BatchedEmbedder:
    @serve.batch(max_batch_size=8, batch_wait_timeout_s=0.05)
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [[float(len(text)), float(text.count(" "))] for text in texts]

    async def embed(self, text: str) -> list[float]:
        return await self.embed_batch(text)
```

Fractional GPU allocation is a Ray scheduling feature, not a magic memory isolation boundary. [Setting `num_gpus: 0.25` tells Ray's scheduler that four such actors may be placed on one GPU](https://raw.githubusercontent.com/ray-project/ray/ray-2.9.0/doc/source/serve/resource-allocation.md). It does not guarantee that the models will fit in GPU memory or that their kernels will not interfere with each other. [Always validate fractional packing with the real model, real batch sizes, and real traffic](https://raw.githubusercontent.com/ray-project/ray/master/doc/source/serve/llm/user-guides/fractional-gpu.md).

| Setting | What it controls | Good use | Risk if misused |
|---|---|---|---|
| `num_replicas` | Fixed number of deployment replicas | Stable, predictable capacity | Overprovisioning or underprovisioning |
| `min_replicas` | Lower bound for autoscaling | Keep warm capacity available | Idle cost if set too high |
| `max_replicas` | Upper bound for autoscaling | Protect cluster capacity | Queue growth if set too low |
| `target_num_ongoing_requests_per_replica` | Queue target per replica | Balance latency and utilization | Tail latency or resource waste |
| `upscale_delay_s` | Delay before scale-up | Avoid reacting to tiny spikes | Slow response to sudden load |
| `downscale_delay_s` | Delay before scale-down | Avoid thrashing and cold starts | Longer idle resource usage |
| `ray_actor_options.num_gpus` | Ray GPU scheduling request | Match model accelerator needs | Pending replicas or GPU contention |
| `@serve.batch` | Per-replica request batching | Improve model throughput | Added wait time and uneven latency |

A reliable tuning process changes one lever at a time. Start with a fixed small replica count and observe baseline latency. Add autoscaling when you know which stage queues. Add batching only when the backend benefits from batches. Add fractional GPUs only after measuring memory and latency isolation. Production performance work is a measurement loop, not a search for a universal YAML snippet.

## Monitoring and Debugging Ray Serve

Monitoring Ray Serve requires three views. Kubernetes tells you whether pods and services exist. The Ray dashboard tells you whether Ray resources, actors, and Serve deployments are healthy. Application metrics and logs tell you whether model behavior is correct. Senior platform engineers move across all three instead of treating one dashboard as the whole truth.

Forward the dashboard when debugging a lab cluster. In production, access should go through your organization's secure access path rather than an unauthenticated local tunnel. [The dashboard is useful for seeing cluster resources, actor placement, Serve deployment health, and logs](https://raw.githubusercontent.com/ray-project/ray/master/doc/source/ray-observability/getting-started.rst).

```bash
k port-forward svc/ray-demo-cluster-head-svc 8265:8265 -n ray-serving
```

Open `http://127.0.0.1:8265` after the port-forward is active. Look for resource totals first. If Ray reports zero GPUs but Kubernetes scheduled GPU worker pods, the problem is likely inside the image, device plugin integration, or Ray startup environment. If Ray reports GPUs but Serve replicas are pending, compare each deployment's `num_gpus` request with available resources.

Prometheus metrics provide the long-term operational view. Names can vary by Ray version and configuration, so always verify the metrics exposed in your environment. The useful categories remain stable: request latency, request count, replica health, ongoing requests, and cluster resource utilization.

```promql
histogram_quantile(
  0.99,
  sum(rate(ray_serve_request_latency_ms_bucket[5m])) by (le, deployment)
)

sum(rate(ray_serve_num_requests_total[5m])) by (deployment)

sum(ray_serve_num_ongoing_requests) by (deployment)

avg(ray_node_gpu_utilization) by (node)
```

Use symptoms to choose the next command. If pods are not ready, stay with `k get pods`, `k describe pod`, and container logs. If pods are healthy but Serve is failing, inspect `RayService` conditions and Ray dashboard Serve state. If Serve is healthy but latency is high, inspect ongoing requests, replica counts, model logs, and downstream dependencies.

```bash
k get rayservices -n ray-serving
k describe rayservice support-assistant -n ray-serving
k logs -n ray-serving -l ray.io/node-type=head --tail=100
k logs -n ray-serving -l ray.io/node-type=worker --tail=100
```

| Symptom | Likely layer | First checks | Common fix |
|---|---|---|---|
| Worker pod is `Pending` | Kubernetes scheduling | `k describe pod`, quotas, node labels, GPU availability | Adjust requests, labels, tolerations, or capacity |
| Ray worker pod runs but does not join | KubeRay or Ray startup | Worker logs, head service DNS, Ray version mismatch | Fix image, networking, or Ray startup parameters |
| Serve route returns not found | Ray Serve routing | `RayService` status, import path, route prefix | Correct `serveConfigV2` and import path |
| Replica stays unhealthy | Application or resource allocation | Replica logs, model load errors, actor resources | Fix dependencies, image, resource requests, or model path |
| Latency rises during traffic | Serve scaling or model bottleneck | Ongoing requests, latency metrics, GPU utilization | Tune replicas, batching, queue target, or model cost |
| GPU exists but actor is pending | Ray resource scheduling | Dashboard resources and `num_gpus` settings | Match actor GPU requests to available Ray resources |

The most dangerous debugging shortcut is changing many settings at once. For example, increasing worker replicas, changing batch size, and modifying `max_replicas` in the same rollout makes it hard to know which change helped or hurt. Treat the serving system like any other distributed system: isolate the symptom, form a hypothesis, make one change, and verify the result.

## Ray Serve Versus Alternatives

Ray Serve sits in a crowded model-serving landscape. Choosing it well requires comparing workload shape, not just feature lists. If your service is one optimized model with strict latency targets and a supported runtime format, [Triton may be a strong fit](https://github.com/triton-inference-server/server). If your organization already built platform standards around [KServe and Knative](https://github.com/kserve/kserve), operational consistency may matter more than Python-native composition.

Ray Serve becomes attractive when the serving application is a distributed Python program. RAG pipelines, multi-model document processing, agentic workflows, and training-to-serving workflows often need more than a single model invocation. Ray Serve lets those stages live in one application graph while still scaling independently. That can reduce glue code and make pipeline-level behavior easier to reason about.

| Feature | Ray Serve | Triton | [Seldon Core](https://github.com/SeldonIO/seldon-core) | KServe |
|---|---|---|---|---|
| Primary strength | Python-native distributed serving | Optimized inference runtime | Enterprise model serving patterns | Kubernetes-native model serving |
| Model composition | Python handles and deployment graphs | Ensembles and backend configuration | Graph-style inference services | Inference services and pipelines |
| Best workload shape | Multi-stage AI applications | Low-latency supported model formats | Governed enterprise serving | Standardized K8s model endpoints |
| Scaling model | Serve replicas on Ray resources | Usually external orchestration | Kubernetes and platform integrations | Kubernetes and Knative patterns |
| GPU sharing approach | Ray fractional resource scheduling | Runtime and deployment dependent | Platform dependent | Platform dependent |
| Developer workflow | Python classes and imports | Model repository and config | CRDs and model server patterns | CRDs and model server patterns |
| Operational trade-off | Adds Ray runtime to operate | Runtime tuning can be specialized | More platform components | Knative and KServe complexity |

A good decision document should include a rejected-options section. For Ray Serve, justify why the distributed Python graph is worth operating Ray. For Triton, justify why model runtime optimization is more important than Python-native orchestration. For KServe, justify why platform standardization and Kubernetes-native workflows outweigh Ray's composition model. Tool choice becomes stronger when it names the trade-off.

**Active check:** Your team serves one ONNX model with strict p99 latency, no Python pipeline, and a platform team already experienced with GPU runtime tuning. Would Ray Serve be your default recommendation? A careful answer is probably no. Ray Serve can serve the model, but Triton or another specialized runtime may be a better first evaluation target because the workload does not need Ray's composition strengths.

## Did You Know?

- Ray started as a distributed systems project at UC Berkeley's RISELab, which helps explain why its core abstractions focus on distributed tasks, actors, and scheduling.
- Ray Serve applications can compose deployments with Python handles, so internal stages do not need to communicate through separate HTTP services.
- Fractional GPU settings in Ray are scheduling requests, so teams must still validate GPU memory pressure and latency behavior under real model load.
- KubeRay provides Kubernetes custom resources such as `RayCluster`, `RayJob`, and `RayService` so Ray workloads can be reconciled through Kubernetes control loops.

## Common Mistakes

| Mistake | Problem | Better approach |
|---|---|---|
| Treating Ray Serve like a single-process web framework | The team misses actor placement, resource scheduling, and distributed failure modes | Debug by layer: Kubernetes, KubeRay, Ray runtime, Serve deployment, application code |
| Putting expensive model replicas on the head pod | Control-plane coordination can compete with inference work | Keep the head focused on coordination and use worker groups for model capacity |
| Asking Ray for more GPUs than Kubernetes gives the pods | Serve replicas remain pending even though pods are running | Match Kubernetes GPU limits with `ray_actor_options.num_gpus` and dashboard resources |
| Using fractional GPUs without load testing | Multiple actors may fit by scheduler accounting but fail on memory or latency | Validate fractional packing with real models, batch sizes, and traffic patterns |
| Scaling every stage equally | Cheap stages overprovision while expensive stages keep queueing | Scale the stage whose ongoing-request queue and latency indicate bottleneck behavior |
| Copying code into pods for production delivery | Rollouts become manual and unreproducible | Package application code in an image, wheel, or controlled runtime artifact |
| Ignoring import-path failures in `RayService` | Kubernetes pods appear healthy while Serve has no usable application | Check `RayService` conditions, Serve logs, and the Python import path together |
| Changing autoscaling, batching, and resources in one rollout | The team cannot identify which change affected latency or cost | Tune one lever at a time and compare metrics before and after each change |

## Quiz

### Question 1

Your team deploys a RayService for a RAG endpoint. Kubernetes shows the head and worker pods as `Running`, but HTTP requests return a route-not-found response. What should you check first, and why?

<details>
<summary>Show Answer</summary>

Start with the `RayService` status, Serve application state, route prefix, and `import_path`. Running pods prove the Ray cluster exists, but they do not prove the Serve application imported correctly or registered the expected route. This is a Ray Serve application-layer symptom, not a pod scheduling symptom.
</details>

### Question 2

A generator deployment uses `ray_actor_options: {"num_gpus": 1}` and autoscaling allows four replicas. The Ray dashboard reports only two GPUs in the cluster, and two replicas remain pending during load. What design correction would you recommend?

<details>
<summary>Show Answer</summary>

Either increase available GPU worker capacity or reduce the generator's maximum replica count to match the real GPU budget. The pending replicas are a resource scheduling mismatch: Ray cannot place four one-GPU actors on a cluster that exposes only two GPU resources.
</details>

### Question 3

A pipeline has a fast normalizer, a moderate retriever, and a slow generator. Latency rises during traffic, and metrics show generator ongoing requests increasing while normalizer replicas are mostly idle. What should you change first?

<details>
<summary>Show Answer</summary>

Tune the generator stage first by evaluating `max_replicas`, queue target, batching, output length, or model cost. Scaling the normalizer will not reduce the queue forming at the generator. The bottleneck should drive the first capacity change.
</details>

### Question 4

Your team wants to use `num_gpus: 0.25` for four small reranker replicas on one GPU. The service starts, but p99 latency becomes unstable under realistic traffic. What does this reveal about fractional GPU allocation?

<details>
<summary>Show Answer</summary>

Fractional GPU allocation is scheduler accounting, not a guarantee of predictable performance isolation. The models may fit on the device but still compete for memory bandwidth, compute, or kernel execution. The team should test fewer colocated replicas, adjust batch behavior, or allocate larger GPU fractions.
</details>

### Question 5

A platform team already runs KServe for simple single-model endpoints. A product team proposes Ray Serve for a new document workflow that includes OCR, retrieval, reranking, and generation with different resource needs. How would you evaluate the proposal?

<details>
<summary>Show Answer</summary>

Compare workload shape against operational cost. Ray Serve is a strong candidate because the workflow is a multi-stage Python application with heterogeneous resources and independent scaling needs. The decision should still account for the extra Ray runtime, platform support model, and whether existing KServe standards can meet the same requirements.
</details>

### Question 6

A learner increases `target_num_ongoing_requests_per_replica` from two to twelve on an expensive LLM deployment because they want better GPU utilization. Throughput improves slightly, but user-facing latency becomes unacceptable. What trade-off did they expose?

<details>
<summary>Show Answer</summary>

They raised the per-replica queue target, which can improve utilization but allows more requests to wait behind expensive inference work. For latency-sensitive generation, the team may need a lower queue target, more replicas, shorter outputs, batching changes, or a different model size.
</details>

### Question 7

After a Ray image upgrade, the `RayCluster` reconciles but Serve replicas fail during startup with dependency import errors. Kubernetes resource settings did not change. What is the most likely category of failure, and what evidence should you gather?

<details>
<summary>Show Answer</summary>

This is likely an application runtime or image dependency failure. Gather Serve replica logs, Python import errors, `runtime_env` details, and image contents. Kubernetes scheduling succeeded, so changing pod resources is unlikely to fix missing packages or incompatible model dependencies.
</details>

### Question 8

A team copies `rag_app.py` into the Ray head pod during a demo and starts `serve run` manually. The demo works, but the endpoint disappears after a pod restart. What production change aligns the deployment with Kubernetes operations?

<details>
<summary>Show Answer</summary>

Package the application code into a versioned image, wheel, or controlled runtime artifact and deploy it through `RayService` with a stable `import_path`. Manual file copies and interactive commands are not reconciled desired state, so they vanish when pods restart.
</details>

## Hands-On Exercise: Build and Diagnose a Ray Serve RAG Pipeline

**Objective**: Deploy a small Ray Serve RAG-style pipeline on Kubernetes, verify the request path, and diagnose one intentional scaling question using the same layer-by-layer method used in production.

### Scenario

Your platform team is evaluating Ray Serve for an internal support assistant. The first version does not call a real LLM because the goal is to validate serving architecture before spending GPU budget. The pipeline normalizes a support question, retrieves a matching context string, and generates a templated answer. After it works, you will inspect where autoscaling would matter if the generator became expensive.

### Step 1: Create the Namespace and Confirm the Operator

Create a namespace for the lab. If the KubeRay operator is already installed, do not reinstall it. If it is missing, install it with Helm before continuing.

```bash
k create namespace ray-lab

k get pods -n ray-system

helm repo add kuberay https://ray-project.github.io/kuberay-helm/
helm repo update

helm install kuberay-operator kuberay/kuberay-operator \
  --namespace ray-system \
  --create-namespace
```

### Step 2: Deploy a CPU Ray Cluster

Save the following manifest as `ray-lab-cluster.yaml`. This cluster uses CPU workers so the exercise can run in more environments. The same structure later supports GPU worker groups when you are ready to test accelerator-backed deployments.

```yaml
apiVersion: ray.io/v1
kind: RayCluster
metadata:
  name: ray-lab-cluster
  namespace: ray-lab
spec:
  rayVersion: "2.9.0"
  headGroupSpec:
    rayStartParams:
      dashboard-host: "0.0.0.0"
    template:
      spec:
        containers:
          - name: ray-head
            image: rayproject/ray:2.9.0-py310
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
              requests:
                cpu: "1"
                memory: "2Gi"
              limits:
                cpu: "2"
                memory: "4Gi"
  workerGroupSpecs:
    - groupName: cpu-workers
      replicas: 2
      minReplicas: 1
      maxReplicas: 3
      rayStartParams: {}
      template:
        spec:
          containers:
            - name: ray-worker
              image: rayproject/ray:2.9.0-py310
              resources:
                requests:
                  cpu: "1"
                  memory: "2Gi"
                limits:
                  cpu: "2"
                  memory: "4Gi"
```

Apply it and wait for the pods. If the wait command times out, inspect pod events before changing the manifest.

```bash
k apply -f ray-lab-cluster.yaml
k get rayclusters -n ray-lab
k get pods -n ray-lab -l ray.io/cluster=ray-lab-cluster
k wait --for=condition=ready pod -l ray.io/cluster=ray-lab-cluster -n ray-lab --timeout=300s
```

### Step 3: Create the RAG Application

Save the following file as `rag_app.py`. The code uses three deployments and one composed pipeline. Notice that the resource settings differ by stage even though the model logic is small.

```python
from ray import serve
from starlette.requests import Request


KNOWLEDGE_BASE = {
    "kubernetes": "Kubernetes manages desired state for containerized workloads.",
    "ray": "Ray distributes Python tasks and actors across a cluster.",
    "serve": "Ray Serve routes HTTP requests to distributed deployment replicas.",
    "gpu": "GPU scheduling requires both Kubernetes device allocation and Ray resource accounting.",
}


@serve.deployment(num_replicas=2, ray_actor_options={"num_cpus": 0.25})
class Normalizer:
    def normalize(self, query: str) -> str:
        return " ".join(query.lower().strip().split())


@serve.deployment(num_replicas=2, ray_actor_options={"num_cpus": 0.5})
class Retriever:
    def retrieve(self, query: str) -> str:
        for key, value in KNOWLEDGE_BASE.items():
            if key in query:
                return value
        return "No matching context found."


@serve.deployment(
    autoscaling_config={
        "min_replicas": 1,
        "max_replicas": 3,
        "target_num_ongoing_requests_per_replica": 4,
    },
    ray_actor_options={"num_cpus": 0.5},
)
class Generator:
    def generate(self, query: str, context: str) -> str:
        return f"Using context '{context}', answer the question: {query}"


@serve.deployment
class RagPipeline:
    def __init__(self, normalizer, retriever, generator):
        self.normalizer = normalizer
        self.retriever = retriever
        self.generator = generator

    async def __call__(self, request: Request) -> dict:
        body = await request.json()
        query = body.get("query", "")

        clean_query = await self.normalizer.normalize.remote(query)
        context = await self.retriever.retrieve.remote(clean_query)
        answer = await self.generator.generate.remote(clean_query, context)

        return {
            "query": query,
            "normalized_query": clean_query,
            "context": context,
            "answer": answer,
        }


normalizer = Normalizer.bind()
retriever = Retriever.bind()
generator = Generator.bind()
app = RagPipeline.bind(normalizer, retriever, generator)
```

### Step 4: Run the Application on the Cluster

For a lab, copy the file into the head pod and run Serve from there. This is not the production delivery method, but it keeps the exercise focused on Ray Serve behavior. Production delivery should package code into an image or artifact and reconcile it through `RayService`.

```bash
HEAD_POD=$(k get pod -n ray-lab -l ray.io/node-type=head -o jsonpath='{.items[0].metadata.name}')

k cp rag_app.py "ray-lab/${HEAD_POD}:/tmp/rag_app.py"

k exec -n ray-lab "${HEAD_POD}" -- bash -lc "cd /tmp && serve run rag_app:app --host 0.0.0.0 --port 8000" 
```

If your terminal remains attached, open a second terminal for the next commands. If the command exits, read the error and classify it. Import errors belong to the Python environment. Route errors belong to Serve configuration. Pod errors belong to Kubernetes or Ray startup.

### Step 5: Send Requests Through the Serve Endpoint

Forward the Serve port and call the endpoint. Try at least two queries: one that matches the knowledge base and one that does not. The difference helps confirm that the request reached the retriever and generator rather than returning a static response.

```bash
k port-forward svc/ray-lab-cluster-head-svc 8000:8000 -n ray-lab
```

```bash
curl http://127.0.0.1:8000 \
  -H "Content-Type: application/json" \
  -d '{"query": "How does Ray Serve route requests?"}'

curl http://127.0.0.1:8000 \
  -H "Content-Type: application/json" \
  -d '{"query": "What should I check when GPU scheduling fails?"}'
```

### Step 6: Inspect the Dashboard and Reason About Scaling

Forward the dashboard and inspect the Serve application. Look for the three deployments, their replica counts, and the cluster resources. Then answer the diagnostic question before changing any settings: if the generator became a real LLM call and started queueing, which deployment would you tune first?

```bash
k port-forward svc/ray-lab-cluster-head-svc 8265:8265 -n ray-lab
```

Open `http://127.0.0.1:8265` and inspect the Serve page. The correct reasoning is that the generator should be tuned first if it is the stage whose queue grows. You might increase `max_replicas`, lower `target_num_ongoing_requests_per_replica`, add batching if the backend benefits, reduce output length, or allocate GPU resources in a GPU-enabled cluster.

### Step 7: Convert the Lab Learning into a Production Plan

Write a short production plan for the same pipeline. Include how code would be packaged, which stages would use CPU or GPU, what metrics would drive autoscaling, and what failure layer each alert would point to. This written plan is part of the exercise because senior platform work is not only applying manifests; it is explaining why the chosen operational boundary is maintainable.

### Success Criteria

- [ ] A `ray-lab` namespace exists and contains a running Ray head pod and worker pods.
- [ ] The RAG application code defines at least three Serve deployments and composes them with `.bind()`.
- [ ] The endpoint returns different context for at least two different query inputs.
- [ ] The Ray dashboard shows the Serve application and deployment replicas.
- [ ] You can explain why a generator queue should be fixed at the generator stage before scaling unrelated stages.
- [ ] You can identify whether a failure belongs first to Kubernetes, KubeRay, Ray runtime, Ray Serve, or application code.
- [ ] You wrote a production plan that replaces manual `k cp` delivery with a versioned image, package, or controlled runtime artifact.

### Cleanup

Delete the lab namespace when finished. This removes the Ray cluster, worker pods, and any objects created inside the namespace.

```bash
k delete namespace ray-lab
```

## Next Module

Continue to [Module 9.6: LangChain & LlamaIndex](../module-9.6-langchain-llamaindex/) to learn about building LLM applications with frameworks for RAG, agents, and chains.

## Sources

- [github.com: kuberay](https://github.com/ray-project/kuberay) — The KubeRay upstream README explicitly describes the operator and its RayCluster, RayJob, and RayService CRDs.
- [ray-project/ray](https://github.com/ray-project/ray) — Upstream repository and README for Ray Core and the Ray library ecosystem, including Serve.
- [raw.githubusercontent.com: index.md](https://raw.githubusercontent.com/ray-project/ray/ray-2.9.0/doc/source/serve/index.md) — The Ray Serve index describes Serve as scalable and programmable serving and discusses combining multiple deployments into one application.
- [raw.githubusercontent.com: key concepts.md](https://raw.githubusercontent.com/ray-project/ray/ray-2.9.0/doc/source/serve/key-concepts.md) — The Ray Serve key concepts page directly defines deployments, replicas, `@serve.deployment`, applications, HTTP route prefixes, and DeploymentHandles.
- [raw.githubusercontent.com: model composition.md](https://raw.githubusercontent.com/ray-project/ray/ray-2.9.0/doc/source/serve/model_composition.md) — The model composition guide describes composing deployments with `.bind()` and DeploymentHandle calls inside a Serve application.
- [raw.githubusercontent.com: autoscaling guide.md](https://raw.githubusercontent.com/ray-project/ray/ray-2.9.0/doc/source/serve/autoscaling-guide.md) — The Ray 2.9 autoscaling guide explicitly defines `target_num_ongoing_requests_per_replica` and the autoscaling replica bounds used in the module.
- [raw.githubusercontent.com: resource allocation.md](https://raw.githubusercontent.com/ray-project/ray/ray-2.9.0/doc/source/serve/resource-allocation.md) — The Ray Serve resource-allocation guide directly documents `ray_actor_options`, `num_gpus`, `num_cpus`, and fractional resources.
- [raw.githubusercontent.com: dyn req batch.md](https://raw.githubusercontent.com/ray-project/ray/ray-2.9.0/doc/source/serve/advanced-guides/dyn-req-batch.md) — The Ray Serve dynamic batching guide documents the `ray.serve.batch` decorator and the batch size and wait-time parameters.
- [raw.githubusercontent.com: fractional gpu.md](https://raw.githubusercontent.com/ray-project/ray/master/doc/source/serve/llm/user-guides/fractional-gpu.md) — The current Ray fractional-GPU guidance explicitly tells operators to validate throughput and latency with the actual workload before production.
- [raw.githubusercontent.com: getting started.md](https://raw.githubusercontent.com/ray-project/ray/ray-2.9.0/doc/source/cluster/kubernetes/getting-started.md) — The KubeRay getting-started page lists the CRDs and defines RayService as RayCluster plus Ray Serve deployment graphs.
- [raw.githubusercontent.com: rayservice.md](https://raw.githubusercontent.com/ray-project/ray/ray-2.9.0/doc/source/cluster/kubernetes/user-guides/rayservice.md) — The RayService guide directly documents `serveConfigV2`, `import_path`, `route_prefix`, runtime environment, deployments, and KubeRay's submission flow.
- [Schedule GPUs](https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/) — Backs Kubernetes GPU scheduling semantics, including vendor device plugin prerequisites, extended GPU resources, and how pods request GPU resources via limits.
- [Device Plugins](https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/device-plugins/) — Backs the Kubernetes device plugin architecture, including kubelet registration, gRPC interfaces, ListAndWatch/Allocate behavior, and vendor-specific hardware exposure.
- [raw.githubusercontent.com: key concepts.rst](https://raw.githubusercontent.com/ray-project/ray/master/doc/source/cluster/key-concepts.rst) — The Ray cluster key concepts page directly describes head nodes, worker nodes, GCS, autoscaler, and user task/actor execution.
- [raw.githubusercontent.com: getting started.rst](https://raw.githubusercontent.com/ray-project/ray/master/doc/source/ray-observability/getting-started.rst) — The Ray observability guide documents the dashboard views for tasks, actors, logs, Serve applications, cluster resources, and GPU assignment.
- [github.com: server](https://github.com/triton-inference-server/server) — The Triton upstream repository describes its inference-server role, supported frameworks, model repository workflow, and ensemble/model-configuration features.
- [github.com: kserve](https://github.com/kserve/kserve) — The KServe upstream repository describes KServe as a Kubernetes inference platform and documents InferenceService and Knative installation integration.
- [github.com: seldon core](https://github.com/SeldonIO/seldon-core) — The Seldon Core upstream repository describes it as an MLOps and LLMOps framework for deploying, managing, and scaling AI systems in Kubernetes.
- [Ray Serve: Scalable and Programmable Serving](https://github.com/ray-project/ray/blob/ray-2.9.0/doc/source/serve/index.md) — Primary upstream entry point for Ray Serve concepts, composition, and serving model.
- [KubeRay RayService Guide](https://github.com/ray-project/ray/blob/ray-2.9.0/doc/source/cluster/kubernetes/user-guides/rayservice.md) — Directly explains how RayService combines RayCluster configuration with Serve application configuration on Kubernetes.
- [Ray: A Distributed Framework for Emerging AI Applications](https://arxiv.org/abs/1712.05889) — Foundational Ray paper explaining the task and actor abstractions behind Ray Serve.

---
title: "Serverless on Bare Metal"
description: "Design, deploy, and operate serverless event-driven architectures and function-as-a-service platforms on bare-metal Kubernetes."
sidebar:
  order: 79
---

# Serverless on Bare Metal

## Learning Outcomes

*   Deploy and configure Knative Serving with a bare-metal compatible networking layer (Kourier or Contour).
*   Implement event-driven scale-to-zero workloads using KEDA and external metric triggers.
*   Compare architectural trade-offs between full Serverless platforms (Knative) and lightweight FaaS frameworks (OpenFaaS, Fission).
*   Diagnose cold start latency issues and implement mitigation strategies for compiled and interpreted runtimes.
*   Configure Knative Eventing brokers and triggers for decoupled message processing on premises.

## The Bare Metal Serverless Paradigm

Running serverless architectures on bare metal shifts the operational burden. In cloud environments, serverless abstracts infrastructure management entirely. On bare metal, the platform engineering team *becomes* the serverless provider. The goal is no longer avoiding infrastructure management, but optimizing resource utilization (bin-packing via scale-to-zero) and accelerating developer velocity through simplified deployment abstractions.

Cloud providers rely on proprietary load balancers and deeply integrated metric pipelines to route cold-start traffic and trigger scaling. On bare metal, you must wire ingress controllers, service meshes, and metric adapters manually to achieve the same request-driven scaling mechanics.

## Knative: The Standardized Serverless Substrate

Knative provides the foundational primitives for request-driven compute and event routing. It consists of two primary, decoupled components: Serving and Eventing.

### Knative Serving Architecture

Knative Serving builds on Kubernetes to support deploying and serving serverless applications. It handles the complex routing and autoscaling (including scale-to-zero) required for serverless workloads.

```mermaid
graph TD
    User([Client]) --> Ingress[Ingress Gateway]
    Ingress -->|Active Route| Pods[Application Pods]
    Ingress -->|Cold Route| Activator[Knative Activator]
    Activator -->|Triggers Scale| Autoscaler[Knative Autoscaler]
    Autoscaler -->|Updates| Deployment[Kubernetes Deployment]
    Deployment -->|Creates| Pods
    Activator -->|Forwards Buffered Request| Pods
```

*   **Autoscaler (KPA):** The Knative Pod Autoscaler collects metrics (concurrency or RPS) from the workload pods. It dictates the desired scale. When metrics drop to zero, KPA scales the deployment to zero.
*   **Activator:** When a service is scaled to zero, the ingress routing table points to the Activator instead of the application pods. The Activator buffers incoming requests, reports the metric spike to the Autoscaler, waits for the application pods to become ready, and then proxies the buffered requests to the new pods.
*   **Queue-Proxy:** A sidecar container injected into every Knative Service pod. It enforces concurrency limits and reports metrics back to the Autoscaler.

#### Networking Layer on Bare Metal

Knative Serving requires a networking layer to manage traffic routing and revisions. While Istio is common, it carries a massive operational footprint. For bare metal, lightweight alternatives are often preferred unless a service mesh is already mandated.

| Networking Layer | Footprint | Primary Use Case | Bare Metal Considerations |
| :--- | :--- | :--- | :--- |
| **Kourier** | Very Low | Pure Knative ingress | Ideal for strict FaaS environments. Uses Envoy. Directly exposes LoadBalancer or NodePort services. |
| **Contour** | Low | General Ingress + Knative | Good if Contour is already handling cluster ingress. |
| **Istio** | High | Advanced traffic management | Required if mTLS or complex cross-service auth is needed. Requires significant tuning. |

:::caution
When using bare metal without a MetalLB or Cilium BGP setup, Knative ingress gateways will default to `NodePort` or remain pending as `LoadBalancer`. Ensure your L2/L3 VIP configuration is functional before deploying Knative.
:::

### Knative Eventing

Knative Eventing provides infrastructure for routing events from producers to consumers using CloudEvents.

*   **Broker:** A routing hub for events. Producers send events to the Broker, unaware of consumers.
*   **Trigger:** Defines a filter and a subscriber. Consumers create Triggers to specify which events they want from the Broker.
*   **Channel / Subscription:** Lower-level primitives for direct pub/sub without the Broker's filtering complexity.

On bare metal, the backing storage for Brokers and Channels dictates reliability. The default in-memory channel is strictly for development. Production deployments require the Kafka broker implementation to ensure at-least-once delivery semantics and message durability during node failures.

## KEDA: Event-Driven Autoscaling

While Knative Serving scales based on HTTP request concurrency, KEDA (Kubernetes Event-driven Autoscaling) scales standard Kubernetes Deployments, StatefulSets, or Custom Resources based on external events (queue depth, database metrics, external API states).

KEDA is not a FaaS platform; it is an autoscaling engine that works alongside the Horizontal Pod Autoscaler (HPA).

### Scale-to-Zero Mechanics with KEDA

The standard Kubernetes HPA cannot scale workloads to zero. KEDA bridges this gap.

1.  **Metric Server:** KEDA acts as a Kubernetes Metrics Server, exposing external metrics to the HPA.
2.  **KEDA Operator:** Monitors the external event source (e.g., a RabbitMQ queue).
3.  **Scale 0 -> 1:** When the event source transitions from 0 to 1 (e.g., a message arrives), the KEDA operator directly scales the workload Deployment from 0 to 1.
4.  **Scale 1 -> N:** Once the workload is running, KEDA hands off scaling logic to the standard HPA, feeding it the configured metrics.
5.  **Scale 1 -> 0:** When the queue empties, the HPA scales down to its minimum (usually 1). The KEDA operator detects the empty queue and forces the scale to 0.

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: rabbitmq-worker-scaler
spec:
  scaleTargetRef:
    name: rabbitmq-worker
  minReplicaCount: 0
  maxReplicaCount: 50
  triggers:
  - type: rabbitmq
    metadata:
      queueName: task_queue
      queueLength: "5"
```

:::tip
KEDA polling intervals dictate how quickly a scale-from-zero event occurs. Aggressive polling (e.g., every 1 second) against large external systems (like a massive Kafka cluster or a slow Prometheus endpoint) can induce control-plane starvation. Default polling is typically 30 seconds.
:::

## FaaS Frameworks Comparison

If Knative provides the infrastructure, FaaS frameworks provide the developer experience. Knative itself requires developers to build and push container images. FaaS frameworks abstract the container build process, allowing developers to deploy raw source code.

### OpenFaaS

OpenFaaS focuses on simplicity. It uses an API Gateway to route traffic to functions. Functions are packaged as containers via the `faas-cli` and watchdog processes.

*   **Architecture:** API Gateway, NATS (for async execution), Queue Worker, Prometheus.
*   **Scaling:** Uses Prometheus metrics (RPS) read by the API Gateway to scale function deployments. Supports scale-to-zero via the `faas-idler`.
*   **Pros:** Extremely lightweight, runs on edge clusters, minimal moving parts.
*   **Cons:** Custom scaling mechanism (not native HPA/KPA), scale-to-zero requires an enterprise license or legacy open-source components.

### Fission

Fission optimizes aggressively for cold start latency by maintaining a pool of pre-warmed environment containers.

*   **Architecture:** Controller, Router, Environment (pre-warmed containers), Builder (compiles code in-cluster).
*   **Scaling:** When a request hits the Router, it grabs a pre-warmed container from the Environment pool, injects the function code dynamically, and routes the request.
*   **Pros:** Near-instant cold starts (sub-100ms) because container provisioning overhead is bypassed.
*   **Cons:** Higher baseline resource consumption (maintaining warm pools). Dynamic code injection violates immutable container patterns, making security scanning and runtime defense more complex.

## Cold Start Optimization on Bare Metal

Cold starts are the primary operational hurdle in serverless environments. A cold start consists of:
1.  Kubernetes scheduling the Pod.
2.  Container runtime pulling the image.
3.  Container runtime starting the container.
4.  Application framework bootstrapping (Spring, Express, etc.).
5.  Readiness probe passing.

On bare metal, network latency to the external container registry is often the largest variable.

### Mitigation Strategies

1.  **Image Locality and Pre-pulling:** Use local registry mirrors (e.g., Harbor proxy caches) running on the same L2 network as the compute nodes. Utilize tools like `kube-flannel` or DaemonSets to pre-pull large base images onto all nodes.
2.  **Runtime Selection:** Interpreted languages (Node.js, Python) have moderate startup times. JIT-compiled languages (Java/Spring, C#) suffer extreme cold starts. AOT-compiled languages (Go, Rust, GraalVM Java) offer the best cold start performance.
3.  **Init Container Elimination:** Avoid init containers in serverless workloads. They execute sequentially and block the main application container from starting.
4.  **CPU Bursting:** Container startup is inherently CPU-intensive. Ensure workloads have high CPU limits (or no limits) relative to their requests, allowing them to burst and consume idle node cycles during initialization.

## Hands-on Lab

This lab deploys Knative Serving utilizing Kourier for ingress, deploys a scale-to-zero service, and tests the autoscaler behavior.

### Prerequisites
*   A running Kubernetes cluster (v1.32+).
*   `kubectl` configured.
*   Cluster must be capable of allocating `LoadBalancer` IPs (e.g., via MetalLB) or you must access via `NodePort`.

### Step 1: Install Knative Serving CRDs and Core Components

Install the current Knative Serving components directly from the release artifacts.

```bash
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.14.0/serving-crds.yaml
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.14.0/serving-core.yaml
```

**Verification:**
```bash
kubectl get pods -n knative-serving
# Expected: activator, autoscaler, controller, webhook are Running.
```

### Step 2: Install Kourier Networking Layer

Kourier acts as the lightweight ingress gateway for Knative on bare metal.

```bash
kubectl apply -f https://github.com/knative/net-kourier/releases/download/knative-v1.14.0/kourier.yaml
kubectl patch configmap/config-network \
  --namespace knative-serving \
  --type merge \
  --patch '{"data":{"ingress-class":"kourier.ingress.networking.knative.dev"}}'
```

**Verification:**
```bash
kubectl get svc kourier -n kourier-system
# Expected: A LoadBalancer service with an external IP or pending state.
```

Capture the External IP or NodePort. If using MetalLB, it will assign an IP. For this lab, assume MetalLB assigned `192.168.100.50`.

```bash
export INGRESS_HOST=$(kubectl -n kourier-system get svc kourier -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
```

### Step 3: Configure DNS Magic (sslip.io)

For lab environments, configure Knative to use a magic DNS service so Services get resolvable URLs automatically based on the Ingress IP.

```bash
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.14.0/serving-default-domain.yaml
```

### Step 4: Deploy a Knative Service

Create a file named `hello-ksvc.yaml`.

```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: hello
  namespace: default
spec:
  template:
    spec:
      containers:
        - image: gcr.io/knative-samples/helloworld-go
          env:
            - name: TARGET
              value: "Bare Metal"
```

Deploy it:

```bash
kubectl apply -f hello-ksvc.yaml
```

**Verification:**
```bash
kubectl get ksvc hello
# Expected:
# NAME    URL                                      LATESTCREATED   LATESTREADY     READY   REASON
# hello   http://hello.default.192.168.100.50.sslip.io   hello-00001     hello-00001     True
```

### Step 5: Test Scale-to-Zero and Cold Start

Wait approximately 60 seconds. Observe the Pods in the default namespace.

```bash
kubectl get pods
# Expected: No pods found in default namespace. The service has scaled to zero.
```

Trigger a cold start by issuing an HTTP request. The request will hang momentarily while the Activator buffers it and the cluster spins up the pod.

```bash
curl http://hello.default.${INGRESS_HOST}.sslip.io
# Expected Output (after a slight delay): Hello Bare Metal!
```

Check the pods immediately after:

```bash
kubectl get pods
# Expected: One pod running.
```

*Troubleshooting:* If the curl hangs indefinitely, verify the `kourier` Service has a valid IP routing to your nodes, and that no host firewalls are dropping traffic on port 80.

## Practitioner Gotchas

1.  **The Activator Bottleneck.**
    *   *Context:* When rapid traffic spikes hit a service scaled to zero, the Activator buffers all requests.
    *   *Gotcha:* If the cold start latency is high, the Activator's memory and connection pools exhaust quickly, leading to cascading 503s before application pods even start. Ensure Activator deployments are scaled out and configured with appropriate resource limits in high-burst environments.

2.  **KEDA RabbitMQ Acknowledgement Races.**
    *   *Context:* KEDA scales down a worker when the queue depth hits zero.
    *   *Gotcha:* A worker might pull the last message from the queue, driving the queue metric to zero. KEDA sees zero and terminates the worker *before* the worker finishes processing and sends the ACK. The message is returned to the queue, triggering a scale-up, causing an endless loop of start/kill without processing. Always configure your application to handle SIGTERM gracefully and ensure `minReplicaCount: 1` if graceful shutdown cannot guarantee completion.

3.  **Ingress Timeout vs. Cold Start Mismatch.**
    *   *Context:* The external LoadBalancer or edge reverse proxy has a hard timeout (often 30 or 60 seconds).
    *   *Gotcha:* If a heavy Java/Spring workload takes 45 seconds to pull and boot, the client receives a 504 Gateway Timeout from the edge layer, even though Knative successfully started the pod a few seconds later. Align upstream ingress timeouts with the 99th percentile cold start time of your slowest serverless workload.

4.  **Metric Resolution Delays.**
    *   *Context:* Scaling relies on scraping metrics.
    *   *Gotcha:* Default Prometheus scraping intervals are often 15-30 seconds. If Knative or KEDA rely on external Prometheus queries for scaling decisions (rather than native adapters), your scaling reaction time is artificially delayed by the scrape interval plus query evaluation time. Use dedicated, tightly polled metric adapters for scaling components.

## Quiz

**Question 1**
Your bare-metal Knative Serving installation uses Istio. You deploy a Service configured to scale to zero. After 5 minutes of inactivity, the pod terminates. You immediately send an HTTP GET request to the service URL. What component receives and holds this initial request while the new pod boots?
A) The Istio Ingress Gateway buffers the request natively.
B) The Knative Autoscaler (KPA) queues the request.
C) The Knative Activator receives the routed request and buffers it.
D) The queue-proxy sidecar in the terminating pod intercepts it.
**Correct Answer: C**

**Question 2**
You are designing an asynchronous document processing pipeline. PDF uploads are saved to an S3-compatible store, which places a message on a Kafka topic. Processing a single PDF takes 4-5 minutes and consumes heavy CPU. You want the processing workers to scale down to zero when no documents are queued. Which architectural approach is best suited for this bare-metal Kubernetes environment?
A) Knative Serving, utilizing the Kafka ingress adapter.
B) KEDA, scaling a standard Kubernetes Deployment based on Kafka topic lag.
C) OpenFaaS, using the synchronous API gateway.
D) Fission, utilizing pre-warmed environment pods.
**Correct Answer: B**

**Question 3**
A platform team implements Fission on their bare metal cluster to minimize cold start times for a high-frequency internal API. Developers write functions in Python. Which architectural characteristic of Fission enables its sub-100ms cold starts?
A) It compiles all Python code into a single statically linked binary during deployment.
B) It maintains a pool of running environment containers and dynamically injects the Python source code upon request.
C) It bypasses the container runtime entirely and executes functions as systemd units on the host node.
D) It relies on Knative Activators to keep TCP connections permanently open.
**Correct Answer: B**

**Question 4**
You deploy a Node.js application via Knative Serving. During load testing, you observe that under sudden load spikes (from 1 to 500 concurrent requests), the application experiences high latency and several initial requests fail with 503 errors, but subsequent requests succeed. The Knative Autoscaler logs show pods are being requested. What is the most likely cause of the initial failures?
A) The Knative Autoscaler is misconfigured and failing to request enough pods.
B) The Node.js application has a memory leak during initialization.
C) The Knative Activator connection pool or buffer is exhausted due to slow container startup times.
D) The `kube-proxy` rules have not synchronized across the cluster.
**Correct Answer: C**

**Question 5**
When migrating a set of HTTP-triggered, synchronous microservices to Knative Serving on a bare-metal cluster, which language/framework combination will present the highest operational risk regarding cold start latency under unpredictable traffic patterns?
A) Go (compiled statically).
B) Rust (compiled dynamically).
C) Node.js (Express framework).
D) Java (Spring Boot framework, JIT compiled).
**Correct Answer: D**

## Further Reading

*   [Knative Serving Documentation](https://knative.dev/docs/serving/)
*   [KEDA Official Documentation](https://keda.sh/docs/)
*   [Knative Kourier Ingress Setup](https://knative.dev/docs/install/installing-istio/#installing-kourier)
*   [Fission Architecture Overview](https://fission.io/docs/architecture/)
*   [CloudEvents Specification](https://cloudevents.io/)
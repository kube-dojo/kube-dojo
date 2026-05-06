---
title: "Module 1.1: Kubernetes API & Extensibility Architecture"
slug: k8s/extending/module-1.1-api-deep-dive
revision_pending: false
sidebar:
  order: 2
---
> **Complexity**: `[MEDIUM]` - Understanding the API machinery
>
> **Time to Complete**: 3 hours
>
> **Prerequisites**: CKA or equivalent Kubernetes experience, basic Go programming, and access to a Kubernetes 1.35+ cluster

# Module 1.1: Kubernetes API & Extensibility Architecture

## Learning Outcomes

After completing this module, you will be able to:

1. **Trace** a `kubectl` request through authentication, authorization, admission control, validation, and etcd persistence.
2. **Implement** a Go program that creates, watches, and modifies Kubernetes resources with client-go informers and workqueues.
3. **Evaluate** whether CRDs, admission webhooks, ValidatingAdmissionPolicy, or API aggregation fits a given extension requirement.
4. **Diagnose** API Server request failures by connecting audit log fields, HTTP response codes, resource versions, and server-side apply ownership.

## Why This Module Matters

Hypothetical scenario: your platform team deploys a controller that labels Pods for chargeback, a security team adds an admission policy that blocks risky images, and an application team suddenly cannot create a Deployment that worked yesterday. The Pod never appears, the controller logs are quiet, and `kubectl` returns a short error that mentions forbidden fields. A useful engineer does not start by guessing which component is broken; they trace the request through the API Server pipeline and identify exactly which stage made the decision.

Kubernetes feels like a collection of components, but operationally it behaves like an API-centered system. The scheduler, kubelet, controllers, `kubectl`, admission webhooks, and custom operators all communicate by reading and writing API objects. If the API Server accepts an object, the rest of the control plane reacts to that stored intent; if the API Server rejects it, nothing downstream can compensate. That makes API literacy the foundation for every extension mechanism you will learn in this track.

This module builds that literacy in layers. First, you will follow a request from client authentication through authorization, admission, validation, persistence, and watches. Then you will interact with the API directly so the REST shape is visible instead of hidden behind `kubectl`. Finally, you will implement the client-go patterns that real controllers use: list, watch, cache, lister, and rate-limited workqueue. The goal is not to memorize every internal package; the goal is to reason clearly when an extension changes the API surface or changes how existing objects are admitted.

The airport security analogy is useful, with one important adjustment. The Kubernetes API Server is not merely a guard at the door; it is also the check-in desk, baggage policy engine, boarding scanner, and flight record system. Authentication asks who is making the request, authorization asks whether that identity may attempt the action, admission asks whether the requested object should be changed or rejected, and persistence records the accepted state in etcd. Each stage has its own evidence, failure codes, and extension hooks, so good debugging means knowing which question each stage answers.

## Core Concept 1: The API Server Request Pipeline

When you run `kubectl create deployment nginx --image=nginx`, `kubectl` constructs an HTTP request, signs it using credentials from your kubeconfig, and sends it to the API Server. The API Server does not immediately write the Deployment to etcd. It first turns the network request into a Kubernetes identity and a requested verb, checks whether that identity is allowed to perform that verb on that resource, applies admission logic, validates the resulting object, and only then persists the accepted object.

The order matters because each stage receives a different form of the request. Authentication sees credentials and produces user information. Authorization sees the user, verb, API group, resource, namespace, and name. Mutating admission sees the object before final validation and may add defaults or sidecars. Validating admission sees the final candidate object and may accept or reject it, but it cannot rewrite it. Persistence stores the approved state and advances the resource version that watch clients use to stay synchronized.

That sequencing is also why a single user-visible error can mislead you if you skip the pipeline model. A denied Pod create might be caused by missing RBAC, a webhook timeout, a CEL validation rule, a schema error, or an etcd storage problem, and each failure leaves different evidence. The fastest path is to ask what evidence exists for each stage: credential validity for authentication, `kubectl auth can-i` for authorization, admission messages for admission, schema errors for validation, and audit or API Server logs for persistence.

The API Server is intentionally stateless with respect to durable cluster data. You can run multiple API Server replicas behind a load balancer because accepted state is stored in etcd, while each API Server process performs request handling, admission calls, conversion, validation, and watch delivery. That stateless design improves availability, but it does not make every request cheap. List requests, watch fan-out, webhook calls, and serialization all consume control-plane capacity, so extension authors have to design as API citizens rather than assuming the server is an unlimited database endpoint.

```text
┌─────────────────────────────────────────────────────────────────────┐
│                    API Server Request Pipeline                       │
│                                                                     │
│   kubectl / client-go / curl                                        │
│        │                                                            │
│        ▼                                                            │
│   ┌─────────────────────────────────────────────────────────┐      │
│   │  1. AUTHENTICATION (AuthN)                               │      │
│   │     Who are you?                                         │      │
│   │     • X.509 client certificates                          │      │
│   │     • Bearer tokens (ServiceAccount, OIDC)               │      │
│   │     • Authenticating proxy                               │      │
│   │     → Result: User info (name, groups, UID)              │      │
│   └────────────────────────┬────────────────────────────────┘      │
│                            │                                        │
│                            ▼                                        │
│   ┌─────────────────────────────────────────────────────────┐      │
│   │  2. AUTHORIZATION (AuthZ)                                │      │
│   │     Are you allowed to do this?                          │      │
│   │     • RBAC (most common)                                 │      │
│   │     • ABAC (legacy)                                      │      │
│   │     • Webhook (external policy engines)                  │      │
│   │     • Node authorizer (kubelet-specific)                 │      │
│   │     → Result: Allow / Deny                               │      │
│   └────────────────────────┬────────────────────────────────┘      │
│                            │                                        │
│                            ▼                                        │
│   ┌─────────────────────────────────────────────────────────┐      │
│   │  3. MUTATING ADMISSION                                   │      │
│   │     Modify the request before validation                 │      │
│   │     • MutatingAdmissionWebhooks (YOUR extension point)   │      │
│   │     • Built-in mutating controllers                      │      │
│   │     → Can modify the object                              │      │
│   └────────────────────────┬────────────────────────────────┘      │
│                            │                                        │
│                            ▼                                        │
│   ┌─────────────────────────────────────────────────────────┐      │
│   │  4. SCHEMA VALIDATION                                    │      │
│   │     Is the object structurally valid?                    │      │
│   │     • OpenAPI schema validation                          │      │
│   │     • CRD structural schema checks                       │      │
│   └────────────────────────┬────────────────────────────────┘      │
│                            │                                        │
│                            ▼                                        │
│   ┌─────────────────────────────────────────────────────────┐      │
│   │  5. VALIDATING ADMISSION                                 │      │
│   │     Final policy check with no modification allowed      │      │
│   │     • ValidatingAdmissionWebhooks (YOUR extension point) │      │
│   │     • ValidatingAdmissionPolicies (CEL-based, in-tree)   │      │
│   │     → Can only Accept / Reject                           │      │
│   └────────────────────────┬────────────────────────────────┘      │
│                            │                                        │
│                            ▼                                        │
│   ┌─────────────────────────────────────────────────────────┐      │
│   │  6. PERSISTENCE                                          │      │
│   │     Write to etcd                                        │      │
│   │     • Serialize to storage format (protobuf)             │      │
│   │     • Apply resource version                             │      │
│   │     • Notify watchers via etcd watch                     │      │
│   └─────────────────────────────────────────────────────────┘      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

Authentication is deliberately pluggable because clusters integrate with many identity systems. A local administrator might use an X.509 client certificate in a kubeconfig, a Pod normally uses a projected ServiceAccount token, and a human user in an enterprise cluster may authenticate through OIDC. The API Server runs configured authenticators until one succeeds, then attaches a username, groups, and optional UID to the request. If no authenticator succeeds, the pipeline stops before Kubernetes even evaluates RBAC.

| Authenticator | How It Works | Common Use |
|---------------|-------------|------------|
| X.509 Client Certs | Certificate CN = username, O = group | kubeconfig for administrators and bootstrap flows |
| Bearer Token | Token in Authorization header | ServiceAccounts and automation |
| OIDC | JWT token from an identity provider | Human SSO and corporate identity |
| Authenticating Proxy | Trusted request headers such as `X-Remote-User` | API gateways and front proxies |

Authorization is where many practical failures happen because the identity is valid but the requested verb is not allowed. RBAC evaluates Roles, ClusterRoles, RoleBindings, and ClusterRoleBindings against a request such as "can this ServiceAccount patch Pods in namespace default?" A `403 Forbidden` after successful authentication means the request did not reach admission or storage. That distinction is important when a team blames an admission webhook even though RBAC blocked the request earlier.

```bash
# Check whether your current identity can create Deployments.
kubectl auth can-i create deployments --namespace=default

# Check as a specific ServiceAccount identity.
kubectl auth can-i create pods --as=system:serviceaccount:default:my-sa

# List the permissions Kubernetes can resolve for the current identity.
kubectl auth can-i --list
```

Admission is the extension-heavy part of the pipeline. Mutating admission can change an incoming object by adding labels, injecting containers, setting defaults, or normalizing fields. Validating admission evaluates the final object and returns accept or reject. Kubernetes 1.35 clusters can use admission webhooks for external logic and ValidatingAdmissionPolicy for in-tree CEL expressions, so the design choice is no longer "webhook or nothing." Use the simplest mechanism that can express the policy and reserve webhooks for logic that needs external data, complex calls, or mutation.

Mutation should be used carefully because it changes the object that every later stage sees. A sidecar injector that adds containers can accidentally trigger a validating policy that counts containers, and a defaulting webhook that adds labels can affect selectors, quotas, or controller behavior. Validation is easier to reason about because it does not rewrite the request, but it can still create operational risk if a webhook is slow or unreachable. In production, the admission design includes timeout, failure policy, namespace selection, object selection, and a rollout plan, not just the webhook code.

Pause and predict: if a user has RBAC permission to create Pods, but a validating admission webhook rejects Pods that use the `latest` image tag, which exact stage fails and which earlier stages must already have succeeded? The request authenticated successfully, passed authorization, may have passed mutating admission and schema validation, and then failed during validating admission. Depending on the admission response, the user will typically see a forbidden or invalid response with a message from the rejecting policy.

The extension map below is a practical way to organize choices. Some hooks live directly inside the request path, which makes them powerful but latency-sensitive. Others create new API types or respond after persistence, which is usually safer for business workflows because a slow controller does not block every create or update request. Treat request-path extensions as admission control and treat post-persistence controllers as reconciliation.

The difference between request-path and post-persistence extensions is the difference between a gate and a worker. A gate has to decide quickly because the user, controller, or kubelet is waiting for the API response. A worker can retry, back off, record status, and continue later because the desired state has already been stored. When a requirement sounds like "this object must never exist," admission is a natural fit; when it sounds like "make the outside world match this object," reconciliation is usually safer.

| Extension Point | Pipeline Stage | Mechanism | Module |
|----------------|---------------|-----------|--------|
| Custom authenticator | AuthN | Webhook token review | Outside this track |
| Custom authorizer | AuthZ | Webhook authorization | Outside this track |
| Mutating webhook | Admission | MutatingAdmissionWebhook | Module 1.6 |
| Validating webhook | Admission | ValidatingAdmissionWebhook | Module 1.6 |
| Validating policy | Admission | ValidatingAdmissionPolicy with CEL | Module 1.6 |
| Custom resources | API surface | CRD or API Aggregation | Modules 1.2 and 1.8 |
| Custom controllers | Post-persist | Controller pattern | Modules 1.3 and 1.4 |
| Scheduler plugins | Scheduling | Scheduling framework | Module 1.7 |
| CNI / CSI / CRI | Node level | Plugin interfaces | Outside this module |

## Core Concept 2: Raw API Interaction and Watch Semantics

`kubectl` is convenient, but it can hide the fact that Kubernetes is a structured HTTP API with discovery endpoints, resource URLs, content negotiation, and streaming watches. Raw API interaction is not something you do every day in production, yet it is one of the fastest ways to debug confusing behavior. When you can inspect the request path directly, you can separate client-side formatting from API behavior and see whether the server returns a list, table, watch event, status object, or admission rejection.

Every Kubernetes resource belongs to either the core API group or a named API group. Core resources such as Pods and Services live under `/api/v1`, while named groups such as Deployments use `/apis/apps/v1`. CustomResourceDefinitions live under the `apiextensions.k8s.io` API group, and instances of your custom resources get their own discovered resource paths. The shape is regular enough that dynamic clients can discover resources at runtime and operate on types that were not compiled into the program.

```text
/api/v1/namespaces/{namespace}/pods/{name}                  # Core API group
/apis/apps/v1/namespaces/{namespace}/deployments            # Named API group
/apis/apiextensions.k8s.io/v1/customresourcedefinitions      # CRD API
```

The easiest safe experiment is to start `kubectl proxy`, which listens locally and forwards requests to the API Server using your kubeconfig credentials. In the examples below, `.venv/bin/python` is used only to pretty-print JSON because this repository standardizes on the local virtual environment. The API requests themselves are plain HTTP requests to the proxy. Before running this, what output do you expect from `/apis` compared with `/api/v1`, and why would custom resources appear in one discovery tree but not the other?

Discovery is more than a convenience for command-line tools. Controllers, backup utilities, policy scanners, and dashboards use discovery to understand which resources exist and which verbs are supported. That is why CRDs feel native once installed: they participate in discovery, authorization, watch, and OpenAPI schema publication. If a tool hardcodes only built-in resources, it will miss the custom APIs that operators introduce, which is a serious gap in clusters where CRDs represent databases, certificates, gateways, policies, and application platforms.

```bash
# Start a kubectl proxy to handle authentication.
kubectl proxy --address=127.0.0.1 --port=8080 &

# Discover all named API groups.
curl -s http://127.0.0.1:8080/apis | .venv/bin/python -m json.tool | head -40

# List core API resources.
curl -s http://127.0.0.1:8080/api/v1 | .venv/bin/python -m json.tool | head -30

# List all Pods in the default namespace.
curl -s http://127.0.0.1:8080/api/v1/namespaces/default/pods | .venv/bin/python -m json.tool

# Get a specific Pod.
curl -s http://127.0.0.1:8080/api/v1/namespaces/default/pods/my-pod | .venv/bin/python -m json.tool

# Watch Pods as a streaming API response.
curl -s "http://127.0.0.1:8080/api/v1/namespaces/default/pods?watch=true"
```

Direct API access without the proxy is useful for understanding ServiceAccount tokens and TLS behavior, but it also demonstrates why client libraries exist. You must find the API Server endpoint, obtain a token, pass the Authorization header, decide how to verify the server certificate, and handle response objects yourself. The `-k` flag below skips certificate verification for a local learning cluster only; production tools should use the cluster CA from kubeconfig or in-cluster configuration.

This direct path also reveals the boundary between authentication and authorization. A valid bearer token proves that the API Server can authenticate the caller, but it does not grant any permissions by itself. The RoleBinding in the example deliberately grants broad edit permissions for a lab namespace so the raw create request can succeed. In a real controller, you would create a narrow ServiceAccount, bind only the verbs and resources required, and test those permissions with `kubectl auth can-i` before debugging client code.

```bash
# Grant permission to the default ServiceAccount to manage Pods for this lab.
kubectl create rolebinding default-edit --clusterrole=edit --serviceaccount=default:default

# Get the API Server URL and a short-lived ServiceAccount token.
APISERVER=$(kubectl config view --minify -o jsonpath='{.clusters[0].cluster.server}')
TOKEN=$(kubectl create token default)

# Direct API call with certificate verification skipped for a local dev cluster only.
curl -s -k -H "Authorization: Bearer $TOKEN" \
  "$APISERVER/api/v1/namespaces/default/pods" | .venv/bin/python -m json.tool | head -20

# Create a Pod via the raw API.
curl -s -k -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  "$APISERVER/api/v1/namespaces/default/pods" \
  -d '{
    "apiVersion": "v1",
    "kind": "Pod",
    "metadata": {"name": "api-test"},
    "spec": {
      "containers": [{
        "name": "nginx",
        "image": "nginx:1.27"
      }]
    }
  }'
```

The most important field in list and watch workflows is `metadata.resourceVersion`. It is not an application version such as `v1` or `v2`, and you should not compare it as if it were a semantic version. It is an opaque value that identifies a point in Kubernetes storage history for a resource collection. A client lists objects, records the returned resource version, then starts a watch from that point so it receives only the changes that happened after the list.

The list-and-watch pattern solves a classic synchronization problem. If a client simply lists all Pods and then starts watching with no continuity point, an update can happen between those two operations and never reach the client. By recording the list response's resource version and using it for the watch, the client creates a bridge between the initial snapshot and the event stream. That bridge is what lets a controller maintain a cache that is eventually consistent with the API Server without repeatedly performing full lists.

```bash
# Get the current resource version for the Pod collection.
RV=$(curl -s http://127.0.0.1:8080/api/v1/namespaces/default/pods \
  | .venv/bin/python -c "import sys,json; print(json.load(sys.stdin)['metadata']['resourceVersion'])")

# Watch from that point forward, receiving only new changes.
curl -s "http://127.0.0.1:8080/api/v1/namespaces/default/pods?watch=true&resourceVersion=$RV"
```

Watch events arrive as newline-delimited JSON objects. The event type tells you what happened, and the object contains the full resource state at that moment. A robust watcher must process events in order, remember the latest resource version it has successfully applied, and recover when the server says an old version is no longer available. If the watch is disconnected for long enough that the historical revision has been compacted, the client must perform a new list and rebuild its local cache.

This is where many hand-written watchers become subtly wrong. They handle the happy path of `ADDED`, `MODIFIED`, and `DELETED`, but they do not handle reconnects, expired resource versions, bookmarks, relists, or object decoding failures. A controller with a wrong local cache can be worse than a controller that is obviously down because it makes decisions from stale state. client-go's reflector is not just saving typing; it is encoding years of failure handling around the Kubernetes watch contract.

```json
{"type":"ADDED","object":{"kind":"Pod","metadata":{"name":"new-pod"},"spec":{},"status":{}}}
{"type":"MODIFIED","object":{"kind":"Pod","metadata":{"name":"new-pod"},"spec":{},"status":{}}}
{"type":"DELETED","object":{"kind":"Pod","metadata":{"name":"new-pod"},"spec":{},"status":{}}}
```

Stop and think: if your script loses its network connection while watching Pods, what happens if it reconnects without the last processed `resourceVersion`? The script can create a gap between its local state and cluster reality because events that happened during the disconnect are not replayed from the correct point. That is why production controllers do not hand-roll this loop casually; they use client-go reflectors and informers, which implement list-and-watch behavior, relist recovery, and cache synchronization.

## Core Concept 3: client-go, Informers, Listers, and Workqueues

You could build a controller by making raw HTTP calls, but every serious controller needs the same hard parts: kubeconfig loading, in-cluster authentication, object decoding, retry behavior, watch reconnection, rate limiting, and a local cache. The official client-go library packages those concerns into patterns used throughout Kubernetes itself. Learning those patterns early prevents the most common controller mistake: treating the API Server like a database to poll instead of a state stream to watch and reconcile.

The word "controller" can make this sound more complicated than it is. A controller is a loop that observes current state, compares it with desired state, and takes action to reduce the difference. Kubernetes makes that loop powerful because desired state is expressed as API objects and current state is observed through the same API. client-go supplies the mechanics that let the loop run efficiently: a shared cache for observation, typed clients for writes, and queues for retrying work without blocking event delivery.

The basic `Clientset` gives you typed clients for built-in resources such as Pods, Deployments, and Services. It is excellent when your program knows the resource types at compile time and wants Go structs with field access and compile-time checks. A `DynamicClient`, which appears later in the track, trades that type safety for runtime discovery and unstructured objects. For this module, the typed client is enough because we are watching Pods and using official `corev1.Pod` structs.

```text
┌─────────────────────────────────────────────────────────────────────┐
│                    client-go Architecture                            │
│                                                                     │
│   ┌─────────────┐         ┌───────────────────────────────────┐    │
│   │  API Server │◄───────│  Reflector                         │    │
│   │             │  WATCH  │  • List + Watch resources          │    │
│   └─────────────┘         │  • Pushes events to DeltaFIFO      │    │
│                           └──────────────┬────────────────────┘    │
│                                          │                          │
│                                          ▼                          │
│                           ┌───────────────────────────────────┐    │
│                           │  DeltaFIFO                         │    │
│                           │  • Queue of Added/Updated/Deleted  │    │
│                           │  • Deduplicates by key             │    │
│                           └──────────────┬────────────────────┘    │
│                                          │                          │
│                                          ▼                          │
│                           ┌───────────────────────────────────┐    │
│                           │  Indexer (In-Memory Store/Cache)  │    │
│                           │  • Thread-safe local store         │    │
│                           │  • Indexed for fast lookups        │    │
│                           └──────────────┬────────────────────┘    │
│                                          │                          │
│   ┌──────────────────────────────────────┼───────────────────┐     │
│   │         SharedIndexInformer          │                    │     │
│   │                                      ▼                    │     │
│   │   Lister ◄──── reads from cache (no API call!)           │     │
│   │                                                           │     │
│   │   EventHandlers ──► OnAdd / OnUpdate / OnDelete          │     │
│   │        │                                                  │     │
│   │        ▼                                                  │     │
│   │   Workqueue ──► Your controller logic processes items    │     │
│   │                                                           │     │
│   └───────────────────────────────────────────────────────────┘     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

| Component | What It Does | Why It Matters |
|-----------|-------------|----------------|
| **Reflector** | Lists then watches a resource type | Keeps a local cache synchronized with the API |
| **DeltaFIFO** | Queues changes with deduplication | Prevents processing stale intermediate events |
| **Indexer** | Stores objects in memory with indexes | Allows fast lookups without API calls |
| **Informer** | Combines Reflector, DeltaFIFO, Indexer, and handlers | Standard way to watch resources in controllers |
| **Lister** | Reads from the Indexer cache | Reduces API Server load during reconciliation |
| **Workqueue** | Rate-limited queue for processing keys | Decouples event receipt from slow or retrying work |

Set up the example module with Kubernetes 1.35 client libraries so the code matches the cluster version targeted by this curriculum. The client-go version number uses the `v0.x` module scheme, so Kubernetes 1.35 corresponds to the `v0.35.x` client-go family. In a real project, pin exact patch versions in `go.mod` and update them intentionally; for a lab, the commands below keep the dependency line clear.

```bash
mkdir -p ~/extending-k8s/pod-watcher
cd ~/extending-k8s/pod-watcher

go mod init github.com/example/pod-watcher
go get k8s.io/client-go@v0.35.0
go get k8s.io/apimachinery@v0.35.0
go get k8s.io/api@v0.35.0
```

Start with a simple list program before adding informers. Listing is intentionally boring: build a REST config from kubeconfig, create a clientset, call the Pods API, and print the objects. That boring path is valuable because it shows the typed client shape before cache machinery enters the picture. If this program fails, the error is usually kubeconfig loading, authentication, authorization, or cluster reachability rather than informer logic.

The same config-building step changes when code runs inside a Pod. An in-cluster controller normally uses the mounted ServiceAccount token and cluster CA through `rest.InClusterConfig()`, while a local tool normally reads kubeconfig through `clientcmd`. Many examples include a fallback that tries in-cluster configuration first and then kubeconfig for local development. This module keeps the first program simple, but the diagnostic habit is the same: prove the client can authenticate, list a resource, and receive an expected error before adding asynchronous control flow.

```go
// main.go
package main

import (
	"context"
	"fmt"
	"os"
	"path/filepath"

	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/tools/clientcmd"
)

func main() {
	// Build config from kubeconfig.
	home, _ := os.UserHomeDir()
	kubeconfig := filepath.Join(home, ".kube", "config")

	config, err := clientcmd.BuildConfigFromFlags("", kubeconfig)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error building kubeconfig: %v\n", err)
		os.Exit(1)
	}

	// Create the clientset.
	clientset, err := kubernetes.NewForConfig(config)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error creating clientset: %v\n", err)
		os.Exit(1)
	}

	// List Pods in all namespaces.
	pods, err := clientset.CoreV1().Pods("").List(context.TODO(), metav1.ListOptions{})
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error listing pods: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("Found %d pods across all namespaces:\n\n", len(pods.Items))
	for _, pod := range pods.Items {
		fmt.Printf("  %-40s %-20s %s\n", pod.Name, pod.Namespace, pod.Status.Phase)
	}
}
```

```bash
go run main.go
```

An informer changes the model from "ask the server every time" to "maintain a synchronized local view." It performs an initial list, opens a watch stream, stores objects in an indexer, and invokes event handlers when objects are added, updated, or deleted. The lister then reads from the cache, which means a reconciliation loop can inspect related objects without repeatedly querying the API Server. This is one reason Kubernetes can support many controllers at once without every controller hammering etcd through the API layer.

The cache is not a loophole around correctness; it is a deliberate consistency model. A controller reads from a cache that may be slightly behind the API Server, then writes changes through the API with resource-version-aware semantics. That is acceptable because controllers are level-based: they keep reconciling toward desired state rather than relying on one perfect event. If the cache lags briefly, the next watch event, resync, or queue retry brings the controller back to the latest observable state.

```go
// informer-example/main.go
package main

import (
	"fmt"
	"os"
	"os/signal"
	"path/filepath"
	"syscall"
	"time"

	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/labels"
	"k8s.io/client-go/informers"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/tools/cache"
	"k8s.io/client-go/tools/clientcmd"
)

func main() {
	home, _ := os.UserHomeDir()
	kubeconfig := filepath.Join(home, ".kube", "config")

	config, err := clientcmd.BuildConfigFromFlags("", kubeconfig)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error building kubeconfig: %v\n", err)
		os.Exit(1)
	}

	clientset, err := kubernetes.NewForConfig(config)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error creating clientset: %v\n", err)
		os.Exit(1)
	}

	// Create a shared informer factory with a 30-second resync period.
	factory := informers.NewSharedInformerFactory(clientset, 30*time.Second)

	// Get the Pod informer.
	podInformer := factory.Core().V1().Pods().Informer()

	// Register event handlers.
	podInformer.AddEventHandler(cache.ResourceEventHandlerFuncs{
		AddFunc: func(obj interface{}) {
			pod := obj.(*corev1.Pod)
			fmt.Printf("[ADDED]    %s/%s (Phase: %s)\n",
				pod.Namespace, pod.Name, pod.Status.Phase)
		},
		UpdateFunc: func(oldObj, newObj interface{}) {
			oldPod := oldObj.(*corev1.Pod)
			newPod := newObj.(*corev1.Pod)
			if oldPod.Status.Phase != newPod.Status.Phase {
				fmt.Printf("[UPDATED]  %s/%s Phase: %s -> %s\n",
					newPod.Namespace, newPod.Name,
					oldPod.Status.Phase, newPod.Status.Phase)
			}
		},
		DeleteFunc: func(obj interface{}) {
			pod := obj.(*corev1.Pod)
			fmt.Printf("[DELETED]  %s/%s\n", pod.Namespace, pod.Name)
		},
	})

	// Start the informer in background goroutines.
	stopCh := make(chan struct{})
	factory.Start(stopCh)

	// Wait for the initial cache sync.
	fmt.Println("Waiting for informer cache to sync...")
	if !cache.WaitForCacheSync(stopCh, podInformer.HasSynced) {
		fmt.Fprintln(os.Stderr, "Failed to sync informer cache")
		os.Exit(1)
	}
	fmt.Println("Cache synced! Watching for Pod changes...\n")

	// Use the Lister to read from cache, not from the API Server.
	lister := factory.Core().V1().Pods().Lister()
	pods, err := lister.List(labels.Everything())
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error listing from cache: %v\n", err)
	} else {
		fmt.Printf("Cache contains %d Pods\n\n", len(pods))
	}

	// Wait for shutdown signal.
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
	<-sigCh
	close(stopCh)
	fmt.Println("\nShutting down...")
}
```

Real controllers should not perform slow work inside an informer event handler. The handler runs on the path that drains events from the informer, so long database calls, cloud API calls, or complex reconciliation can delay event processing and cause the controller to fall behind. A workqueue solves this by letting the handler enqueue a stable object key such as `namespace/name` and return immediately. Worker goroutines then process keys with retry and rate limiting, which is a much better failure boundary.

Enqueuing keys instead of full objects is another small design choice with large consequences. The object you receive in an event may already be stale by the time a worker handles it, especially during rapid updates. A key lets the worker ask the lister for the latest cached object when reconciliation actually begins. If the object was deleted, the lister miss becomes part of the desired behavior, and your controller can clean up external state or simply record that there is nothing left to do.

```go
import (
	"k8s.io/client-go/tools/cache"
	"k8s.io/client-go/util/workqueue"
)

// Create a rate-limited workqueue.
queue := workqueue.NewTypedRateLimitingQueue(
	workqueue.DefaultTypedControllerRateLimiter[string](),
)

// In event handlers, enqueue the object key.
AddFunc: func(obj interface{}) {
	key, err := cache.MetaNamespaceKeyFunc(obj)
	if err != nil {
		return
	}
	queue.Add(key) // key is "namespace/name"
}

// Process items from the queue.
func processNextItem(queue workqueue.TypedRateLimitingInterface[string]) bool {
	key, shutdown := queue.Get()
	if shutdown {
		return false
	}
	defer queue.Done(key)

	// Your reconciliation logic here.
	err := syncHandler(key)
	if err != nil {
		// Re-enqueue with rate limiting on failure.
		queue.AddRateLimited(key)
		return true
	}

	// Tell the queue this item was processed successfully.
	queue.Forget(key)
	return true
}
```

Creating and modifying resources still uses the clientset directly. Informers are optimized for reads and event delivery; writes are explicit API operations. When updating an existing object, fetch the latest version first or use retry-on-conflict helpers in a full controller. Kubernetes uses optimistic concurrency through `resourceVersion`, so blindly updating an old object can overwrite someone else's newer intent or be rejected with a conflict.

Server-side apply is often a better write path for controllers that own a well-defined set of fields. Instead of reading an object, editing a full struct, and sending an update that may include unrelated fields, the controller sends the fields it intends to manage with a field manager name. The API Server tracks that ownership and reports conflicts when another manager owns the same field. That makes conflict resolution explicit and keeps controllers from accidentally taking responsibility for fields they only copied from a previous read.

```go
// Create a Pod.
newPod := &corev1.Pod{
	ObjectMeta: metav1.ObjectMeta{Name: "example-pod"},
	Spec: corev1.PodSpec{
		Containers: []corev1.Container{{Name: "nginx", Image: "nginx:1.27"}},
	},
}
_, _ = clientset.CoreV1().Pods("default").Create(context.TODO(), newPod, metav1.CreateOptions{})

// Modify a Pod after fetching the latest stored version.
pod, _ := clientset.CoreV1().Pods("default").Get(context.TODO(), "example-pod", metav1.GetOptions{})
pod.Annotations = map[string]string{"updated": "true"}
_, _ = clientset.CoreV1().Pods("default").Update(context.TODO(), pod, metav1.UpdateOptions{})
```

Stop and think: if your controller's processing logic hits a temporary network error when calling an external API, what happens if you return an error to the workqueue versus acknowledging the item and dropping the error? Returning the error keeps desired state honest because the item is retried with backoff. Dropping the error may make metrics look calm while the external system remains wrong, which is exactly the kind of hidden drift a controller is supposed to repair.

## Core Concept 4: API Groups, Versioning, Apply, Fairness, and Audit Evidence

Kubernetes API groups and versions let the project evolve without changing every resource at once. The core group contains resources such as Pods, ConfigMaps, and Services, while named groups contain specialized resources such as Deployments under `apps/v1`. Version labels communicate stability expectations: alpha APIs are experimental, beta APIs are closer to complete but still changeable, and stable `v1` APIs carry strong compatibility expectations. Custom resources follow the same pattern when you define served versions in a CRD.

Versioning is not only a documentation label; it is an API contract with storage and conversion implications. A CRD may serve multiple versions while storing one canonical version, and clients may continue using an older served version during a migration. Built-in Kubernetes APIs follow similar compatibility principles, which is why scripts should avoid depending on unstable alpha fields unless the operational risk is intentional. For extension authors, a version change is a promise to users about how safely their manifests and clients will keep working.

| Stage | Meaning | Stability |
|-------|---------|-----------|
| `v1alpha1` | Experimental and may be removed or redesigned | Do not use for durable production APIs |
| `v1beta1` | Feature complete enough for wider testing | Use carefully and plan migrations |
| `v1` | Stable with compatibility guarantees | Safe default for production API contracts |

```bash
# See all API versions available in the cluster.
kubectl api-versions

# See all resources and their API groups.
kubectl api-resources -o wide

# Check specific resource API details.
kubectl explain deployment --api-version=apps/v1
```

Content negotiation is another reminder that `kubectl get` is not the API itself. The server can return JSON for general clients, protocol buffers for efficient Kubernetes-native clients, and a Table representation that powers human-friendly `kubectl get` output. When debugging a custom client, check the `Accept` header before assuming the server returned the wrong shape. You may be asking for a representation optimized for a different consumer.

The Table representation is especially useful to understand because it explains why `kubectl get` can show concise columns without downloading every detail in the way a YAML dump does. Custom resources can define additional printer columns, and the API Server can present those columns to clients that request the table form. That means a CRD author influences not only validation and storage, but also the day-to-day operator experience of listing and scanning resources during incidents.

```bash
# JSON is the default representation.
curl -s -H "Accept: application/json" http://127.0.0.1:8080/api/v1/pods

# Protocol Buffers are more efficient for Kubernetes-native clients.
curl -s -H "Accept: application/vnd.kubernetes.protobuf" \
  http://127.0.0.1:8080/api/v1/pods -o pods.pb

# Table format is what kubectl uses for get-style output.
curl -s -H "Accept: application/json;as=Table;g=meta.k8s.io;v=v1" \
  http://127.0.0.1:8080/api/v1/namespaces/default/pods
```

Dry run and server-side apply are API features, not just `kubectl` conveniences. Server-side dry run asks the API Server to run admission and validation without persisting the object, which is useful before enabling a strict policy. Server-side apply asks the API Server to track field ownership in `managedFields`, which lets multiple actors safely manage different parts of the same object. Controllers that use apply can avoid stomping on fields owned by humans or other controllers.

Dry run is also a safe way to test admission behavior before a rollout. If a new validating rule would reject existing deployment patterns, a server-side dry run can expose that problem without creating or updating the object. This is more faithful than local YAML validation because the request goes through the API Server's schema, defaulting, and admission chain. It still does not prove that a workload will run correctly after persistence, but it narrows the question to the API acceptance stage.

```bash
# Create a deployment manifest locally.
kubectl create deployment my-app --image=nginx --dry-run=client -o yaml > deployment.yaml

# Server-side dry run validates through the API Server without persisting.
kubectl apply -f deployment.yaml --dry-run=server

# Server-side apply records field ownership for this manager.
kubectl apply -f deployment.yaml --server-side --field-manager=my-controller

# View field ownership.
kubectl get deployment my-app -o yaml | head -40
# Look for the managedFields section.
```

API Priority and Fairness matters once you write controllers because not all API traffic has the same operational importance. A misbehaving controller that rapidly lists large resources should not starve kubelets, controllers, or human incident responders. APF classifies requests into flow schemas and priority levels, then queues and dispatches them with fairness rules. If your controller sees throttling, that is not just a nuisance; it is a signal that your watch, cache, or retry design may be too expensive.

Good controllers are polite under failure. They use watches instead of repeated lists, rate-limit retries, avoid unbounded worker pools, and expose metrics that show queue depth and error rates. APF protects the cluster from the worst effects of noisy clients, but it is not a license to generate wasteful traffic. If your controller only works when it can make unlimited API calls, it is not ready for a shared control plane.

```bash
# View flow schemas that classify requests.
kubectl get flowschemas

# View priority levels used by API Priority and Fairness.
kubectl get prioritylevelconfigurations

# API Server metrics, when exposed, show whether requests are queued or rejected.
```

Audit logs are the request pipeline's paper trail. They record who made a request, which verb and resource were targeted, where the request came from, which stage was logged, and what response code was returned. Audit policy determines how much detail is captured, so clusters differ, but the fields below are enough to connect a user-visible failure to a pipeline stage. A `201` response means persistence succeeded; a `403` can mean authorization or admission rejected the request, and the surrounding fields tell you which path is more likely.

Audit evidence is strongest when combined with an intentional reproduction. If a user reports that a Deployment cannot be created, reproduce with server-side dry run, check `kubectl auth can-i` for the exact identity and namespace, and then inspect audit events for the request URI and response status. That sequence prevents a common trap where teams read a webhook error from one request and apply it to a different identity, namespace, or API version. The pipeline model keeps the evidence tied to the actual request.

```json
{"kind":"Event","apiVersion":"audit.k8s.io/v1","level":"Metadata","auditID":"1234-abcd","stage":"ResponseComplete","requestURI":"/api/v1/namespaces/default/pods","verb":"create","user":{"username":"kubernetes-admin","groups":["system:masters","system:authenticated"]},"sourceIPs":["192.168.1.100"],"userAgent":"kubectl/v1.35.0","objectRef":{"resource":"pods","namespace":"default","name":"nginx","apiVersion":"v1"},"responseStatus":{"metadata":{},"code":201}}
```

Read this audit event like a timeline. The `verb` and `requestURI` show a create request for Pods in the `default` namespace. The `user` object identifies the authenticated identity and groups, while `sourceIPs` and `userAgent` help distinguish human `kubectl` traffic from controller traffic. The `stage` of `ResponseComplete` means a response was sent, and `responseStatus.code` tells you the final outcome. If the same user can create Pods in one namespace but not another, your next stop is RBAC bindings or namespace-scoped admission.

## Core Concept 5: Building the Annotation Watcher

The exercise program watches all Pods and reports annotation changes. That may sound small, but it uses the same architecture as more serious controllers: a typed clientset, a shared informer factory, event handlers that enqueue object keys, a lister that reads from cache, and a rate-limited workqueue that processes retries. The domain logic is intentionally simple so you can focus on the control-plane pattern rather than external systems, CRD schemas, or reconciliation side effects.

Annotation changes are a useful teaching target because they are easy to trigger and easy to observe, yet they still exercise real update semantics. Adding an annotation, overwriting a value, and removing a key all create API updates with new resource versions. The watcher sees those updates through the informer stream, compares old and new annotation maps, and processes only the changes it cares about. This mirrors production controllers that ignore most events but enqueue the subset relevant to their reconciliation contract.

```text
pod-annotation-watcher/
├── go.mod
├── go.sum
└── main.go
```

The complete program below is longer than a minimal example because it keeps the important production habits visible. It waits for cache sync before reading, uses a context for shutdown, handles update events by comparing old and new annotation maps, retries queue items a bounded number of times, and reads objects from the informer lister instead of calling `Get` against the API Server inside the hot path. Those habits scale from this tiny watcher to controllers that reconcile cloud load balancers, certificates, databases, or policy state.

The bounded retry behavior is intentionally conservative. Infinite retries without rate limiting can hide a permanent bug while consuming CPU and log volume, but dropping failures immediately can leave external state broken forever. A real controller usually records errors in metrics and status conditions, then retries with backoff until either the desired state is reached or an operator has enough evidence to intervene. The workqueue gives you the mechanical foundation for that behavior without blocking the informer.

```go
// main.go
package main

import (
	"context"
	"fmt"
	"os"
	"os/signal"
	"path/filepath"
	"strings"
	"syscall"
	"time"

	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/labels"
	"k8s.io/client-go/informers"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/tools/cache"
	"k8s.io/client-go/tools/clientcmd"
	"k8s.io/client-go/util/workqueue"
	"k8s.io/klog/v2"
)

// AnnotationWatcher watches Pods for annotation changes.
type AnnotationWatcher struct {
	clientset kubernetes.Interface
	informer  cache.SharedIndexInformer
	queue     workqueue.TypedRateLimitingInterface[string]
	factory   informers.SharedInformerFactory
}

// NewAnnotationWatcher creates a new watcher.
func NewAnnotationWatcher(clientset kubernetes.Interface) *AnnotationWatcher {
	factory := informers.NewSharedInformerFactoryWithOptions(
		clientset,
		60*time.Second, // resync period
		informers.WithNamespace(metav1.NamespaceAll),
	)

	podInformer := factory.Core().V1().Pods()

	queue := workqueue.NewTypedRateLimitingQueueWithConfig(
		workqueue.DefaultTypedControllerRateLimiter[string](),
		workqueue.TypedRateLimitingQueueConfig[string]{
			Name: "annotation-watcher",
		},
	)

	w := &AnnotationWatcher{
		clientset: clientset,
		informer:  podInformer.Informer(),
		queue:     queue,
		factory:   factory,
	}

	podInformer.Informer().AddEventHandler(cache.ResourceEventHandlerFuncs{
		AddFunc: func(obj interface{}) {
			pod := obj.(*corev1.Pod)
			if len(pod.Annotations) > 0 {
				w.enqueue(obj)
			}
		},
		UpdateFunc: func(oldObj, newObj interface{}) {
			oldPod := oldObj.(*corev1.Pod)
			newPod := newObj.(*corev1.Pod)
			if !annotationsEqual(oldPod.Annotations, newPod.Annotations) {
				w.enqueue(newObj)
			}
		},
		DeleteFunc: func(obj interface{}) {
			w.enqueue(obj)
		},
	})

	return w
}

func (w *AnnotationWatcher) enqueue(obj interface{}) {
	key, err := cache.MetaNamespaceKeyFunc(obj)
	if err != nil {
		klog.Errorf("Failed to get key for object: %v", err)
		return
	}
	w.queue.Add(key)
}

// Run starts the informer and processes the workqueue.
func (w *AnnotationWatcher) Run(ctx context.Context) error {
	defer w.queue.ShutDown()

	// Start informers.
	w.factory.Start(ctx.Done())

	// Wait for cache sync.
	klog.Info("Waiting for informer cache to sync...")
	if !cache.WaitForCacheSync(ctx.Done(), w.informer.HasSynced) {
		return fmt.Errorf("failed to sync informer cache")
	}
	klog.Info("Cache synced successfully!")

	// Report initial state from cache.
	lister := w.factory.Core().V1().Pods().Lister()
	pods, err := lister.List(labels.Everything())
	if err != nil {
		return fmt.Errorf("listing Pods from cache: %w", err)
	}

	annotatedCount := 0
	for _, pod := range pods {
		if len(pod.Annotations) > 0 {
			annotatedCount++
		}
	}
	klog.Infof("Initial state: %d total Pods, %d with annotations",
		len(pods), annotatedCount)

	// Process workqueue items.
	klog.Info("Starting workers...")
	for {
		select {
		case <-ctx.Done():
			klog.Info("Context cancelled, shutting down")
			return nil
		default:
			if !w.processNextItem() {
				return nil
			}
		}
	}
}

func (w *AnnotationWatcher) processNextItem() bool {
	key, shutdown := w.queue.Get()
	if shutdown {
		return false
	}
	defer w.queue.Done(key)

	err := w.handleItem(key)
	if err != nil {
		if w.queue.NumRequeues(key) < 3 {
			klog.Warningf("Error processing %s (will retry): %v", key, err)
			w.queue.AddRateLimited(key)
			return true
		}
		klog.Errorf("Giving up on %s after 3 retries: %v", key, err)
	}

	w.queue.Forget(key)
	return true
}

func (w *AnnotationWatcher) handleItem(key string) error {
	namespace, name, err := cache.SplitMetaNamespaceKey(key)
	if err != nil {
		return fmt.Errorf("invalid key %q: %w", key, err)
	}

	// Read from the cache, not directly from the API Server.
	pod, err := w.factory.Core().V1().Pods().Lister().Pods(namespace).Get(name)
	if err != nil {
		klog.Infof("[DELETED] %s/%s", namespace, name)
		return nil
	}

	// Report annotations.
	fmt.Printf("\n--- Pod: %s/%s ---\n", pod.Namespace, pod.Name)
	fmt.Printf("    Phase: %s | Node: %s\n", pod.Status.Phase, pod.Spec.NodeName)

	if len(pod.Annotations) == 0 {
		fmt.Println("    Annotations: (none)")
	} else {
		fmt.Printf("    Annotations (%d):\n", len(pod.Annotations))
		for key, value := range pod.Annotations {
			display := value
			if len(display) > 80 {
				display = display[:80] + "..."
			}
			fmt.Printf("      %s = %s\n", key, display)
		}
	}

	return nil
}

// annotationsEqual checks if two annotation maps are the same.
func annotationsEqual(a, b map[string]string) bool {
	if len(a) != len(b) {
		return false
	}
	for key, value := range a {
		if b[key] != value {
			return false
		}
	}
	return true
}

func main() {
	klog.InitFlags(nil)

	home, _ := os.UserHomeDir()
	kubeconfig := filepath.Join(home, ".kube", "config")

	config, err := clientcmd.BuildConfigFromFlags("", kubeconfig)
	if err != nil {
		klog.Fatalf("Error building kubeconfig: %v", err)
	}

	clientset, err := kubernetes.NewForConfig(config)
	if err != nil {
		klog.Fatalf("Error creating clientset: %v", err)
	}

	watcher := NewAnnotationWatcher(clientset)

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Handle graceful shutdown.
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
	go func() {
		sig := <-sigCh
		klog.Infof("Received signal %v, shutting down", sig)
		cancel()
	}()

	fmt.Println(strings.Repeat("=", 60))
	fmt.Println("  Pod Annotation Watcher")
	fmt.Println("  Press Ctrl+C to exit")
	fmt.Println(strings.Repeat("=", 60))

	if err := watcher.Run(ctx); err != nil {
		klog.Fatalf("Error running watcher: %v", err)
	}
}
```

Notice the shape of the failure handling. A deleted object is not an error for this watcher because the absence of the Pod is itself the state change being reported. A temporary processing error, however, is returned to the queue so the item can be retried with rate limiting. That distinction between expected state transitions and retryable failures is one of the core design skills in controller development.

## Patterns & Anti-Patterns

The most reliable Kubernetes extensions treat the API Server as a coordination boundary, not as a place to hide arbitrary application logic. They store desired state declaratively, validate input close to the request path, and reconcile side effects after persistence. The patterns below are deliberately phrased as design moves rather than library recipes because the same reasoning applies whether you write a controller with client-go, controller-runtime, Java, Python, or another Kubernetes client.

A useful design review starts by writing down which part of the system owns each decision. The API Server owns authentication, authorization, admission ordering, schema validation, storage, and watch delivery. Your controller owns domain reconciliation after the object exists. Your admission policy owns fast request-time decisions about whether the object is acceptable. When those responsibilities blur, extensions become hard to operate because a failure in one part of the system appears as a mysterious symptom somewhere else.

| Pattern | When to Use It | Why It Works | Scaling Considerations |
|---------|----------------|--------------|------------------------|
| List-then-watch with informer cache | Any controller that reacts to Kubernetes objects | Builds a consistent local view and avoids repeated full lists | Watch reconnects and relists are handled by the library, but resyncs still cost CPU |
| Enqueue keys, not objects | Reconciliation can be slow, retrying, or dependent on external systems | Keeps event handlers fast and lets workers fetch current state | Queue depth and retry metrics become important health signals |
| Server-side apply with a named field manager | Multiple actors manage different fields of the same object | API Server records ownership and detects conflicts explicitly | Field ownership needs stable manager names and careful conflict handling |
| Admission for request-time policy | Invalid objects must be blocked before persistence | Users get immediate feedback and bad state never enters storage | Webhooks must be fast, highly available, and failure policy must be chosen carefully |

Anti-patterns usually start as shortcuts that work in a small cluster. Polling every second feels simpler than informers, direct object processing feels simpler than workqueues, and broad admission webhooks feel simpler than precise policies. Those shortcuts become outages when the cluster grows because they turn every controller into a competing API load generator or turn every create request into a dependency on an unreliable external service.

The safer habit is to design for the failure mode before writing the happy path. Ask what happens when the API Server is temporarily throttling, when a webhook is down, when a watch reconnects, when two actors update the same field, and when the external API your controller calls returns an error. If the answer is "the user request blocks" or "the controller silently drops the item," the design needs another boundary. Kubernetes gives you admission, status, events, queues, and managed fields so you can make those boundaries explicit.

| Anti-Pattern | What Goes Wrong | Better Alternative |
|--------------|-----------------|--------------------|
| Polling large resource lists in a loop | The API Server and etcd spend work sending the same state repeatedly | Use shared informers and listers |
| Doing slow work inside event handlers | Informer processing backs up and events are delayed | Enqueue keys and process them with workers |
| Using admission webhooks for post-create side effects | Request latency and availability depend on external systems | Persist intent, then reconcile side effects with a controller |
| Updating stale objects without conflict handling | Concurrent changes are rejected or overwritten | Fetch latest state and use retry-on-conflict or server-side apply |
| Treating all `403` responses as RBAC | Admission can also reject with forbidden-style responses | Inspect audit fields, admission messages, and authorization checks together |

## Decision Framework

The fastest way to choose an extension point is to ask what kind of change you are making to the cluster. If you need a new declarative API type, start with a CRD. If you need to reject or default existing resources at request time, use admission. If you need a full custom REST implementation, custom storage, or non-standard API semantics, consider API aggregation only after CRDs prove insufficient. If you need to create real-world side effects, write a controller that watches stored intent and reconciles it.

| Requirement | Prefer | Why | Avoid |
|-------------|--------|-----|-------|
| Store new declarative state such as `Database` or `BackupPolicy` | CRD plus controller | Native discovery, validation, RBAC, watches, and status | API aggregation unless CRD semantics are insufficient |
| Block Pods missing required labels | ValidatingAdmissionPolicy or validating webhook | Rejects invalid state before persistence | Controller-only cleanup after bad objects already exist |
| Inject sidecars or defaults into Pods | Mutating admission webhook | Mutation must happen before schema validation and persistence | Post-create controller mutation that races workloads |
| Call a cloud API to create external resources | Controller with workqueue | External calls can retry without blocking API writes | Admission webhook that depends on cloud API availability |
| Provide custom storage or unusual REST behavior | API aggregation | Lets you serve an API through the Kubernetes aggregation layer | CRD when you need behavior CRDs cannot model |

Use this text flow when you design an extension: first ask whether you need a new resource type, then ask whether the request must be changed or rejected before storage, then ask whether side effects can happen asynchronously after storage. Which approach would you choose here and why: a policy that rejects Deployments without `app.kubernetes.io/name`, a `Database` resource that provisions a managed database, and a sidecar injector for observability? The likely answers are validating policy or webhook, CRD plus controller, and mutating webhook, respectively, because each requirement lives at a different point in the pipeline.

There are edge cases, but the defaults should be conservative. CRDs are the normal path for new declarative state because they let Kubernetes handle discovery, RBAC, validation, storage, and watches. ValidatingAdmissionPolicy is attractive when CEL can express the rule because it avoids an external network dependency in the request path. Webhooks remain necessary for mutation and complex checks, but they deserve production engineering around availability and timeouts. API aggregation is powerful, but it is an advanced choice because you operate a full API server behind the Kubernetes aggregation layer.

## Did You Know?

- **The Kubernetes API is intentionally discoverable.** A client can call discovery endpoints to find groups, versions, and resources at runtime, which is why generic tools can list CRDs installed after the tool was compiled.
- **Server-side apply became generally available in Kubernetes 1.22.** Its managed field ownership is one of the main reasons modern controllers can cooperate on the same object without relying only on last-writer-wins updates.
- **API Priority and Fairness has been stable since Kubernetes 1.29.** It replaced simple max-in-flight limits with request classification, queuing, and fairness so important control-plane traffic is less likely to be starved by noisy clients.
- **client-go uses the same list-watch foundation that Kubernetes controllers rely on internally.** Understanding reflectors, informers, listers, and workqueues prepares you to read higher-level controller frameworks instead of treating them as magic.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|----------------|---------------|
| Polling the API Server in a tight loop | Polling feels simple and works in a tiny cluster, but it repeatedly serializes full lists and bypasses watch efficiency | Use informers with watch streams and read from listers whenever possible |
| Processing events directly in the handler | The first prototype has no slow dependency, so the handler becomes a convenient place for business logic | Enqueue `namespace/name` keys and process them in worker goroutines with rate limiting |
| Reading before cache sync | The lister exists immediately, so it is easy to forget that the initial list may still be running | Always call `WaitForCacheSync` before using informer-backed listers |
| Treating `resourceVersion` as a semantic version | The name suggests application versioning, but the value is an opaque storage marker | Store and pass it only as an API token for list-watch continuity |
| Hardcoding kubeconfig-only configuration | Local development uses `~/.kube/config`, so the program fails when deployed as a Pod | Use in-cluster config with a kubeconfig fallback in deployable controllers |
| Using API calls in hot reconciliation paths | Direct `Get` calls are familiar and appear harmless during testing | Prefer lister reads from the informer cache and reserve direct client calls for writes |
| Ignoring update conflicts and field ownership | Single-writer tests hide concurrent updates from humans and other controllers | Fetch latest state, use retry-on-conflict, or use server-side apply with a stable field manager |
| Blaming the wrong pipeline stage | A short `kubectl` error often hides whether RBAC, admission, validation, or storage rejected the request | Combine `kubectl auth can-i`, server-side dry run, audit logs, and admission messages |

## Quiz

<details>
<summary>Scenario: A controller receives `403 Forbidden` when patching Pods, but the ServiceAccount token is valid. Which API Server stage should you investigate first, and why?</summary>

Investigate authorization first because valid authentication only proves the ServiceAccount identity was accepted. A `403` during a patch often means RBAC does not allow the `patch` verb for Pods in the target namespace, so the request never reaches mutating admission, validating admission, or etcd persistence. Confirm with `kubectl auth can-i patch pods --as=system:serviceaccount:<namespace>:<name> --namespace=<namespace>`. If RBAC allows the request, then inspect audit logs and admission messages because admission can also deny a request after authorization succeeds.
</details>

<details>
<summary>Scenario: A junior engineer proposes `kubectl get pods -o json` every second to monitor Pod phase changes. How do you evaluate that design?</summary>

Reject the polling design for anything beyond a quick local experiment because it repeatedly asks the API Server to list and serialize the same collection. The better pattern is an informer, which performs an initial list, opens a watch stream, and maintains a local cache that can be read through a lister. This reduces API Server and etcd load while still delivering changes promptly. The tradeoff is that the program must follow controller patterns such as cache sync, event handlers, and watch recovery instead of a simple loop.
</details>

<details>
<summary>Scenario: An informer `UpdateFunc` runs a slow database query before returning. What architectural component is missing, and what failure mode does it create?</summary>

The missing component is a workqueue that decouples event receipt from reconciliation work. Running slow operations inside the event handler blocks the informer path that drains and dispatches events, so the controller can fall behind during bursts or external dependency delays. A workqueue lets the handler enqueue the object key quickly and return, while workers process keys with retry and rate limiting. This also gives you metrics such as queue depth and retry count, which are much easier to operate than hidden handler latency.
</details>

<details>
<summary>Scenario: A raw watch connection drops, and your local cache misses several Pod updates after reconnecting. How does `resourceVersion` change your recovery strategy?</summary>

Track the latest resource version from the last event your program successfully applied, then reconnect the watch from that version so the API Server can send later changes. If the stored revision is too old because compaction removed the history, the server can respond with `410 Gone`, and your client must perform a fresh list before starting a new watch. This is the reason production controllers rely on client-go reflectors rather than ad hoc watch loops. The recovery strategy is list, remember the collection resource version, watch from there, and relist when the watch history is no longer available.
</details>

<details>
<summary>Scenario: A mutating webhook injects a sidecar, then a validating policy rejects Pods with more than one container. What happens when a user creates a single-container Pod?</summary>

The request is rejected after mutation because validating admission evaluates the final candidate object, not the original object the user submitted. The mutating webhook first adds the sidecar, which changes the in-flight Pod to contain two containers. The validating policy then sees the two-container object and rejects it, so the Pod is never persisted to etcd. The fix is not to reorder the stages; the teams must align the mutation and validation rules or scope one of them more precisely.
</details>

<details>
<summary>Scenario: You need a new `Database` API with desired spec, observed status, RBAC, watches, and `kubectl` discovery. Which extension mechanism should you evaluate first?</summary>

Evaluate a CRD with a controller first because the requirement is a new declarative resource type stored through the Kubernetes API. CRDs give you discovery, schema validation, RBAC integration, watch support, and status subresources without writing a full aggregated API server. API aggregation is worth evaluating only if you need custom storage or REST behavior that CRDs cannot represent. Admission webhooks may still support the design by validating or defaulting the custom resource, but they are not the primary storage mechanism.
</details>

<details>
<summary>Scenario: An audit event shows `ResponseComplete`, `verb=create`, a Pod `objectRef`, and response code `201`. What can you conclude, and what can you not conclude?</summary>

You can conclude that the create request completed successfully and the object was accepted through the pipeline and persisted. The authenticated user, request URI, source IPs, and user agent identify who made the request and what they targeted. You cannot conclude that the Pod became Ready, because scheduling, image pulls, kubelet execution, and readiness probes happen after API persistence. To diagnose runtime state, follow the persisted Pod through scheduler and kubelet events rather than staying inside admission and audit evidence.
</details>

## Hands-On Exercise

Exercise scenario: you are building a lightweight diagnostic tool for a platform team that wants to see Pod annotation changes as they happen. The tool should not poll the API Server, and it should not perform API reads every time an event arrives. It should use the informer cache for reads, enqueue work by key, and shut down cleanly when interrupted. This exercise is intentionally close to the complete example above so you can focus on running, observing, and modifying the controller pattern.

**Task**: Build and run a Go program that uses a client-go informer to watch Pods across all namespaces and report annotation changes in real time.

### Setup

```bash
# Ensure you have a running local cluster.
kind create cluster --name extending-k8s

# Checkpoint: verify the cluster is reachable.
kubectl cluster-info

# Create the project.
mkdir -p ~/extending-k8s/pod-annotation-watcher
cd ~/extending-k8s/pod-annotation-watcher
go mod init github.com/example/pod-annotation-watcher
go get k8s.io/client-go@v0.35.0
go get k8s.io/apimachinery@v0.35.0
go get k8s.io/api@v0.35.0
go get k8s.io/klog/v2@latest
```

### Progressive Tasks

1. Copy the complete annotation watcher from Core Concept 5 into `main.go`, run `gofmt -w main.go`, and inspect the imports so you can explain why `labels`, `cache`, and `workqueue` are each needed.

2. Build and run the watcher in one terminal. Keep it running so you can observe initial cache sync and later event processing.

```bash
go build -o pod-watcher .
./pod-watcher
```

3. In another terminal, create a Pod, wait for it to become Ready, add annotations, modify an annotation, remove an annotation, and then delete the Pod. Watch the first terminal and connect each printed line to an add, update, or delete event.

```bash
# Create a Pod.
kubectl run test-pod --image=nginx

# Checkpoint: wait for the Pod to be Ready.
kubectl wait --for=condition=Ready pod/test-pod --timeout=120s

# Add annotations.
kubectl annotate pod test-pod team=backend priority=high

# Modify an annotation.
kubectl annotate pod test-pod priority=critical --overwrite

# Remove an annotation.
kubectl annotate pod test-pod team-

# Delete the Pod.
kubectl delete pod test-pod
```

4. Verify that the initial cache report shows cluster Pods before you create `test-pod`. Explain why that read should come from the informer lister rather than a direct `Clientset.Get` or `Clientset.List` call inside the event path.

5. Change the resync period from `60*time.Second` to a shorter interval for a local experiment, rerun the watcher, and observe whether unchanged Pods are reprocessed. Then restore the original value so the lab does not leave behind a noisy controller.

6. Press Ctrl+C and confirm that the context cancellation path stops the informer and drains the process without a panic. A clean shutdown is part of controller correctness because Kubernetes sends termination signals during rollouts and node maintenance.

7. Clean up the local cluster when you are done.

```bash
kind delete cluster --name extending-k8s
```

<details>
<summary>Solution notes</summary>

The watcher should print a cache sync message before reporting annotation changes. Add events with no annotations may not be enqueued because the example only enqueues added Pods when annotations already exist, while update events should be enqueued when annotation maps differ. Delete events are reported when the lister can no longer find the cached object. If the program fails before cache sync, check kubeconfig, cluster reachability, and RBAC before changing informer logic.
</details>

### Success Criteria

- [ ] Program compiles and runs without errors.
- [ ] Initial cache sync completes and reports the Pod count.
- [ ] New Pod creation is observable through the informer event stream.
- [ ] Annotation additions, modifications, and removals trigger update processing.
- [ ] Pod deletion is detected and reported without a panic.
- [ ] Ctrl+C triggers graceful shutdown through context cancellation.
- [ ] Lister reads come from the informer cache rather than direct hot-path API calls.

## Sources

- https://kubernetes.io/docs/reference/using-api/api-concepts/
- https://kubernetes.io/docs/reference/access-authn-authz/authentication/
- https://kubernetes.io/docs/reference/access-authn-authz/authorization/
- https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/
- https://kubernetes.io/docs/reference/access-authn-authz/extensible-admission-controllers/
- https://kubernetes.io/docs/tasks/extend-kubernetes/custom-resources/custom-resource-definitions/
- https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/apiserver-aggregation/
- https://kubernetes.io/docs/reference/using-api/server-side-apply/
- https://kubernetes.io/docs/concepts/cluster-administration/flow-control/
- https://kubernetes.io/docs/tasks/debug/debug-cluster/audit/
- https://github.com/kubernetes/client-go
- https://pkg.go.dev/k8s.io/client-go/tools/cache
- https://pkg.go.dev/k8s.io/client-go/util/workqueue

## Next Module

[Module 1.2: Custom Resource Definitions Deep Dive](../module-1.2-crds-advanced/) - Define your own Kubernetes resource types with advanced validation, versioning, and subresources.

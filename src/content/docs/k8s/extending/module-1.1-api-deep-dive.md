---
title: "Module 1.1: Kubernetes API & Extensibility Architecture"
slug: k8s/extending/module-1.1-api-deep-dive
sidebar:
  order: 2
---
> **Complexity**: `[MEDIUM]` - Understanding the API machinery
>
> **Time to Complete**: 3 hours
>
> **Prerequisites**: CKA or equivalent Kubernetes experience, Basic Go programming

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Trace** a kubectl request through authentication, authorization, and admission control to etcd storage
2. **Implement** a Go program that creates, watches, and modifies Kubernetes resources using client-go
3. **Evaluate** which API extensibility hook (CRDs, admission webhooks, aggregation) fits a given use case
4. **Diagnose** API Server request failures by interpreting audit logs and HTTP response codes

---

## Why This Module Matters

Every single thing that happens in a Kubernetes cluster goes through one gateway: the **API Server**. When you run `kubectl apply`, when a controller reconciles state, when the scheduler places a Pod -- every action is an API call. If you want to extend Kubernetes (and you do, that is why you are here), you need to understand this gateway inside and out.

This module takes you from "I can use kubectl" to "I understand what kubectl does under the hood." You will trace a request through the entire API Server pipeline, learn where the extensibility hooks live, and write your first Go program that talks to the Kubernetes API using the official client-go library.

> **The Airport Security Analogy**
>
> Think of the Kubernetes API Server as airport security. Every request (passenger) must go through a strict pipeline: first **Authentication** (show your passport -- who are you?), then **Authorization** (check your boarding pass -- are you allowed on this flight?), then **Admission Control** (security screening -- is your luggage compliant?). Only after passing all three stages does your request board the plane and reach etcd. Just like an airport, each stage can reject you, and there are specific "extensibility points" where you can add your own screening rules.

---

## What You'll Learn

By the end of this module, you will be able to:
- Trace a request through the full API Server lifecycle
- Identify all extensibility points in the Kubernetes API
- Interact with the API using curl and raw HTTP
- Write Go programs using client-go with Informers, Listers, and Workqueues
- Explain the difference between polling and watching resources

---

## Did You Know?

- **The API Server handles roughly 500-2,000 requests per second** in a production cluster of moderate size. Every `kubectl get pods` is a REST call. Every controller reconciliation is a WATCH stream event. The efficiency of this machinery is what makes Kubernetes work at scale.

- **etcd is the only stateful component**: The API Server itself is stateless. You can (and should) run multiple replicas. All state lives in etcd, which is why etcd backup is the single most critical operational task.

- **client-go is older than most Kubernetes operators**: The client-go library dates back to Kubernetes 0.x days. Its Informer pattern -- watch + in-memory cache -- has been copied by controller frameworks in every language. Understanding it means understanding every operator ever written.

---

## Part 1: API Server Request Lifecycle

### 1.1 The Full Request Pipeline

When you run `kubectl create deployment nginx --image=nginx`, here is exactly what happens:

```
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
│   │     Is the object structurally valid?                     │      │
│   │     • OpenAPI schema validation                          │      │
│   │     • CRD structural schema checks                       │      │
│   └────────────────────────┬────────────────────────────────┘      │
│                            │                                        │
│                            ▼                                        │
│   ┌─────────────────────────────────────────────────────────┐      │
│   │  5. VALIDATING ADMISSION                                 │      │
│   │     Final policy check — no modifications allowed        │      │
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

### 1.2 Understanding Each Stage

**Authentication** runs multiple authenticators in sequence. The first one that succeeds wins. In most clusters you will encounter:

| Authenticator | How It Works | Common Use |
|---------------|-------------|------------|
| X.509 Client Certs | Certificate CN = username, O = group | kubectl (kubeconfig) |
| Bearer Token | Token in Authorization header | ServiceAccounts |
| OIDC | JWT token from identity provider | SSO/corporate auth |
| Authenticating Proxy | Header-based (X-Remote-User) | API gateways |

**Authorization** checks whether the authenticated user can perform the requested action. RBAC is the standard:

```bash
# Check if you can create deployments
k auth can-i create deployments --namespace=default

# Check as a specific user
k auth can-i create pods --as=system:serviceaccount:default:my-sa

# List all permissions
k auth can-i --list
```

**Admission Controllers** are the most important extensibility point. They come in two flavors:
- **Mutating**: Can modify the incoming object (e.g., inject sidecar containers, set defaults)
- **Validating**: Can only accept or reject (e.g., enforce naming conventions, deny privileged pods)

> **Pause and predict**: If a user has RBAC permissions to create a Pod, but a Validating Admission Webhook is configured to reject Pods using the `latest` image tag, at which exact stage will their request fail, and what HTTP status code will they likely receive?

### 1.3 Extensibility Points Map

Here is every place you can extend Kubernetes, organized by where it fits in the pipeline:

| Extension Point | Pipeline Stage | Mechanism | Module |
|----------------|---------------|-----------|--------|
| Custom authenticator | AuthN | Webhook token review | N/A |
| Custom authorizer | AuthZ | Webhook authorization | N/A |
| Mutating webhook | Admission | MutatingAdmissionWebhook | 1.6 |
| Validating webhook | Admission | ValidatingAdmissionWebhook | 1.6 |
| Validating policy | Admission | ValidatingAdmissionPolicy (CEL) | 1.6 |
| Custom resources | API surface | CRD / API Aggregation | 1.2, 1.8 |
| Custom controllers | Post-persist | Controller pattern | 1.3, 1.4 |
| Scheduler plugins | Scheduling | Scheduling framework | 1.7 |
| CNI / CSI / CRI | Node level | Plugin interfaces | Outside scope |

#### Decision Framework: Which Extensibility Hook to Use?

When extending the API, use this decision tree to choose the right tool:

1. **Do you need to store new configuration or state in the cluster?**
   - **Yes, and it is mostly declarative data**: Use **Custom Resource Definitions (CRDs)**. This is the default for the vast majority of use cases.
   - **Yes, but it requires custom storage (e.g., a SQL database) or extremely specialized REST semantics**: Use **API Aggregation**.
2. **Do you need to intercept and modify existing resources (like Pods or Deployments)?**
   - **Yes, to set defaults or inject sidecars**: Use **Mutating Admission Webhooks**.
   - **Yes, to enforce security policies or complex validation**: Use **Validating Admission Webhooks** (or Validating Admission Policies).

---

## Part 2: Raw API Interaction

### 2.1 API Discovery

Every Kubernetes API follows a consistent URL structure:

```
/api/v1/namespaces/{namespace}/pods/{name}          # Core API group
/apis/apps/v1/namespaces/{namespace}/deployments     # Named API group
/apis/apiextensions.k8s.io/v1/customresourcedefinitions  # CRD API
```

```bash
# Start a kubectl proxy to handle authentication
k proxy --port=8080 &

# Discover all API groups
curl -s http://localhost:8080/apis | python3 -m json.tool | head -40

# List core API resources
curl -s http://localhost:8080/api/v1 | python3 -m json.tool | head -30

# List all pods in default namespace
curl -s http://localhost:8080/api/v1/namespaces/default/pods | python3 -m json.tool

# Get a specific pod
curl -s http://localhost:8080/api/v1/namespaces/default/pods/my-pod | python3 -m json.tool

# Watch pods (streaming)
curl -s "http://localhost:8080/api/v1/namespaces/default/pods?watch=true"
```

### 2.2 Direct API Access (Without Proxy)

```bash
# Get API server URL and token
APISERVER=$(k config view --minify -o jsonpath='{.clusters[0].cluster.server}')
TOKEN=$(k create token default)

# Direct API call with certificate verification skipped (dev only!)
curl -s -k -H "Authorization: Bearer $TOKEN" \
  "$APISERVER/api/v1/namespaces/default/pods" | python3 -m json.tool | head -20

# Create a pod via raw API
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

### 2.3 Resource Versions and Watches

Every Kubernetes resource has a `resourceVersion` field. This is not a "version" in the semantic sense -- it is an **etcd revision number** that changes on every write. Watches use this to efficiently stream changes:

```bash
# Get the current resource version
RV=$(curl -s http://localhost:8080/api/v1/namespaces/default/pods \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['metadata']['resourceVersion'])")

# Watch from that point forward (only new changes)
curl -s "http://localhost:8080/api/v1/namespaces/default/pods?watch=true&resourceVersion=$RV"
```

Watch events come as newline-delimited JSON:

```json
{"type":"ADDED","object":{"kind":"Pod","metadata":{"name":"new-pod",...},...}}
{"type":"MODIFIED","object":{"kind":"Pod","metadata":{"name":"new-pod",...},...}}
{"type":"DELETED","object":{"kind":"Pod","metadata":{"name":"new-pod",...},...}}
```

> **Stop and think**: If your script loses its network connection while watching a resource, what happens if you reconnect and do not provide the `resourceVersion` from the last event you received? How would this affect your local cache state?

---

## Part 3: Introduction to client-go

### 3.1 Why client-go?

You could talk to the Kubernetes API with raw HTTP, but you would have to handle:
- Authentication (certificates, tokens, kubeconfig parsing)
- Watch reconnection and resource version bookmarks
- Rate limiting and backoff
- Deserialization of Kubernetes objects
- Caching to avoid hammering the API Server

**client-go** handles all of this. It is the same library that kubectl, the scheduler, and the controller-manager use internally.

### 3.2 Core client-go Concepts

```
┌─────────────────────────────────────────────────────────────────────┐
│                    client-go Architecture                            │
│                                                                     │
│   ┌─────────────┐         ┌───────────────────────────────────┐    │
│   │  API Server  │◄───────│  Reflector                         │    │
│   │              │  WATCH  │  • List + Watch resources          │    │
│   └─────────────┘         │  • Pushes events to DeltaFIFO      │    │
│                           └──────────────┬────────────────────┘    │
│                                          │                          │
│                                          ▼                          │
│                           ┌───────────────────────────────────┐    │
│                           │  DeltaFIFO                         │    │
│                           │  • Queue of (Added/Updated/Deleted) │   │
│                           │  • Deduplicates by key              │    │
│                           └──────────────┬────────────────────┘    │
│                                          │                          │
│                                          ▼                          │
│                           ┌───────────────────────────────────┐    │
│                           │  Indexer (In-Memory Store/Cache)    │    │
│                           │  • Thread-safe local store          │    │
│                           │  • Indexed for fast lookups         │    │
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
| **Reflector** | Lists then watches a resource type | Keeps local cache in sync with API |
| **DeltaFIFO** | Queues changes with deduplication | Prevents processing stale events |
| **Indexer** | In-memory store with indexes | Allows fast lookups without API calls |
| **Informer** | Combines Reflector + DeltaFIFO + Indexer | The standard way to watch resources |
| **Lister** | Read from the Indexer cache | Enables reads without hitting the API Server |
| **Workqueue** | Rate-limited queue for processing | Decouples event handling from processing |

### 3.3 Setting Up a Go Project

```bash
mkdir -p ~/extending-k8s/pod-watcher && cd ~/extending-k8s/pod-watcher

go mod init github.com/example/pod-watcher
go get k8s.io/client-go@latest
go get k8s.io/apimachinery@latest
go get k8s.io/api@latest
```

### 3.4 Basic Client: Listing Pods

Start simple -- connect and list pods:

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
	// Build config from kubeconfig
	home, _ := os.UserHomeDir()
	kubeconfig := filepath.Join(home, ".kube", "config")

	config, err := clientcmd.BuildConfigFromFlags("", kubeconfig)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error building kubeconfig: %v\n", err)
		os.Exit(1)
	}

	// Create the clientset
	clientset, err := kubernetes.NewForConfig(config)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error creating clientset: %v\n", err)
		os.Exit(1)
	}

	// List pods in all namespaces
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

### 3.5 Using Informers: Watching Pods

The Informer pattern is the efficient way to watch resources. Instead of polling (which hammers the API Server), an Informer establishes a long-lived watch connection and maintains a local cache:

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

	// Create a shared informer factory with a 30-second resync period
	factory := informers.NewSharedInformerFactory(clientset, 30*time.Second)

	// Get the Pod informer
	podInformer := factory.Core().V1().Pods().Informer()

	// Register event handlers
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
				fmt.Printf("[UPDATED]  %s/%s Phase: %s → %s\n",
					newPod.Namespace, newPod.Name,
					oldPod.Status.Phase, newPod.Status.Phase)
			}
		},
		DeleteFunc: func(obj interface{}) {
			pod := obj.(*corev1.Pod)
			fmt.Printf("[DELETED]  %s/%s\n", pod.Namespace, pod.Name)
		},
	})

	// Start the informer (runs in background goroutines)
	stopCh := make(chan struct{})
	factory.Start(stopCh)

	// Wait for the initial cache sync
	fmt.Println("Waiting for informer cache to sync...")
	if !cache.WaitForCacheSync(stopCh, podInformer.HasSynced) {
		fmt.Fprintln(os.Stderr, "Failed to sync informer cache")
		os.Exit(1)
	}
	fmt.Println("Cache synced! Watching for pod changes...\n")

	// Use the Lister to read from cache (no API call)
	lister := factory.Core().V1().Pods().Lister()
	pods, err := lister.List(labels.Everything())
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error listing from cache: %v\n", err)
	} else {
		fmt.Printf("Cache contains %d pods\n\n", len(pods))
	}

	// Wait for shutdown signal
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
	<-sigCh
	close(stopCh)
	fmt.Println("\nShutting down...")
}
```

> **Note**: The above example needs the import `"k8s.io/apimachinery/pkg/labels"` for the `labels.Everything()` call. We omitted it from the import block for brevity; your IDE will add it automatically if you use `goimports`.

### 3.6 Workqueues: Decoupling Events from Processing

In a real controller, you never process events directly in the event handler. Instead, you enqueue an item key and process it separately. This gives you:
- **Rate limiting**: Don't overwhelm downstream systems
- **Retries**: Failed items go back on the queue with exponential backoff
- **Deduplication**: Multiple events for the same object collapse into one processing

```go
import (
	"k8s.io/client-go/util/workqueue"
)

// Create a rate-limited workqueue
queue := workqueue.NewTypedRateLimitingQueue(
	workqueue.DefaultTypedControllerRateLimiter[string](),
)

// In event handlers, enqueue the object key
AddFunc: func(obj interface{}) {
    key, err := cache.MetaNamespaceKeyFunc(obj)
    if err != nil {
        return
    }
    queue.Add(key)  // key is "namespace/name"
}

// Process items from the queue
func processNextItem(queue workqueue.TypedRateLimitingInterface[string]) bool {
    key, shutdown := queue.Get()
    if shutdown {
        return false
    }
    defer queue.Done(key)

    // Your business logic here
    err := syncHandler(key)
    if err != nil {
        // Re-enqueue with rate limiting on failure
        queue.AddRateLimited(key)
        return true
    }

    // Tell the queue we processed this item successfully
    queue.Forget(key)
    return true
}
```

> **Stop and think**: If your controller's processing logic encounters a temporary network error when talking to an external API, what happens if you return an error to the Workqueue versus acknowledging the item and dropping the error? How does the Workqueue's rate limiter prevent this failure from overwhelming the API Server?

---

## Part 4: API Server Internals

### 4.1 API Groups and Versioning

Kubernetes uses API groups to organize resources and API versioning to evolve them:

| Stage | Meaning | Stability |
|-------|---------|-----------|
| `v1alpha1` | Experimental, may be removed | Do not use in production |
| `v1beta1` | Feature complete, may change | Use with caution |
| `v1` | Stable, backward compatible | Safe for production |

```bash
# See all API versions available
k api-versions

# See all resources and their API groups
k api-resources -o wide

# Check specific resource API details
k explain deployment --api-version=apps/v1
```

### 4.2 Content Negotiation

The API Server supports multiple serialization formats:

```bash
# JSON (default)
curl -s -H "Accept: application/json" http://localhost:8080/api/v1/pods

# Protocol Buffers (more efficient, used internally)
curl -s -H "Accept: application/vnd.kubernetes.protobuf" \
  http://localhost:8080/api/v1/pods -o pods.pb

# Table format (what kubectl uses for get)
curl -s -H "Accept: application/json;as=Table;g=meta.k8s.io;v=v1" \
  http://localhost:8080/api/v1/namespaces/default/pods
```

### 4.3 Dry Run and Server-Side Apply

Two powerful API features that are often overlooked:

```bash
# Dry run: validate without persisting
k apply -f deployment.yaml --dry-run=server

# Server-side apply: the API server manages field ownership
k apply -f deployment.yaml --server-side --field-manager=my-controller

# View field ownership
k get deployment my-app -o yaml | head -40
# Look for managedFields section
```

Server-side apply is crucial for controllers. It prevents conflicts when multiple controllers modify the same resource by tracking which controller owns which fields.

> **Stop and think**: Why is Server-Side Apply crucial for controllers that manage different fields of the same resource, compared to traditional client-side apply? What specific problem does field ownership solve if two controllers update the same object concurrently?

### 4.4 API Priority and Fairness

Since Kubernetes 1.29+, API Priority and Fairness (APF) replaced the old max-in-flight request limiting:

```bash
# View flow schemas (how requests are classified)
k get flowschemas

# View priority levels
k get prioritylevelconfigurations

# Check API request metrics (if you have access to API server metrics)
# These show you if requests are being queued or rejected
```

APF ensures that one misbehaving controller cannot starve the API Server. Requests are classified into priority levels and queued fairly within each level.

### 4.5 Interpreting API Server Audit Logs

Audit logs provide a security-relevant, chronological set of records documenting the sequence of actions in a cluster. The API Server can log requests at different stages (e.g., RequestReceived, ResponseComplete).

To view audit logs (typically found on the control plane node at `/var/log/kubernetes/audit/audit.log`, depending on your distribution), you will see JSON entries like this:

```json
{"kind":"Event","apiVersion":"audit.k8s.io/v1","level":"Metadata","auditID":"1234-abcd","stage":"ResponseComplete","requestURI":"/api/v1/namespaces/default/pods","verb":"create","user":{"username":"kubernetes-admin","groups":["system:masters","system:authenticated"]},"sourceIPs":["192.168.1.100"],"userAgent":"kubectl/v1.27.0","objectRef":{"resource":"pods","namespace":"default","name":"nginx","apiVersion":"v1"},"responseStatus":{"metadata":{},"code":201}}
```

**How to interpret this log entry:**
- **`verb` and `requestURI`**: Tells you exactly what action was attempted (`create` on `/api/v1/namespaces/default/pods`).
- **`user`**: Identifies who made the request (`kubernetes-admin`).
- **`stage`**: `ResponseComplete` means the request went through the entire pipeline and a response was sent.
- **`responseStatus.code`**: A `201` means the pod was successfully created. A `403` would mean Authorization rejected it, and a `400` or `422` might mean an Admission Webhook rejected it.

---

## Part 5: Building a Real Informer-Based Application

### 5.1 Project Structure for the Exercise

```
pod-annotation-watcher/
├── go.mod
├── go.sum
└── main.go
```

This program watches all Pods and specifically tracks annotation changes, printing a detailed report whenever annotations are added, removed, or modified.

### 5.2 Complete Working Example

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

// AnnotationWatcher watches pods for annotation changes.
type AnnotationWatcher struct {
	clientset  kubernetes.Interface
	informer   cache.SharedIndexInformer
	lister     cache.GenericLister
	queue      workqueue.TypedRateLimitingInterface[string]
	factory    informers.SharedInformerFactory
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

	// Start informers
	w.factory.Start(ctx.Done())

	// Wait for cache sync
	klog.Info("Waiting for informer cache to sync...")
	if !cache.WaitForCacheSync(ctx.Done(), w.informer.HasSynced) {
		return fmt.Errorf("failed to sync informer cache")
	}
	klog.Info("Cache synced successfully!")

	// Report initial state from cache
	lister := w.factory.Core().V1().Pods().Lister()
	pods, err := lister.List(labels.Everything())
	if err != nil {
		return fmt.Errorf("listing pods from cache: %w", err)
	}

	annotatedCount := 0
	for _, pod := range pods {
		if len(pod.Annotations) > 0 {
			annotatedCount++
		}
	}
	klog.Infof("Initial state: %d total pods, %d with annotations",
		len(pods), annotatedCount)

	// Process workqueue
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

	// Read from the cache (not the API server)
	pod, err := w.factory.Core().V1().Pods().Lister().Pods(namespace).Get(name)
	if err != nil {
		klog.Infof("[DELETED] %s/%s", namespace, name)
		return nil
	}

	// Report annotations
	fmt.Printf("\n━━━ Pod: %s/%s ━━━\n", pod.Namespace, pod.Name)
	fmt.Printf("    Phase: %s | Node: %s\n", pod.Status.Phase, pod.Spec.NodeName)

	if len(pod.Annotations) == 0 {
		fmt.Println("    Annotations: (none)")
	} else {
		fmt.Printf("    Annotations (%d):\n", len(pod.Annotations))
		for k, v := range pod.Annotations {
			display := v
			if len(display) > 80 {
				display = display[:80] + "..."
			}
			fmt.Printf("      %s = %s\n", k, display)
		}
	}

	return nil
}

// annotationsEqual checks if two annotation maps are the same.
func annotationsEqual(a, b map[string]string) bool {
	if len(a) != len(b) {
		return false
	}
	for k, v := range a {
		if b[k] != v {
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

	// Handle graceful shutdown
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

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Polling the API Server in a loop | Creates excessive load, eventually rate-limited | Use Informers with Watch streams |
| Processing events in the handler | Blocks the Informer, missed events | Enqueue keys, process in workers |
| Ignoring cache sync | Reading stale or empty data | Always `WaitForCacheSync` before reading |
| Not handling tombstones | Panics on `DeletedFinalStateUnknown` | Type-assert and handle tombstone objects |
| Hardcoding kubeconfig path | Breaks in-cluster deployment | Use `rest.InClusterConfig()` with fallback |
| Using `Clientset.Get()` in hot paths | Hammers the API Server | Use Listers from the Informer cache |
| Ignoring `resourceVersion` conflicts | Lost updates under concurrency | Use retry loops with `RetryOnConflict` |

---

## Quiz

1. **Scenario:** You are troubleshooting a custom controller that keeps receiving `403 Forbidden` errors when trying to patch Pods, even though you verified the ServiceAccount token is valid. Based on the API Server request pipeline, which stage is rejecting the request, and what are the preceding and subsequent stages?
   <details>
   <summary>Answer</summary>
   The request is being rejected at the Authorization (AuthZ) stage, which is the second main stage of the pipeline. Because the ServiceAccount token is valid, the request successfully passed the first stage, Authentication (AuthN). However, the API server determined that the authenticated identity does not have the necessary RBAC permissions to patch Pods. Since it was rejected at Authorization, the request will never reach the third stage, Admission Control (Mutating and Validating), nor will it be persisted to etcd.
   </details>

2. **Scenario:** A junior engineer on your team proposes writing a quick script that runs `kubectl get pods -o json` in a `while true; do ... sleep 1; done` loop to monitor Pod phases. You need to explain why this architectural approach is dangerous for the cluster and what pattern should be used instead. How do you justify the alternative?
   <details>
   <summary>Answer</summary>
   Polling the API Server in a tight loop places immense load on the control plane, forcing the API Server to query etcd, serialize large JSON payloads, and transmit them over the network every second. In a large cluster, this can quickly lead to rate-limiting or API Server degradation for all users. Instead, the engineer should use the Informer pattern (via client-go), which performs a single initial List followed by a highly efficient, long-lived Watch stream. This stream only pushes incremental delta events (Adds, Updates, Deletes) when actual state changes occur, and the Informer maintains a local in-memory cache allowing instant queries without hitting the API.
   </details>

3. **Scenario:** You are reviewing a custom controller's code and notice the developer is executing long-running database queries directly inside the Informer's `UpdateFunc` event handler. What specific architectural component is missing from this design, and what systemic failures will occur if this code is deployed to production?
   <details>
   <summary>Answer</summary>
   The controller is missing a Workqueue to decouple event reception from event processing. By executing slow operations directly inside the `UpdateFunc`, the developer is blocking the Informer's internal goroutines that are responsible for draining the DeltaFIFO queue. This will cause the controller to fall behind the API Server's watch stream, potentially leading to missed events or memory exhaustion as the internal queues fill up. A Workqueue solves this by allowing the event handler to instantly enqueue a string key and return immediately, while separate worker goroutines safely process the keys at a controlled rate with built-in retries.
   </details>

4. **Scenario:** Your network connection to the API Server is unstable, and your raw HTTP Watch stream (`?watch=true`) drops repeatedly. When you reconnect, you notice your local state is out of sync with the cluster. How does the concept of `resourceVersion` solve this problem, and what specific error must you handle if your disconnected period is too long?
   <details>
   <summary>Answer</summary>
   When a watch connection drops, you lose any events that occur between the disconnect and your subsequent reconnection. To prevent this data loss, you must track the `resourceVersion` of the last event you successfully processed and include it in your next request. This tells the API Server to replay all events that happened after that specific etcd revision, ensuring you don't miss any state changes. However, if you are disconnected for too long and etcd compacts that old revision, the API Server will return a `410 Gone` error, forcing you to perform a full List operation to resync your state from scratch.
   </details>

5. **Scenario:** You deploy a Mutating Admission Webhook that automatically injects a sidecar container into all Pods. Simultaneously, a security team deploys a Validating Admission Webhook that strictly forbids Pods with more than one container. When a user creates a single-container Pod, what is the exact outcome of the API request, and what does the user see?
   <details>
   <summary>Answer</summary>
   The API request will be completely rejected, and the Pod will not be persisted to etcd. In the API Server pipeline, Mutating Admission always runs before Validating Admission. Therefore, your webhook will first successfully inject the sidecar, modifying the in-flight object to have two containers. Subsequently, the security team's Validating Webhook will inspect this mutated object, see that it violates the single-container policy, and deny the request, returning a `403 Forbidden` to the user.
   </details>

6. **Scenario:** You are tasked with writing a generic cluster backup tool that must iterate over every possible resource in the cluster, including newly installed Custom Resource Definitions (CRDs) that are unknown at compile time. Why would you choose a `DynamicClient` over a standard `Clientset` for this task, and what trade-off are you making?
   <details>
   <summary>Answer</summary>
   You must choose a `DynamicClient` because it operates on unstructured data and can interact with any arbitrary Group-Version-Resource (GVR) discovered at runtime. A standard `Clientset` is strictly typed and its methods are generated at compile time, meaning it fundamentally cannot understand or interact with CRDs that were not compiled into your binary. The major trade-off of using a `DynamicClient` is the complete loss of compile-time type safety. You cannot access fields directly; instead, you must use string-based map lookups, which increases the risk of runtime panics or typos.
   </details>

7. **Scenario:** You are writing a controller that ensures a specific external cloud load balancer is configured to match the state of Kubernetes Services. Even though your controller handles all Update events perfectly, you notice that if the cloud provider's API goes down temporarily, the load balancer sometimes remains in a broken state forever. How does configuring an Informer's "resync period" solve this edge case?
   <details>
   <summary>Answer</summary>
   Configuring a resync period solves this by periodically forcing the Informer to re-evaluate all objects currently held in its local cache. When the resync timer fires, the Informer generates synthetic Update events for every cached object, even if nothing has actually changed in the Kubernetes API. This triggers your controller's event handlers and subsequent Workqueue processing, providing a self-healing mechanism to retry synchronization with the external cloud provider. It guarantees that temporary failures or missed edge cases are eventually reconciled, ensuring the desired state is strictly maintained over time.
   </details>

---

## Hands-On Exercise

**Task**: Build and run a Go program that uses a client-go Informer to watch Pods across all namespaces and report annotation changes in real time.

**Setup**:
```bash
# Ensure you have a running cluster (kind or minikube)
kind create cluster --name extending-k8s

# Create the project
mkdir -p ~/extending-k8s/pod-annotation-watcher
cd ~/extending-k8s/pod-annotation-watcher
go mod init github.com/example/pod-annotation-watcher
go get k8s.io/client-go@latest
go get k8s.io/apimachinery@latest
go get k8s.io/api@latest
go get k8s.io/klog/v2@latest
```

**Steps**:

1. **Copy the complete example from Part 5.2** into `main.go`

2. **Build and run**:
   ```bash
   go build -o pod-watcher .
   ./pod-watcher
   ```

3. **In another terminal, create and annotate pods**:
   ```bash
   # Create a pod
   k run test-pod --image=nginx

   # Add annotations
   k annotate pod test-pod team=backend priority=high

   # Modify an annotation
   k annotate pod test-pod priority=critical --overwrite

   # Remove an annotation
   k annotate pod test-pod team-

   # Delete the pod
   k delete pod test-pod
   ```

4. **Verify the watcher reports each change** in the first terminal

5. **Test the Lister** -- while the watcher runs, the initial cache report should show all cluster pods without making additional API calls

6. **Test graceful shutdown** -- press Ctrl+C and verify clean exit

7. **Cleanup**:
   ```bash
   kind delete cluster --name extending-k8s
   ```

**Success Criteria**:
- [ ] Program compiles and runs without errors
- [ ] Initial cache sync completes and reports pod count
- [ ] New pod creation is detected (ADDED event)
- [ ] Annotation changes trigger UPDATE processing
- [ ] Pod deletion is detected (DELETED event)
- [ ] Ctrl+C triggers graceful shutdown
- [ ] No API Server calls during Lister reads (verify by checking API Server audit logs or metrics)

---

## Next Module

[Module 1.2: Custom Resource Definitions Deep Dive](../module-1.2-crds-advanced/) - Define your own Kubernetes resource types with advanced validation, versioning, and subresources.
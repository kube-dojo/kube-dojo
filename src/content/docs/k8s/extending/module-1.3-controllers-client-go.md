---
title: "Module 1.3: Building Controllers with client-go"
slug: k8s/extending/module-1.3-controllers-client-go
revision_pending: false
sidebar:
  order: 4
---
# Module 1.3: Building Controllers with client-go

> **Complexity**: `[COMPLEX]` - Full controller implementation from scratch
>
> **Time to Complete**: 5 hours
>
> **Prerequisites**: Module 1.1 (API Deep Dive), Module 1.2 (CRDs Advanced), intermediate Go programming

---

## Learning Outcomes

After completing this module, you will be able to:

1. **Build** a complete Kubernetes controller from scratch using client-go Informers, Listers, and Workqueues.
2. **Implement** a reconciliation loop that creates, updates, and deletes child resources based on a custom resource spec.
3. **Apply** owner references and garbage collection so child resources are cleaned up automatically when the parent is deleted.
4. **Debug** controller issues using event recording, structured logging, and workqueue retry metrics.

---

## Why This Module Matters

Hypothetical scenario: your platform team has introduced a `WebApp` custom resource so application teams can ask for an image, a replica count, and a service port without learning every Deployment and Service field. The API server can store that object because the CRD exists, but storage alone does not create Pods, repair drift, report status, or clean up children. Without a controller, the custom resource is only a durable note in etcd, and the operational promise behind the API is still missing.

A Kubernetes controller is the engine that turns **declarative intent** into **running reality**. When you create a Deployment, it is a controller that creates and adjusts ReplicaSets, and when endpoints change behind a Service, controller logic updates the discovery objects that clients use. The API server is the source of truth for desired state, but controllers are the workers that compare that truth with observed cluster state and take the smallest safe action needed to converge.

In this module you will build a complete controller from scratch using only client-go, with no framework scaffolding hiding the moving parts. You will assemble the Informer that watches resources, the Lister that reads from the shared cache, the Workqueue that buffers keys, the reconciliation loop that creates child resources, and the retry behavior that keeps transient errors from becoming outages. Kubebuilder and controller-runtime are productive tools, but learning the client-go pattern first gives you the diagnostic vocabulary to debug generated controllers when the abstraction leaks.

The thermostat analogy is useful because it captures both the simplicity and the discipline of reconciliation. You set the desired temperature, the thermostat observes the current temperature, and it turns heating or cooling on only when the two differ. A Kubernetes controller does the same thing with `spec` and current cluster objects; it should not rely on memory of the last event, and it should be safe to run the same comparison repeatedly.

---

## Part 1: The Controller Pattern

### 1.1 Observe-Analyze-Act

Every Kubernetes controller follows a three-step loop: observe what exists, analyze the difference between desired and actual state, and act only where the difference requires a change. The loop is deliberately boring because reliability comes from repeatability. If a controller can be restarted, delayed, or asked to process the same key many times and still make the same decision, it fits the Kubernetes control-plane model.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Controller Loop                                   │
│                                                                     │
│   ┌──────────────────────────────────────────────────────────┐     │
│   │                     OBSERVE                               │     │
│   │                                                           │     │
│   │   Informer watches API Server for resource changes        │     │
│   │   Lister reads current state from local cache             │     │
│   │   Event handlers enqueue changed object keys              │     │
│   └────────────────────────┬─────────────────────────────────┘     │
│                            │                                        │
│                            ▼                                        │
│   ┌──────────────────────────────────────────────────────────┐     │
│   │                     ANALYZE                               │     │
│   │                                                           │     │
│   │   Dequeue object key from Workqueue                       │     │
│   │   Read desired state (spec) from cache                    │     │
│   │   Read actual state (owned resources) from cache          │     │
│   │   Compare desired vs actual — what needs to change?       │     │
│   └────────────────────────┬─────────────────────────────────┘     │
│                            │                                        │
│                            ▼                                        │
│   ┌──────────────────────────────────────────────────────────┐     │
│   │                       ACT                                 │     │
│   │                                                           │     │
│   │   Create / Update / Delete child resources                │     │
│   │   Update status subresource                               │     │
│   │   Emit Kubernetes Events                                  │     │
│   │   Re-enqueue on failure (with backoff)                    │     │
│   └──────────────────────────────────────────────────────────┘     │
│                                                                     │
│   Then back to OBSERVE — the loop never ends                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Level-Triggered vs Edge-Triggered

The most important design choice is that Kubernetes controllers are level-triggered, not edge-triggered. An edge-triggered system reacts to the fact that an `ADDED`, `MODIFIED`, or `DELETED` event happened, so missing an event can leave the system permanently wrong. A level-triggered controller reacts to the current level of the world: desired state from the parent resource, actual state from children, and the gap between them.

| Approach | Reacts To | Problem |
|----------|----------|---------|
| **Edge-triggered** | Individual events (ADDED, MODIFIED, DELETED) | If you miss an event, state diverges forever |
| **Level-triggered** | Current state difference (desired vs actual) | Self-healing: always converges regardless of missed events |

Kubernetes controllers are **level-triggered**, so your reconcile function should avoid asking which specific event happened. It should ask what the current desired state is, what actual resources exist right now, and what minimum API operation would make the two match. That habit is what lets controllers survive missed watch events, process restarts, queue deduplication, and humans changing child resources by hand.

Pause and predict: suppose your controller process is killed right after the API server emits an `ADDED` event for a new `WebApp` resource, but before the controller processes it. When the controller restarts several minutes later, the old watch event is gone. Before reading further, explain how a fresh LIST, an Informer cache, and level-triggered reconciliation still lead to the associated Deployment being created.

### 1.3 Idempotency

Every reconciliation must be **idempotent**, which means running it once or many times should leave the cluster in the same correct state. Idempotency is not a style preference; it is required because the same key can be enqueued repeatedly, a worker can fail after creating one child resource, and another worker may later retry the same parent. The reconcile loop must therefore read current state first, then create, update, or skip based on what it actually finds.

This means:
- Use `Create` with conflict detection, not blind creates
- Use `Update` with resource version checks
- Check if a resource already exists before creating it
- Make decisions based on current state, not event history

Stop and think: if your `syncHandler` function blindly calls `Create` on a Deployment without checking whether it already exists, the second reconciliation loop for the same `WebApp` becomes a bug instead of a harmless repeat. Decide whether that failure should be treated as expected drift, a conflict to resolve, or a signal that the controller design is not idempotent enough.

### 1.4 Worked Reconciliation Trace

Imagine a user creates a `WebApp` named `demo-app` with image `nginx:1.27`, three replicas, and port `80`. The API server persists the object and the dynamic Informer eventually observes it through the LIST/watch stream. The event handler does not create anything; it computes the key `default/demo-app`, places that key on the workqueue, and returns so observation can continue.

A worker later dequeues `default/demo-app` and starts the real reconciliation. It splits the key into namespace and name, reads the current `WebApp` from the Informer cache, applies defaults for optional fields, and then uses typed Listers to check whether a Deployment and Service already exist. At this point the controller is still only observing and analyzing; no write should happen until it has enough information to know which action is necessary.

Because this is the first reconciliation, the Deployment and Service are missing, so the controller creates both children with labels, selectors, ports, and owner references derived from the parent. Those creates are the Act phase. If the Deployment create succeeds but the Service create fails, a later retry should notice the Deployment already exists, skip recreating it, and continue with the missing Service. That is the practical value of idempotency.

After child creation, the controller updates status using the observed Deployment readiness. The status may initially say `Pending` because Pods are not ready yet, and that is still useful feedback because it proves the controller observed the parent and created the child. Later, when the Deployment controller updates readiness, the secondary Deployment watch path can enqueue the parent again, and the `WebApp` status can move toward `Running`.

This trace is also a debugging checklist. If no Deployment appears, inspect whether the parent key entered the queue and whether `syncHandler` found the `WebApp` in the cache. If the Deployment appears but status stays empty, inspect the status subresource and patch path. If manual edits to the Deployment are not repaired, inspect the owner reference and the secondary Informer handler.

---

## Part 2: Controller Architecture

### 2.1 Component Overview

The client-go controller architecture separates observation from action so that the API server is not hammered by every decision. Informers maintain a shared local cache, Listers read from that cache, event handlers enqueue lightweight keys, and workers perform reconciliation outside the watch path. This split is why a controller can watch thousands of objects while still keeping API writes deliberate and bounded.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Controller Components                             │
│                                                                     │
│   API Server                                                        │
│       │                                                             │
│       │ WATCH (primary resource: WebApp)                           │
│       ▼                                                             │
│   ┌───────────────┐    ┌──────────────┐    ┌──────────────────┐   │
│   │  Informer     │───▶│  DeltaFIFO   │───▶│  Indexer/Cache   │   │
│   │  (WebApp)     │    │              │    │                  │   │
│   └───────┬───────┘    └──────────────┘    └────────┬─────────┘   │
│           │                                          │             │
│           │ Event Handlers                          │ Lister      │
│           ▼                                          ▼             │
│   ┌───────────────┐                        ┌──────────────────┐   │
│   │  Workqueue    │                        │  Read desired    │   │
│   │  (rate-       │                        │  state from      │   │
│   │   limited)    │                        │  cache           │   │
│   └───────┬───────┘                        └──────────────────┘   │
│           │                                                        │
│           │ Dequeue keys                                          │
│           ▼                                                        │
│   ┌───────────────────────────────────────────────────────────┐   │
│   │                   syncHandler                              │   │
│   │                                                            │   │
│   │   1. Get WebApp from Lister                                │   │
│   │   2. Get/Create owned Deployment                           │   │
│   │   3. Get/Create owned Service                              │   │
│   │   4. Update WebApp status                                  │   │
│   │   5. Emit Events                                           │   │
│   │                                                            │   │
│   │   On error → re-enqueue with backoff                      │   │
│   │   On success → forget (reset backoff)                     │   │
│   └───────────────────────────────────────────────────────────┘   │
│                                                                     │
│   API Server                                                        │
│       │                                                             │
│       │ WATCH (secondary resources: Deployment, Service)           │
│       ▼                                                             │
│   ┌───────────────┐                                                │
│   │  Informers    │── Event handlers look up ownerRef             │
│   │  (Deployment, │   and enqueue the parent WebApp key           │
│   │   Service)    │                                                │
│   └───────────────┘                                                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

The diagram also shows why controller event handlers should be small. An event handler is not the place to create Deployments, patch status, or call external systems, because it runs on the observation side of the controller. The handler should extract the namespace/name key, add that key to a workqueue, and return quickly so the Informer can keep processing watch updates and cache changes.

### 2.2 Watching Owned Resources

When your controller creates a Deployment, you also need to know when that Deployment changes because child resources are part of the actual state you are responsible for reconciling. The Deployment might become ready, fail rollout, get scaled manually, or be deleted by someone debugging an incident. Watching only the parent `WebApp` would miss those child-side changes, so a complete controller watches owned Deployments and Services as secondary resources.

The trick is that a Deployment event should not enqueue the Deployment itself; it should enqueue the parent `WebApp` key. The owner reference provides that bridge. When a secondary resource changes, the controller reads its controller owner reference, checks that the owner kind is `WebApp`, builds the parent key from namespace and name, and lets the normal reconcile loop compare desired and actual state again.

Pause and predict: you manually delete a Deployment that is owned by a `WebApp` custom resource. Walk through the exact chain of events in the controller architecture diagram that leads from the Deployment watch event to the parent key entering the queue, and then explain why the replacement Deployment should be created by the parent reconciliation rather than by the delete handler itself.

```go
// When a Deployment changes, enqueue the owning WebApp
deploymentInformer.AddEventHandler(cache.ResourceEventHandlerFuncs{
    AddFunc: func(obj interface{}) {
        controller.handleOwnedResource(obj)
    },
    UpdateFunc: func(old, new interface{}) {
        controller.handleOwnedResource(new)
    },
    DeleteFunc: func(obj interface{}) {
        controller.handleOwnedResource(obj)
    },
})

func (c *Controller) handleOwnedResource(obj interface{}) {
    object, ok := obj.(metav1.Object)
    if !ok {
        tombstone, ok := obj.(cache.DeletedFinalStateUnknown)
        if !ok {
            return
        }
        object, ok = tombstone.Obj.(metav1.Object)
        if !ok {
            return
        }
    }

    // Look for an owner reference pointing to our CRD
    ownerRef := metav1.GetControllerOf(object)
    if ownerRef == nil || ownerRef.Kind != "WebApp" {
        return
    }

    // Enqueue the parent WebApp
    webapp, err := c.webappLister.WebApps(object.GetNamespace()).Get(ownerRef.Name)
    if err != nil {
        return
    }
    c.enqueue(webapp)
}
```

Notice that `handleOwnedResource` also handles tombstones. A delete event may arrive as `cache.DeletedFinalStateUnknown` when the cache no longer has the final object in its expected type, especially around missed deletes or relists. Production controllers need this defensive path because a panic in a delete handler is exactly the kind of failure that turns a normal drift event into a controller outage.

### 2.3 Cache Boundaries and Event Pressure

The Informer cache is a boundary between the API server and your reconciliation code. Instead of every worker issuing a live GET for every parent and child, the shared cache performs watches and stores objects locally. That design reduces API server pressure, but it also means the controller must respect cache synchronization and eventual consistency. A cached read is fast and scalable, but it is only trustworthy after the Informer has completed its initial LIST.

Queue keys are the second boundary. They intentionally throw away event payload details because the payload may be stale by the time a worker sees it. If a `WebApp` is updated repeatedly while one key is already waiting, the queue can collapse the burst into one future reconciliation. The worker then reads the latest object from the cache and makes a decision based on the final state that matters.

This design is different from a message queue that promises to deliver every event for business processing. A controller is not trying to bill for every modification or preserve an audit log; Kubernetes already has API server audit mechanisms for that. The controller is trying to converge managed resources, and convergence is usually more reliable when duplicate and intermediate events are harmless rather than mandatory.

Cache boundaries also change how you debug. If controller logs say a child resource is missing but `kubectl get` shows it exists, ask whether the relevant Informer has synced, whether the controller is watching the correct namespace, and whether RBAC allows the watch. If the cache is correct but the queue is not moving, inspect worker count, retry delays, and whether a poison-pill key is consuming attention.

Finally, remember that the cache stores Kubernetes objects, not your intentions. If your controller supports user-provided defaults, generated names, or external data, your reconcile loop must be able to reconstruct the desired child shape every time from the current parent spec and any authoritative external state. Hidden in-memory state makes restarts dangerous and makes leader transitions almost impossible to reason about.

---

## Part 3: The Complete Controller

### 3.1 Project Structure

A controller project needs more than a reconcile function because it is both a Kubernetes client and a long-running process. The entry point builds configuration, starts Informer factories, wires event recording, and handles shutdown signals. The controller file owns cache wiring, queue processing, reconciliation, and child resource construction. Keeping those responsibilities separated makes it easier to test reconciliation behavior without mixing it with process lifecycle code.

```
webapp-controller/
├── go.mod
├── go.sum
├── main.go              # Entry point, signal handling, leader election
├── controller.go        # Controller struct and reconcile logic
├── crd/
│   └── webapp-crd.yaml  # CRD definition from Module 1.2
└── deploy/
    └── rbac.yaml        # RBAC for the controller ServiceAccount
```

This module keeps the project intentionally small so the client-go pieces stay visible. In a larger controller you would usually split API types, generated clients, controller packages, manifests, and tests into separate directories, but the same control flow remains. The important habit is to know which code reads from caches, which code writes to the API server, and which code exists only to start or stop the process cleanly.

### 3.2 CRD Types (Simplified)

Since we are not using code generation, the Informer for `WebApp` will deliver unstructured objects and the controller will convert them into a small local Go type before reconciling. That is not how most production operators are written, because generated typed clients give stronger compile-time safety and cleaner listers. It is useful here because it exposes what the dynamic client is doing and makes the bridge between generic Kubernetes objects and domain-specific controller logic explicit.

```go
// types.go
package main

import metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"

// WebApp represents our custom resource.
type WebApp struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`
	Spec              WebAppSpec   `json:"spec"`
	Status            WebAppStatus `json:"status,omitempty"`
}

type WebAppSpec struct {
	Image    string `json:"image"`
	Replicas *int32 `json:"replicas,omitempty"`
	Port     int32  `json:"port,omitempty"`
}

type WebAppStatus struct {
	ReadyReplicas int32  `json:"readyReplicas,omitempty"`
	Phase         string `json:"phase,omitempty"`
}
```

### 3.3 Controller Implementation

The implementation below is the heart of the module and it preserves the full client-go flow: typed clients for built-in resources, a dynamic client for the CRD, Informer factories for observation, Listers for cached reads, a typed rate-limiting queue for work, and an event recorder for user-visible feedback. Read it in layers rather than trying to memorize every import. First follow how objects enter the queue, then follow how workers drain the queue, and only then study the resource-specific decisions inside `syncHandler`.

Before running this, predict which API calls happen when a new `WebApp` appears with an image, three replicas, and a service port. You should be able to name the cache read for the parent, the cached reads for the owned Deployment and Service, the create calls for missing children, and the status patch that reports observed readiness. If you cannot trace those operations, pause on the code comments and map them back to Observe, Analyze, and Act.

```go
// controller.go
package main

import (
	"context"
	"encoding/json"
	"fmt"

	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/runtime/schema"
	utilruntime "k8s.io/apimachinery/pkg/util/runtime"
	"k8s.io/apimachinery/pkg/util/intstr"
	"k8s.io/client-go/dynamic"
	"k8s.io/client-go/dynamic/dynamicinformer"
	"k8s.io/client-go/informers"
	"k8s.io/client-go/kubernetes"
	appslisters "k8s.io/client-go/listers/apps/v1"
	corelisters "k8s.io/client-go/listers/core/v1"
	"k8s.io/client-go/tools/cache"
	"k8s.io/client-go/tools/record"
	"k8s.io/client-go/util/workqueue"
	"k8s.io/klog/v2"
)

var webappGVR = schema.GroupVersionResource{
	Group:    "apps.kubedojo.io",
	Version:  "v1beta1",
	Resource: "webapps",
}

const (
	controllerName = "webapp-controller"
	maxRetries     = 5
)

// Controller manages WebApp resources.
type Controller struct {
	kubeClient    kubernetes.Interface
	dynamicClient dynamic.Interface

	// Listers for reading from cache
	deploymentLister appslisters.DeploymentLister
	serviceLister    corelisters.ServiceLister

	// Informer synced functions
	deploymentSynced cache.InformerSynced
	serviceSynced    cache.InformerSynced
	webappSynced     cache.InformerSynced

	// Dynamic informer for our CRD
	webappInformer cache.SharedIndexInformer

	// Workqueue
	queue workqueue.TypedRateLimitingInterface[string]

	// Event recorder
	recorder record.EventRecorder
}

// NewController creates a new WebApp controller.
func NewController(
	kubeClient kubernetes.Interface,
	dynamicClient dynamic.Interface,
	kubeInformerFactory informers.SharedInformerFactory,
	dynamicInformerFactory dynamicinformer.DynamicSharedInformerFactory,
	recorder record.EventRecorder,
) *Controller {

	// Get informers for owned resources
	deploymentInformer := kubeInformerFactory.Apps().V1().Deployments()
	serviceInformer := kubeInformerFactory.Core().V1().Services()

	// Get dynamic informer for our CRD
	webappInformer := dynamicInformerFactory.ForResource(webappGVR).Informer()

	c := &Controller{
		kubeClient:       kubeClient,
		dynamicClient:    dynamicClient,
		deploymentLister: deploymentInformer.Lister(),
		serviceLister:    serviceInformer.Lister(),
		deploymentSynced: deploymentInformer.Informer().HasSynced,
		serviceSynced:    serviceInformer.Informer().HasSynced,
		webappSynced:     webappInformer.HasSynced,
		webappInformer:   webappInformer,
		queue: workqueue.NewTypedRateLimitingQueueWithConfig(
			workqueue.DefaultTypedControllerRateLimiter[string](),
			workqueue.TypedRateLimitingQueueConfig[string]{
				Name: controllerName,
			},
		),
		recorder: recorder,
	}

	// Set up event handlers for WebApp (primary resource)
	webappInformer.AddEventHandler(cache.ResourceEventHandlerFuncs{
		AddFunc: func(obj interface{}) {
			c.enqueueWebApp(obj)
		},
		UpdateFunc: func(old, new interface{}) {
			c.enqueueWebApp(new)
		},
		DeleteFunc: func(obj interface{}) {
			c.enqueueWebApp(obj)
		},
	})

	// Set up event handlers for owned Deployments
	deploymentInformer.Informer().AddEventHandler(cache.ResourceEventHandlerFuncs{
		AddFunc: func(obj interface{}) {
			c.handleOwnedObject(obj)
		},
		UpdateFunc: func(old, new interface{}) {
			c.handleOwnedObject(new)
		},
		DeleteFunc: func(obj interface{}) {
			c.handleOwnedObject(obj)
		},
	})

	// Set up event handlers for owned Services
	serviceInformer.Informer().AddEventHandler(cache.ResourceEventHandlerFuncs{
		AddFunc: func(obj interface{}) {
			c.handleOwnedObject(obj)
		},
		UpdateFunc: func(old, new interface{}) {
			c.handleOwnedObject(new)
		},
		DeleteFunc: func(obj interface{}) {
			c.handleOwnedObject(obj)
		},
	})

	return c
}

func (c *Controller) enqueueWebApp(obj interface{}) {
	key, err := cache.MetaNamespaceKeyFunc(obj)
	if err != nil {
		utilruntime.HandleError(fmt.Errorf("getting key for object: %v", err))
		return
	}
	c.queue.Add(key)
}

func (c *Controller) handleOwnedObject(obj interface{}) {
	var object metav1.Object
	var ok bool

	if object, ok = obj.(metav1.Object); !ok {
		tombstone, ok := obj.(cache.DeletedFinalStateUnknown)
		if !ok {
			utilruntime.HandleError(fmt.Errorf("error decoding object, invalid type"))
			return
		}
		object, ok = tombstone.Obj.(metav1.Object)
		if !ok {
			utilruntime.HandleError(fmt.Errorf("error decoding tombstone, invalid type"))
			return
		}
	}

	ownerRef := metav1.GetControllerOf(object)
	if ownerRef == nil {
		return
	}

	if ownerRef.Kind != "WebApp" {
		return
	}

	// Enqueue the parent WebApp
	key := object.GetNamespace() + "/" + ownerRef.Name
	c.queue.Add(key)
}

// Run starts the controller.
func (c *Controller) Run(ctx context.Context, workers int) error {
	defer utilruntime.HandleCrash()
	defer c.queue.ShutDown()

	klog.Infof("Starting %s", controllerName)

	// Wait for all caches to sync
	klog.Info("Waiting for informer caches to sync")
	if ok := cache.WaitForCacheSync(ctx.Done(),
		c.deploymentSynced,
		c.serviceSynced,
		c.webappSynced,
	); !ok {
		return fmt.Errorf("failed to wait for caches to sync")
	}

	klog.Infof("Starting %d workers", workers)
	for i := 0; i < workers; i++ {
		go c.runWorker(ctx)
	}

	klog.Info("Controller started")
	<-ctx.Done()
	klog.Info("Shutting down controller")
	return nil
}

func (c *Controller) runWorker(ctx context.Context) {
	for c.processNextWorkItem(ctx) {
	}
}

func (c *Controller) processNextWorkItem(ctx context.Context) bool {
	key, shutdown := c.queue.Get()
	if shutdown {
		return false
	}
	defer c.queue.Done(key)

	err := c.syncHandler(ctx, key)
	if err == nil {
		// Success — reset the rate limiter for this key
		c.queue.Forget(key)
		return true
	}

	// Failure — re-enqueue with rate limiting
	if c.queue.NumRequeues(key) < maxRetries {
		klog.Warningf("Error syncing %q (retry %d/%d): %v",
			key, c.queue.NumRequeues(key)+1, maxRetries, err)
		c.queue.AddRateLimited(key)
		return true
	}

	// Too many retries — give up on this key
	klog.Errorf("Dropping %q after %d retries: %v", key, maxRetries, err)
	c.queue.Forget(key)
	utilruntime.HandleError(err)
	return true
}

// syncHandler is the core reconciliation logic.
func (c *Controller) syncHandler(ctx context.Context, key string) error {
	namespace, name, err := cache.SplitMetaNamespaceKey(key)
	if err != nil {
		return fmt.Errorf("invalid resource key: %s", key)
	}

	// OBSERVE: Get the WebApp from the cache
	unstructuredObj, err := c.webappInformer.GetIndexer().ByIndex(
		cache.NamespaceIndex, namespace)
	if err != nil {
		return err
	}

	// Find the specific WebApp
	var webapp *WebApp
	for _, item := range unstructuredObj {
		u := item.(*unstructured.Unstructured)
		if u.GetName() == name && u.GetNamespace() == namespace {
			webapp, err = unstructuredToWebApp(u)
			if err != nil {
				return fmt.Errorf("converting unstructured to WebApp: %v", err)
			}
			break
		}
	}

	if webapp == nil {
		// WebApp was deleted — owned resources will be garbage collected
		// via OwnerReferences
		klog.Infof("WebApp %s deleted, owned resources will be GC'd", key)
		return nil
	}

	// Set defaults
	replicas := int32(2)
	if webapp.Spec.Replicas != nil {
		replicas = *webapp.Spec.Replicas
	}
	port := int32(8080)
	if webapp.Spec.Port > 0 {
		port = webapp.Spec.Port
	}

	// ANALYZE + ACT: Ensure Deployment exists and matches spec
	deploymentName := webapp.Name
	deployment, err := c.deploymentLister.Deployments(namespace).Get(deploymentName)
	if errors.IsNotFound(err) {
		// Create the Deployment
		deployment, err = c.kubeClient.AppsV1().Deployments(namespace).Create(
			ctx,
			c.newDeployment(webapp, deploymentName, replicas, port),
			metav1.CreateOptions{},
		)
		if err != nil {
			return fmt.Errorf("creating deployment: %v", err)
		}
		klog.Infof("Created Deployment %s/%s", namespace, deploymentName)
		c.recorder.Eventf(webapp, corev1.EventTypeNormal, "DeploymentCreated",
			"Created Deployment %s", deploymentName)
	} else if err != nil {
		return fmt.Errorf("getting deployment: %v", err)
	} else {
		// Deployment exists — check if it needs updating
		if *deployment.Spec.Replicas != replicas ||
			deployment.Spec.Template.Spec.Containers[0].Image != webapp.Spec.Image {
			deploymentCopy := deployment.DeepCopy()
			deploymentCopy.Spec.Replicas = &replicas
			deploymentCopy.Spec.Template.Spec.Containers[0].Image = webapp.Spec.Image
			_, err = c.kubeClient.AppsV1().Deployments(namespace).Update(
				ctx, deploymentCopy, metav1.UpdateOptions{})
			if err != nil {
				return fmt.Errorf("updating deployment: %v", err)
			}
			klog.Infof("Updated Deployment %s/%s", namespace, deploymentName)
			c.recorder.Eventf(webapp, corev1.EventTypeNormal, "DeploymentUpdated",
				"Updated Deployment %s (replicas=%d, image=%s)",
				deploymentName, replicas, webapp.Spec.Image)
		}
	}

	// Ensure Service exists
	serviceName := webapp.Name
	_, err = c.serviceLister.Services(namespace).Get(serviceName)
	if errors.IsNotFound(err) {
		_, err = c.kubeClient.CoreV1().Services(namespace).Create(
			ctx,
			c.newService(webapp, serviceName, port),
			metav1.CreateOptions{},
		)
		if err != nil {
			return fmt.Errorf("creating service: %v", err)
		}
		klog.Infof("Created Service %s/%s", namespace, serviceName)
		c.recorder.Eventf(webapp, corev1.EventTypeNormal, "ServiceCreated",
			"Created Service %s", serviceName)
	} else if err != nil {
		return fmt.Errorf("getting service: %v", err)
	}

	// Update status
	err = c.updateStatus(ctx, webapp, deployment)
	if err != nil {
		return fmt.Errorf("updating status: %v", err)
	}

	return nil
}

func (c *Controller) newDeployment(webapp *WebApp, name string, replicas int32, port int32) *appsv1.Deployment {
	labels := map[string]string{
		"app":                          name,
		"app.kubernetes.io/managed-by": controllerName,
	}

	return &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      name,
			Namespace: webapp.Namespace,
			OwnerReferences: []metav1.OwnerReference{
				*metav1.NewControllerRef(webapp, schema.GroupVersionKind{
					Group:   "apps.kubedojo.io",
					Version: "v1beta1",
					Kind:    "WebApp",
				}),
			},
			Labels: labels,
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: &replicas,
			Selector: &metav1.LabelSelector{
				MatchLabels: labels,
			},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels: labels,
				},
				Spec: corev1.PodSpec{
					Containers: []corev1.Container{
						{
							Name:  "app",
							Image: webapp.Spec.Image,
							Ports: []corev1.ContainerPort{
								{
									ContainerPort: port,
									Protocol:      corev1.ProtocolTCP,
								},
							},
						},
					},
				},
			},
		},
	}
}

func (c *Controller) newService(webapp *WebApp, name string, port int32) *corev1.Service {
	return &corev1.Service{
		ObjectMeta: metav1.ObjectMeta{
			Name:      name,
			Namespace: webapp.Namespace,
			OwnerReferences: []metav1.OwnerReference{
				*metav1.NewControllerRef(webapp, schema.GroupVersionKind{
					Group:   "apps.kubedojo.io",
					Version: "v1beta1",
					Kind:    "WebApp",
				}),
			},
			Labels: map[string]string{
				"app":                          name,
				"app.kubernetes.io/managed-by": controllerName,
			},
		},
		Spec: corev1.ServiceSpec{
			Selector: map[string]string{
				"app": name,
			},
			Ports: []corev1.ServicePort{
				{
					Port:       port,
					TargetPort: intstr.FromInt32(port),
					Protocol:   corev1.ProtocolTCP,
				},
			},
			Type: corev1.ServiceTypeClusterIP,
		},
	}
}

func (c *Controller) updateStatus(ctx context.Context, webapp *WebApp, deployment *appsv1.Deployment) error {
	readyReplicas := int32(0)
	phase := "Pending"

	if deployment != nil {
		readyReplicas = deployment.Status.ReadyReplicas
		if deployment.Status.ReadyReplicas == *deployment.Spec.Replicas {
			phase = "Running"
		} else if deployment.Status.ReadyReplicas > 0 {
			phase = "Deploying"
		}
	}

	// Build the status patch
	patch := map[string]interface{}{
		"status": map[string]interface{}{
			"readyReplicas": readyReplicas,
			"phase":         phase,
		},
	}

	patchBytes, err := json.Marshal(patch)
	if err != nil {
		return err
	}

	_, err = c.dynamicClient.Resource(webappGVR).Namespace(webapp.Namespace).Patch(
		ctx,
		webapp.Name,
		"application/merge-patch+json",
		patchBytes,
		metav1.PatchOptions{},
		"status",
	)
	return err
}

// unstructuredToWebApp converts an unstructured object to a WebApp.
func unstructuredToWebApp(u *unstructured.Unstructured) (*WebApp, error) {
	data, err := json.Marshal(u.Object)
	if err != nil {
		return nil, err
	}
	var webapp WebApp
	if err := json.Unmarshal(data, &webapp); err != nil {
		return nil, err
	}
	// Copy ObjectMeta fields that are needed
	webapp.Name = u.GetName()
	webapp.Namespace = u.GetNamespace()
	webapp.UID = u.GetUID()
	return &webapp, nil
}
```

### 3.4 Main Entry Point

The main entry point is deliberately smaller than the controller because process startup should prepare dependencies and then hand control to the reconciliation engine. It supports both in-cluster configuration and a local kubeconfig, which lets you run the controller against a kind cluster during the lab and later deploy the same binary into Kubernetes. It also starts both Informer factories before calling `Run`, giving the controller a chance to wait for cache synchronization before workers begin acting.

```go
// main.go
package main

import (
	"context"
	"os"
	"os/signal"
	"path/filepath"
	"syscall"
	"time"

	"k8s.io/client-go/dynamic"
	"k8s.io/client-go/dynamic/dynamicinformer"
	"k8s.io/client-go/informers"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/kubernetes/scheme"
	typedcorev1 "k8s.io/client-go/kubernetes/typed/core/v1"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/client-go/rest"
	"k8s.io/client-go/tools/clientcmd"
	"k8s.io/client-go/tools/record"
	"k8s.io/klog/v2"
)

func main() {
	klog.InitFlags(nil)

	// Build config (supports both in-cluster and kubeconfig)
	config, err := buildConfig()
	if err != nil {
		klog.Fatalf("Error building config: %v", err)
	}

	// Create clients
	kubeClient, err := kubernetes.NewForConfig(config)
	if err != nil {
		klog.Fatalf("Error creating kubernetes client: %v", err)
	}

	dynamicClient, err := dynamic.NewForConfig(config)
	if err != nil {
		klog.Fatalf("Error creating dynamic client: %v", err)
	}

	// Create informer factories
	kubeInformerFactory := informers.NewSharedInformerFactory(kubeClient, 30*time.Second)
	dynamicInformerFactory := dynamicinformer.NewDynamicSharedInformerFactory(
		dynamicClient, 30*time.Second)

	// Create event recorder
	eventBroadcaster := record.NewBroadcaster()
	eventBroadcaster.StartStructuredLogging(0)
	eventBroadcaster.StartRecordingToSink(&typedcorev1.EventSinkImpl{
		Interface: kubeClient.CoreV1().Events(""),
	})
	recorder := eventBroadcaster.NewRecorder(scheme.Scheme, corev1.EventSource{
		Component: controllerName,
	})

	// Create controller
	controller := NewController(
		kubeClient,
		dynamicClient,
		kubeInformerFactory,
		dynamicInformerFactory,
		recorder,
	)

	// Set up shutdown context
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
	go func() {
		sig := <-sigCh
		klog.Infof("Received signal %v, initiating shutdown", sig)
		cancel()
	}()

	// Start informer factories
	kubeInformerFactory.Start(ctx.Done())
	dynamicInformerFactory.Start(ctx.Done())

	// Run controller with 2 workers
	if err := controller.Run(ctx, 2); err != nil {
		klog.Fatalf("Error running controller: %v", err)
	}
}

func buildConfig() (*rest.Config, error) {
	// Try in-cluster config first
	config, err := rest.InClusterConfig()
	if err == nil {
		return config, nil
	}

	// Fall back to kubeconfig
	home, _ := os.UserHomeDir()
	kubeconfig := filepath.Join(home, ".kube", "config")
	return clientcmd.BuildConfigFromFlags("", kubeconfig)
}
```

The order of startup matters. If workers start before caches sync, the controller can make decisions from an empty or partial worldview and create resources that already exist. If the process ignores signals, Kubernetes can terminate it while a worker is midway through a reconciliation attempt. The combination of context cancellation, cache sync, queue shutdown, and worker loops gives you a controller that behaves predictably when Pods are rolled, nodes drain, or leadership changes.

### 3.5 Reading `syncHandler` as a Contract

The `syncHandler` function is more than a long function body; it is the contract between the `WebApp` API and the resources the controller owns. The first part of the contract says that a queue key must identify a valid namespace/name pair. Bad keys are programming errors, so returning an error and letting the worker record it is better than silently ignoring malformed input.

The next part says that deletion of the parent is not an error. When the controller cannot find the `WebApp` in the cache, it assumes the parent was deleted and returns successfully because owner references let garbage collection handle the children. That return path is easy to miss, but it prevents a deleted parent from becoming a permanently failing queue item.

Defaulting is another contract boundary. In this module, the controller applies defaults for replicas and port before building child objects, while the CRD schema also defines defaults for those fields. In production you should be clear about where defaulting happens and how it is tested. If defaults live in the CRD schema, clients and controllers see a more consistent object. If defaults live only in controller code, other API readers may see missing fields until reconciliation interprets them.

The Deployment reconciliation block demonstrates create-or-update behavior. On not-found, the controller creates a child from the desired shape. On other read errors, it returns the error because the controller does not know enough to proceed. On an existing Deployment, it compares only the fields it owns, such as replica count and image, then deep-copies the object before updating so it does not mutate cache state directly.

The Service block is simpler because the preserved code creates the Service when missing and otherwise leaves it alone. That is a design choice worth noticing. If the `WebApp` port changes, a stricter controller might patch the Service, while a conservative controller might treat Service port changes as immutable and report a condition. The right answer depends on the API contract you document for `WebApp`.

Status reconciliation closes the loop for users. A parent resource that creates children but never reports observed state forces users to inspect Deployments manually, which defeats part of the value of a higher-level API. The status patch should communicate what the controller has observed, not what it hopes will happen. That is why ready replicas come from the Deployment status rather than directly from `spec.replicas`.

Event recording serves a different audience from status. Status is durable state on the custom resource, while Events are a recent history of notable transitions that show up in `kubectl describe`. A good controller uses both: status for machine-readable conditions and progress, Events for human-readable explanations of creates, updates, and failures. Logs are still useful, but they should not be the only way a resource owner learns what happened.

When you later move from client-go to controller-runtime, keep this contract model. The framework will rename some surfaces, generate reconcilers, and provide helpers, but it cannot decide your ownership semantics, retry classification, status vocabulary, or idempotency rules. Those decisions are part of your API design, not merely part of your Go implementation.

---

## Part 4: Rate Limiting and Retry Strategies

### 4.1 Built-in Rate Limiters

Errors are normal in controller code because the API server can reject writes, webhooks can time out, resource versions can conflict, and users can submit invalid desired state. The workqueue is where a controller turns those errors into controlled retries instead of tight failure loops. client-go provides several rate limiters, and the default controller rate limiter combines per-item exponential backoff with an overall token bucket so one broken object cannot consume all worker capacity.

```go
// Default: combines exponential backoff with a bucket rate limiter
queue := workqueue.NewTypedRateLimitingQueue(
    workqueue.DefaultTypedControllerRateLimiter[string](),
)

// Custom: exponential backoff (5ms base, 1000s max)
queue := workqueue.NewTypedRateLimitingQueue(
    workqueue.NewTypedItemExponentialFailureRateLimiter[string]
    (
        5*time.Millisecond,    // base delay
        1000*time.Second,      // max delay
    ),
)

// Custom: fixed rate (10 items/sec, burst of 100)
queue := workqueue.NewTypedRateLimitingQueue(
    &workqueue.TypedBucketRateLimiter[string]{
        Limiter: rate.NewLimiter(rate.Limit(10), 100),
    },
)

// Combine multiple limiters (all must allow)
queue := workqueue.NewTypedRateLimitingQueue(
    workqueue.NewTypedMaxOfRateLimiter(
        workqueue.NewTypedItemExponentialFailureRateLimiter[string]
        (
            5*time.Millisecond, 60*time.Second),
        &workqueue.TypedBucketRateLimiter[string]{
            Limiter: rate.NewLimiter(rate.Limit(10), 100)},
    ),
)
```

The examples show several shapes of retry control, but the design question is always the same: is this error likely to succeed later without user intervention, and how quickly should the controller try again? A conflict can often be retried soon because another writer changed the object first. A validation error caused by an invalid spec should usually be surfaced through status or an Event, then forgotten until the user changes the resource.

### 4.2 Retry Best Practices

| Practice | Why |
|----------|-----|
| Cap max retries (e.g., 5-15) | Prevents infinite retry loops |
| Use exponential backoff | Prevents thundering herd on transient failures |
| Log retries with count | Enables monitoring and alerting |
| Forget on success | Resets backoff for next failure |
| Distinguish retryable vs fatal errors | Do not retry validation errors |

Stop and think: a user creates a `WebApp` with a spec that contains a value your controller maps into an invalid Deployment, causing the API server to reject creation. Decide whether your controller should retry with exponential backoff, update status with a clear condition, emit a warning Event, or combine those behaviors. The important distinction is whether time can fix the problem or whether the user must change desired state.

```go
func (c *Controller) processNextWorkItem(ctx context.Context) bool {
    key, shutdown := c.queue.Get()
    if shutdown {
        return false
    }
    defer c.queue.Done(key)

    err := c.syncHandler(ctx, key)

    switch {
    case err == nil:
        c.queue.Forget(key)
    case errors.IsConflict(err):
        // Resource version conflict — retry immediately
        klog.V(4).Infof("Conflict on %s, retrying", key)
        c.queue.AddRateLimited(key)
    case errors.IsNotFound(err):
        // Resource gone — no point retrying
        klog.V(4).Infof("Resource %s not found, skipping", key)
        c.queue.Forget(key)
    case c.queue.NumRequeues(key) < maxRetries:
        klog.Warningf("Error syncing %s (attempt %d): %v",
            key, c.queue.NumRequeues(key)+1, err)
        c.queue.AddRateLimited(key)
    default:
        klog.Errorf("Dropping %s after %d attempts: %v",
            key, maxRetries, err)
        c.queue.Forget(key)
    }

    return true
}
```

Retry handling also affects observability. A controller that drops a key after too many attempts without recording an Event or status condition leaves users guessing, while a controller that retries forever can hide a poison-pill object behind noisy logs. The production pattern is to rate-limit transient failures, forget successful keys, classify permanent failures where possible, and expose enough information for the resource owner to repair their spec.

### 4.3 Classifying Failures

Failure classification starts with asking whether retrying the same desired state could succeed later. API server timeouts, temporary admission webhook failures, resource-version conflicts, and short network partitions are usually retryable. Invalid field values, forbidden operations caused by RBAC, and immutable field changes usually require a spec change, permission change, or different controller action. The queue can delay retries, but it cannot make an invalid child object valid.

Conflicts deserve special attention because they are common in Kubernetes. If another actor updated a child resource between your read and update, the API server may reject your write because the resource version is stale. The safest response is to requeue and let the next reconciliation read the latest version from the cache or API. Trying to patch blindly without understanding ownership can accidentally erase someone else's fields.

Not-found errors need context. A missing parent often means deletion has already converged, so success is appropriate. A missing child can mean the controller should recreate it, but only if that child is still part of desired state and the parent still exists. Treating every not-found as a retryable error creates noisy loops after legitimate deletes.

For user-facing APIs, permanent failures should become part of the resource's observed state. A `WebApp` with an invalid image policy, forbidden port, or impossible child spec should show a clear condition or Event rather than simply disappearing into controller logs. That feedback loop is what turns a controller from an invisible background process into a reliable API implementation.

---

## Part 5: Graceful Shutdown

### 5.1 Shutdown Sequence

A controller must shut down cleanly because Kubernetes treats controller Pods like any other workload: they are rescheduled, rolled, evicted, and terminated during maintenance. The controller cannot assume that a worker will always finish naturally, so it needs a predictable shutdown sequence that stops new observations, lets workers finish their current item, and releases process resources. The goal is not to preserve an in-memory queue forever; the goal is to stop without corrupting the control loop, because future LIST and watch activity can rediscover current state.

```
Signal received (SIGTERM/SIGINT)
    │
    ├── 1. Cancel context → informers stop watching
    │
    ├── 2. queue.ShutDown() → workers drain remaining items
    │
    ├── 3. Workers finish current item → return false
    │
    ├── 4. Event broadcaster stops
    │
    └── 5. Process exits
```

### 5.2 Implementation

The graceful shutdown path is already built into our controller through context cancellation and `queue.ShutDown`. When the process receives `SIGTERM` or `SIGINT`, `main` cancels the context, Informer factories stop watching, and `Run` eventually returns after the workers stop. That pattern works locally during the lab and also maps cleanly to Kubernetes termination behavior when the controller runs in a Pod.

The key points are:

1. `ctx.Done()` stops the informers
2. `defer c.queue.ShutDown()` in `Run()` drains the queue
3. Workers check `shutdown` from `queue.Get()` and exit
4. `defer cancel()` in `main()` ensures cleanup on any exit path

The subtle part is that graceful shutdown and idempotency support each other. If a worker is interrupted after creating a Deployment but before updating status, the next reconciliation should observe that the Deployment already exists and continue from there. A controller that stores essential progress only in memory is fragile; a controller that derives progress from cluster state can recover after ordinary process lifecycle events.

### 5.3 Shutdown Failure Modes

The most common shutdown bug is starting new work after cancellation has begun. If Informers stop but workers continue to make decisions from stale caches for too long, the controller can act on an increasingly old view of the cluster. Passing the same context through client calls and worker loops helps the process stop making writes once Kubernetes has asked the Pod to terminate.

Another subtle bug is assuming that queue shutdown means every desired state has been reconciled. The in-memory queue is not durable, and that is acceptable because the API server remains the durable source of desired state. After a restart, the Informer LIST can rediscover parents and children, and level-triggered reconciliation can repair anything unfinished. This is why correctness should come from cluster state, not from draining every historical queue item.

Event broadcasters and log flushing also matter during shutdown. A controller that exits immediately after a failure may lose the human-visible clue that would have explained the next retry. In a production deployment, combine graceful process handling with Kubernetes readiness, sensible termination grace periods, and leader election callbacks so the active reconciler steps down cleanly.

---

## Part 6: Leader Election

### 6.1 Why Leader Election?

When you run multiple replicas of your controller for high availability, only **one** should be actively reconciling at a time unless the controller is explicitly designed for multi-leader operation. Multiple active reconcilers can race on status updates, duplicate Events, and fight over child resources. Leader election uses a Kubernetes Lease resource in the coordination API to let one replica hold leadership while other replicas remain warm standbys.

```go
// main.go — add leader election
import (
    "k8s.io/client-go/tools/leaderelection"
    "k8s.io/client-go/tools/leaderelection/resourcelock"
)

func runWithLeaderElection(ctx context.Context, kubeClient kubernetes.Interface,
    startFunc func(ctx context.Context)) {

    id, _ := os.Hostname()

    lock := &resourcelock.LeaseLock{
        LeaseMeta: metav1.ObjectMeta{
            Name:      "webapp-controller-leader",
            Namespace: "webapp-system",
        },
        Client: kubeClient.CoordinationV1(),
        LockConfig: resourcelock.ResourceLockConfig{
            Identity: id,
        },
    }

    leaderelection.RunOrDie(ctx, leaderelection.LeaderElectionConfig{
        Lock:            lock,
        LeaseDuration:   15 * time.Second,
        RenewDeadline:   10 * time.Second,
        RetryPeriod:     2 * time.Second,
        Callbacks: leaderelection.LeaderCallbacks{
            OnStartedLeading: func(ctx context.Context) {
                klog.Info("Became leader, starting controller")
                startFunc(ctx)
            },
            OnStoppedLeading: func() {
                klog.Info("Lost leadership, shutting down")
                os.Exit(0)
            },
            OnNewLeader: func(identity string) {
                if identity == id {
                    return
                }
                klog.Infof("New leader elected: %s", identity)
            },
        },
        ReleaseOnCancel: true,
    })
}
```

Leader election is not a substitute for idempotency. The active leader can still crash after a partial action, and the next leader must be able to reconcile from the state it inherits. Treat the Lease as a way to reduce unnecessary concurrent writers, not as a guarantee that only one process ever touched a resource during its lifetime.

### 6.2 Leader Election Parameters

| Parameter | Typical Value | Description |
|-----------|--------------|-------------|
| LeaseDuration | 15s | How long a non-leader waits before trying to acquire |
| RenewDeadline | 10s | How long the leader has to renew before losing the lease |
| RetryPeriod | 2s | How often to retry acquiring the lease |
| ReleaseOnCancel | true | Release lease on graceful shutdown |

Pause and predict: you have two replicas of your controller running, and Replica A is the leader. Replica A experiences a network partition and cannot reach the API server, but its process is still running. Use the lease duration, renew deadline, and retry period to explain when Replica B can become leader and why Replica A must stop reconciling once it can no longer renew.

### 6.3 Leadership and Reconciliation Safety

Leader election protects the cluster from unnecessary duplicate writers, but it also introduces timing windows that your reconciliation code must tolerate. A leader may lose access to the API server, fail to renew its Lease, and continue running for a short time until its callback stops the process. Another replica may later acquire leadership and observe children that the old leader partially changed. Idempotent reconciliation is what makes that handoff safe.

The Lease timings are operational tradeoffs. Short durations fail over quickly but increase sensitivity to API server latency and network blips. Longer durations reduce accidental leadership churn but extend the time before a standby replica takes over after a real failure. There is no universal setting; choose values based on how disruptive duplicate reconciliation would be, how quickly the controller must repair drift, and how stable the control-plane network is.

You should also decide what non-leaders do. In many controllers, non-leaders start clients and wait inside the leader-election loop without running workers. That keeps them ready to take over quickly while avoiding writes. They still need correct RBAC for the Lease resource, and they still need logs that make leadership state clear during operations, because a healthy standby can otherwise look idle or broken.

---

## Patterns & Anti-Patterns

The best client-go controllers look conservative from the outside because they treat every reconciliation as a repair attempt rather than as a reaction to a single event. They read from caches, write only when actual state differs from desired state, and expose progress through status, Events, and logs. The anti-patterns usually appear when controller code borrows habits from request-response services, such as doing heavy work in handlers or assuming the process will remember what it just did.

| Pattern | When to Use | Why It Works |
|---------|-------------|--------------|
| Enqueue keys, not objects | Use this for nearly every Informer event handler | Keys deduplicate naturally and force workers to read current cache state before acting |
| Watch owned resources | Use this when the parent owns Deployments, Services, Jobs, ConfigMaps, or Secrets | Child drift becomes another trigger for parent reconciliation instead of hidden state |
| Patch status separately | Use this when the CRD has a status subresource | Spec writers and status writers avoid fighting over the same object update path |
| Record Kubernetes Events for user-actionable transitions | Use this for creates, updates, permanent validation failures, and repeated transient failures | Users can debug the resource with `kubectl describe` without reading controller logs first |

| Anti-Pattern | What Goes Wrong | Better Alternative |
|--------------|-----------------|--------------------|
| Processing events directly in handlers | The Informer path blocks, cache updates lag, and watch backpressure grows | Add the namespace/name key to the queue and let workers reconcile |
| Comparing events instead of states | Missed events during restart can leave children stale forever | Compare desired parent state with actual child resources every time |
| Retrying all errors forever | Invalid specs become poison-pill queue items and logs hide useful failures | Classify errors, rate-limit transient failures, and surface permanent failures in status |
| Direct API reads in hot paths | Large clusters create unnecessary API server load and uneven latency | Prefer Listers backed by shared Informer caches for observed state |

These patterns also create a scaling boundary. Informers and Listers make reads cheap after cache synchronization, while the workqueue gives you backpressure and retry control for writes. If your controller needs to call an external system, treat that call like any other unreliable dependency: make it idempotent, bound retries, and avoid doing it inside the Informer callback.

## Decision Framework

Use this decision framework when you are choosing how to structure a client-go controller or diagnose one that is already failing. The main question is not whether you can make the controller react faster; the main question is whether each reaction is based on a complete enough view of current state to be safe. Faster broken reconciliation only damages the cluster sooner.

Start with a changed object key, then decide whether it is a primary `WebApp` or an owned child that must be mapped back to a parent. After that, verify caches are synced before reading desired and actual state from Listers. If the actual state already matches, update status if needed and forget the key. If action is required, create, update, delete, or patch the child resource, then classify any failure as retryable or permanent before deciding whether to rate-limit the key or surface a user-facing condition.

| Decision | Prefer This | Avoid This |
|----------|-------------|------------|
| Parent object access | Read from the Informer cache during reconciliation | Fetch from the API server for every queue item |
| Child resource ownership | Set controller owner references on created children | Depend on naming conventions alone for cleanup |
| Drift detection | Watch secondary resources and enqueue the parent | Wait for the parent spec to change before repairing children |
| Retry strategy | Use typed rate-limiting queues with bounded poison-pill handling | Requeue immediately in a tight loop |
| High availability | Add Lease-based leader election and keep reconcile idempotent | Assume one replica means no process or node failure |

Which approach would you choose here and why: if a user manually edits the generated Service to change its port, should the controller patch it back immediately, leave it alone, or report a conflict in status? Answering that question forces you to define whether the Service port is part of the managed desired state, whether users are allowed to customize children, and how the controller communicates ownership boundaries.

A useful rule is to make ownership explicit before you write reconciliation code. If the `WebApp` owns the Deployment image, replica count, labels, selector, and Service port, then the controller should repair drift in those fields and users should edit the parent instead of the children. If some child fields are intentionally user-managed, the controller should avoid overwriting them and should document that boundary in the API. Ambiguous ownership creates surprising controllers: one field is silently repaired, another is ignored, and a third fails only during upgrades.

The framework also helps you decide when client-go from scratch is the right learning or production choice. Use direct client-go when you need to understand the mechanics, build a very small specialized controller, or debug behavior hidden by a higher-level framework. Prefer controller-runtime or Kubebuilder when you need generated typed clients, admission webhooks, conversion webhooks, envtest support, manager wiring, and common controller conventions. The point of this module is not to reject frameworks; it is to make the framework's generated code legible.

Finally, design your controller's feedback surfaces before incidents force the decision. Logs are for controller operators, Events are for people inspecting a resource, and status is for both humans and automation that need durable observed state. A healthy `WebApp` API should let a user answer three questions without reading source code: what did I ask for, what has the controller observed, and what action should I take if convergence is blocked?

## Did You Know?

- **The kube-controller-manager runs many controllers in one binary**, and each follows the same broad observe, queue, reconcile, and retry pattern you are practicing here. The exact set changes across Kubernetes releases, but the architectural idea is stable: specialized loops continuously converge different resource relationships.

- **The Kubernetes watch protocol is paired with LIST for correctness**, so controllers do not need a perfect memory of every historical event. On startup or relist, the Informer establishes current state, then watch updates keep the local cache fresh from that resource version forward.

- **The coordination.k8s.io `Lease` API became the standard lightweight primitive for leader election**, replacing older patterns that used heavier resources for the same coordination job. A Lease is small, fast to update, and easy for controllers to renew on a short cadence.

- **Status subresources deliberately separate desired state from observed state**, which is why a controller can patch `.status.readyReplicas` without overwriting a user's `.spec.replicas`. That separation is one of the cleanest signs that a custom resource has matured from a stored schema into a real Kubernetes API.

---

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|----------------|---------------|
| Not setting OwnerReferences | The controller creates children successfully, so cleanup is easy to forget until deletion testing | Always set a controller owner reference on generated Deployments and Services |
| No rate limiting on queue | Early demos often requeue immediately because it looks simpler than classifying errors | Use a typed rate-limiting queue and call `Forget` after successful reconciliation |
| Single worker thread forever | The first implementation works in a tiny lab and never gets revisited for production load | Start with a small worker count, measure queue depth and latency, then tune deliberately |
| Not handling tombstones | Delete handlers are tested only with ordinary objects and miss `DeletedFinalStateUnknown` cases | Type-check delete events and unwrap tombstones before reading owner references |
| Hardcoded namespace | Local examples use one namespace, then the controller is deployed cluster-wide later | Parse namespace from the queue key and pass it through every lister and client call |
| No graceful shutdown | The process is treated like a script instead of a Kubernetes workload | Use signal handling, context cancellation, queue shutdown, and worker exit checks |
| Ignoring `IsNotFound` errors | Deleted resources look like failures when reconciliation logic expects every key to resolve | Treat not-found as successful convergence for deleted parents or children |

---

## Quiz

<details>
<summary>Scenario: Your controller has been down for ten minutes due to a node failure. During this time, users created many `WebApp` resources and deleted several others. When your controller restarts, it does not receive the historical stream of `ADDED` and `DELETED` events. How does it still manage to converge the cluster to the correct state?</summary>

Kubernetes controllers use level-triggered reconciliation rather than edge-triggered logic, meaning they react to the current state difference rather than individual change events. When the controller restarts, its Informers perform a LIST operation to populate the local cache with the current state of all `WebApp` resources. The controller then compares this desired state against the actual state of existing Deployments and Services. Because it does not rely on historical event replays, it self-heals and processes the net result of all changes that occurred during downtime.
</details>

<details>
<summary>Scenario: A user runs a script that patches the same `WebApp` resource many times in a few seconds to update annotations. Your controller's Informer receives many `MODIFIED` events. Why should the controller avoid reconciling every intermediate object version?</summary>

Controllers enqueue string keys such as `namespace/name` rather than passing full resource objects directly to the workqueue. The workqueue deduplicates identical keys that are added before a worker processes them, which reduces unnecessary work during bursts. By the time a worker dequeues the key and fetches the object from the Informer's local cache, it reads the latest version of the resource. This makes reconciliation focus on current state rather than noisy intermediate transitions.
</details>

<details>
<summary>Scenario: You decommission a `WebApp` named `frontend-app` with `kubectl delete webapp frontend-app`. The controller's `syncHandler` notices the deletion, but the code does not explicitly delete the associated Deployment and Service. How do the child resources get cleaned up?</summary>

The child resources are cleaned up by the Kubernetes garbage collector, not by custom deletion code in this controller. When the controller initially created the Deployment and Service, it attached an `OwnerReference` pointing back to the parent `WebApp` resource. When the API server processes deletion of the `WebApp`, the garbage collector detects those references and initiates cascading deletion of dependents. This mechanism gives reliable cleanup without requiring finalizers for this simple parent-child relationship.
</details>

<details>
<summary>Scenario: You remove `cache.WaitForCacheSync` from `Run` to speed startup. On restart, workers immediately process `WebApp` keys, and the controller starts creating Deployments that already exist. Why did this happen?</summary>

Without waiting for cache synchronization, workers begin the Analyze phase while local Informer caches are empty or partially populated. When `syncHandler` asks the `deploymentLister` if a Deployment exists, the cache can incorrectly return not-found because it has not finished listing state from the API server. The controller interprets that missing cache entry as missing actual state and issues a Create call. `WaitForCacheSync` protects the controller from acting on a partial worldview.
</details>

<details>
<summary>Scenario: Your controller tries to create a Deployment for a `WebApp`, but the API server rejects the request because an admission webhook times out. The `syncHandler` returns an error. How should the workqueue retry this without overwhelming the API server?</summary>

When `syncHandler` returns a retryable error, the worker should call `AddRateLimited` to place the key back into the workqueue under backoff. The rate limiter delays the next attempt for that key and prevents a tight loop from hammering the API server during a transient outage. If failures continue past the configured retry budget, the controller should forget or classify the key and expose enough status or Events for operators to see the problem. The important behavior is bounded retry with useful feedback, not infinite immediate reprocessing.
</details>

<details>
<summary>Scenario: An administrator runs `kubectl scale deployment my-webapp --replicas=0`, overriding the Deployment owned by a `WebApp` whose spec asks for three replicas. The Deployment soon scales back up. How did the controller detect and repair this drift?</summary>

The controller watches secondary resources such as Deployments and Services in addition to the primary `WebApp` resource. When the administrator scaled the Deployment, the API server emitted a modified event for that Deployment, and the Deployment Informer delivered it to the controller. The event handler examined the Deployment's owner reference, identified the parent `WebApp`, and enqueued the parent key. The next reconciliation compared desired replicas with actual replicas and updated the Deployment back to the managed state.
</details>

<details>
<summary>Scenario: A worker successfully reconciles a `WebApp` and calls `queue.Done(key)` but forgets `queue.Forget(key)`. Later, the same key fails once due to a conflict and receives a surprisingly long retry delay. What caused the delay?</summary>

`queue.Done(key)` signals that the worker has finished processing the item, but it does not clear the rate limiter's failure history for that key. `queue.Forget(key)` is responsible for resetting the backoff state after success. If a successful reconciliation omits `Forget`, the rate limiter can remember previous failures and apply a larger delay to a later unrelated failure. Controllers should call `Forget` after successful reconciliation so new failures start with the intended initial backoff.
</details>

---

## Hands-On Exercise

**Task**: Build, deploy, and test a complete custom controller that watches WebApp CRs and creates Deployments and Services.

Exercise scenario: you are preparing a small platform API for application teams that should create a Deployment and Service from a single `WebApp` resource. The goal is not to ship this exact controller unchanged into production; the goal is to prove that you can wire Informers, a workqueue, reconciliation, owner references, status updates, and drift repair without relying on a framework. Keep a terminal open for controller logs while you run the `kubectl` checks, because the fastest way to learn the loop is to watch a key move from event to queue to action.

Use this setup block to create a disposable kind cluster and install the simplified `WebApp` CRD that the controller watches. The CRD includes a status subresource and printer columns so you can see the controller's observed state directly from `kubectl get`.
```bash
# Create a cluster
kind create cluster --name controller-lab

# Apply the WebApp CRD from Module 1.2
# (use the simplified version below)
cat << 'EOF' | kubectl apply -f -
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: webapps.apps.kubedojo.io
spec:
  group: apps.kubedojo.io
  names:
    kind: WebApp
    listKind: WebAppList
    plural: webapps
    singular: webapp
    shortNames: ["wa"]
  scope: Namespaced
  versions:
  - name: v1beta1
    served: true
    storage: true
    subresources:
      status: {}
    additionalPrinterColumns:
    - name: Image
      type: string
      jsonPath: .spec.image
    - name: Replicas
      type: integer
      jsonPath: .spec.replicas
    - name: Ready
      type: integer
      jsonPath: .status.readyReplicas
    - name: Phase
      type: string
      jsonPath: .status.phase
    - name: Age
      type: date
      jsonPath: .metadata.creationTimestamp
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            required: ["image"]
            properties:
              image:
                type: string
              replicas:
                type: integer
                minimum: 1
                maximum: 50
                default: 2
              port:
                type: integer
                minimum: 1
                maximum: 65535
                default: 8080
          status:
            type: object
            properties:
              readyReplicas:
                type: integer
              phase:
                type: string
EOF
```

Work through the following six tasks in order, keeping the controller process visible while you apply resources from a second terminal. Each task adds one layer of evidence: compilation, cache synchronization, parent observation, child creation, drift repair, and garbage-collected cleanup.

1. **Create the project and dependencies**. This task gives you a clean Go module and downloads the Kubernetes libraries used by the preserved controller code. Keep the project outside the KubeDojo repository so generated `go.sum` changes and local binaries never appear in this documentation worktree.
```bash
mkdir -p ~/extending-k8s/webapp-controller && cd ~/extending-k8s/webapp-controller
go mod init github.com/example/webapp-controller
go get k8s.io/client-go@latest k8s.io/apimachinery@latest k8s.io/api@latest k8s.io/klog/v2@latest
```

2. **Create the source files** from the code in Parts 3.2, 3.3, and 3.4. Put the type definitions, controller implementation, and main entry point in separate files so compiler errors point to the same conceptual boundaries used in the lesson.

3. **Build and run the controller locally**. Start it with verbose logging and leave the process running so it can watch the kind cluster through your kubeconfig. Before you create a `WebApp`, look for cache-sync log lines; if caches do not sync, reconciliation should not begin.
```bash
go build -o webapp-controller .
./webapp-controller -v=2
```

4. **Create a `WebApp` from another terminal**. This is the first complete Observe-Analyze-Act pass: the parent object appears, the key is enqueued, the controller creates child resources, and status begins to reflect Deployment readiness.
```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: apps.kubedojo.io/v1beta1
kind: WebApp
metadata:
  name: demo-app
spec:
  image: nginx:1.27
  replicas: 3
  port: 80
EOF
```

5. **Verify creation, ownership, Events, and self-healing**. Run the checks before and after deleting the generated Deployment so you can see both parent-triggered creation and child-triggered drift repair. The important evidence is not only that resources exist, but that the Deployment is controlled by the `WebApp` and that controller Events describe the actions.
```bash
# Check WebApp status
kubectl get webapp demo-app

# Check created Deployment
kubectl get deployment demo-app
kubectl describe deployment demo-app | grep "Controlled By"

# Check created Service
kubectl get svc demo-app

# Check events
kubectl get events --sort-by=.lastTimestamp | grep webapp
```

```bash
# Delete the Deployment — controller should recreate it
kubectl delete deployment demo-app
sleep 5
kubectl get deployment demo-app

# Scale the WebApp
kubectl patch webapp demo-app --type=merge -p '{"spec":{"replicas":5}}'
sleep 5
kubectl get deployment demo-app
```

6. **Test deletion cascade and cleanup**. Deleting the parent should remove the child Deployment and Service through Kubernetes garbage collection because the controller set owner references when it created them. After the check, delete the kind cluster so the lab leaves no local workloads behind.
```bash
kubectl delete webapp demo-app
sleep 5
kubectl get deployment demo-app     # Should be gone (GC'd via OwnerRef)
kubectl get svc demo-app             # Should be gone
```

8. **Cleanup**:
```bash
kind delete cluster --name controller-lab
```

Use this checklist as the lab's completion contract rather than as a loose suggestion. If one item fails, map it back to the controller architecture: cache sync, queue processing, owner references, child watches, status patching, or shutdown behavior.
- [ ] Controller compiles and starts without errors
- [ ] Cache sync completes (check logs)
- [ ] Creating a WebApp triggers Deployment + Service creation
- [ ] Deployment has correct OwnerReference pointing to WebApp
- [ ] Deleting the Deployment triggers controller to recreate it
- [ ] Updating WebApp replicas updates the Deployment
- [ ] Deleting the WebApp cascades deletion to Deployment + Service
- [ ] Kubernetes Events are recorded for create/update actions
- [ ] Ctrl+C triggers graceful shutdown

<details>
<summary>Solution notes for the lab</summary>

If the controller starts but no child resources appear, check cache sync first, then confirm the CRD group, version, and plural match the `webappGVR` in the controller. If the Deployment exists but deletion of the `WebApp` leaves it behind, inspect the Deployment owner reference and verify the UID points to the parent, not only a matching name. If self-healing does not happen after deleting or scaling the Deployment, the secondary Deployment Informer is probably not enqueueing the parent key from the owner reference.
</details>

---

## Sources

- https://kubernetes.io/docs/concepts/architecture/controller/
- https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/
- https://kubernetes.io/docs/tasks/extend-kubernetes/custom-resources/custom-resource-definitions/
- https://kubernetes.io/docs/concepts/overview/working-with-objects/owners-dependents/
- https://kubernetes.io/docs/concepts/architecture/garbage-collection/
- https://kubernetes.io/docs/reference/using-api/api-concepts/
- https://kubernetes.io/docs/reference/using-api/server-side-apply/
- https://kubernetes.io/docs/reference/kubernetes-api/cluster-resources/lease-v1/
- https://pkg.go.dev/k8s.io/client-go/tools/cache
- https://pkg.go.dev/k8s.io/client-go/util/workqueue
- https://pkg.go.dev/k8s.io/client-go/tools/leaderelection
- https://pkg.go.dev/k8s.io/client-go/tools/record

---

## Next Module

[Module 1.4: The Operator Pattern & Kubebuilder](../module-1.4-kubebuilder/) - Use the Kubebuilder framework to build operators with less boilerplate and more structure.

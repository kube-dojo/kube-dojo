# Module 1.3: Building Controllers with client-go

> **Complexity**: `[COMPLEX]` - Full controller implementation from scratch
>
> **Time to Complete**: 5 hours
>
> **Prerequisites**: Module 1.1 (API Deep Dive), Module 1.2 (CRDs Advanced), intermediate Go programming

---

## Why This Module Matters

A Kubernetes controller is the engine that turns **declarative intent** into **running reality**. When you create a Deployment, it is a controller (the Deployment controller) that creates the ReplicaSet. When you create a Service, it is a controller (the Endpoints controller) that populates the Endpoints. Without controllers, Kubernetes is just a database of YAML documents.

In this module you will build a complete controller from scratch using only client-go -- no frameworks, no scaffolding, no magic. You will implement every piece yourself: the Informer that watches resources, the Workqueue that buffers events, the reconciliation loop that creates child resources, and the error handling that makes it production-ready. This foundational knowledge is what separates someone who *uses* operators from someone who *builds* them.

> **The Thermostat Analogy**
>
> A Kubernetes controller works exactly like a thermostat. You set the desired temperature (spec). The thermostat continuously observes the current temperature (status). If there is a difference, it acts -- turning on the heater or the AC. It does not remember what it did last time; it just compares desired vs. actual and takes the minimum action to converge. This is the **Observe-Analyze-Act** loop, and every controller follows it.

---

## What You'll Learn

By the end of this module, you will be able to:
- Implement the full controller pattern (Observe, Analyze, Act)
- Use SharedIndexInformer with DeltaFIFO
- Build a rate-limited Workqueue with retries
- Write idempotent reconciliation logic
- Handle controller shutdown gracefully
- Implement leader election for HA deployments
- Create child Kubernetes resources (Deployments, Services) from a CRD

---

## Did You Know?

- **The Kubernetes controller-manager runs 37 controllers** in a single binary. Each one follows the exact same pattern you will learn here. The Deployment controller, the Job controller, the Namespace controller -- all use SharedInformers, Workqueues, and the reconcile loop.

- **"Level-triggered" beats "edge-triggered"**: Kubernetes controllers do not react to individual events. They react to the *current state*. If your controller crashes and misses 50 events, it does not matter -- on restart, it sees the current state and reconciles. This is why controllers are so resilient.

- **The average production controller handles 10,000+ resources** with a single Informer cache consuming roughly 100MB of memory. The Watch protocol is remarkably efficient -- the API Server only sends deltas, and the Informer deduplicates them.

---

## Part 1: The Controller Pattern

### 1.1 Observe-Analyze-Act

Every Kubernetes controller follows this three-step loop:

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

This distinction is fundamental:

| Approach | Reacts To | Problem |
|----------|----------|---------|
| **Edge-triggered** | Individual events (ADDED, MODIFIED, DELETED) | If you miss an event, state diverges forever |
| **Level-triggered** | Current state difference (desired vs actual) | Self-healing: always converges regardless of missed events |

Kubernetes controllers are **level-triggered**. Your reconcile function should never ask "what event happened?" It should ask "what is the current desired state, what is the current actual state, and what do I need to do to make them match?"

### 1.3 Idempotency

Every reconciliation must be **idempotent**: running it 1 time or 100 times produces the same result. This means:
- Use `Create` with conflict detection, not blind creates
- Use `Update` with resource version checks
- Check if a resource already exists before creating it
- Make decisions based on current state, not event history

---

## Part 2: Controller Architecture

### 2.1 Component Overview

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

### 2.2 Watching Owned Resources

When your controller creates a Deployment, you also need to know when that Deployment changes (e.g., it becomes ready, or someone deletes it). You watch Deployments too, but when an event fires, you look up the **owner reference** to find the parent WebApp, and enqueue *that* key.

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

---

## Part 3: The Complete Controller

### 3.1 Project Structure

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

### 3.2 CRD Types (Simplified)

Since we are not using code generation, we will work with unstructured objects. But first, let us define our Go types for clarity:

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

```go
// controller.go
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

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

```go
// main.go
package main

import (
	"context"
	"fmt"
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

> **Note**: The `main.go` file references `corev1` -- you will need to add `corev1 "k8s.io/api/core/v1"` to the imports. Your IDE or `goimports` will handle this.

---

## Part 4: Rate Limiting and Retry Strategies

### 4.1 Built-in Rate Limiters

client-go provides several rate limiters:

```go
// Default: combines exponential backoff with a bucket rate limiter
queue := workqueue.NewTypedRateLimitingQueue(
    workqueue.DefaultTypedControllerRateLimiter[string](),
)

// Custom: exponential backoff (5ms base, 1000s max)
queue := workqueue.NewTypedRateLimitingQueue(
    workqueue.NewTypedItemExponentialFailureRateLimiter[string](
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
        workqueue.NewTypedItemExponentialFailureRateLimiter[string](
            5*time.Millisecond, 60*time.Second),
        &workqueue.TypedBucketRateLimiter[string]{
            Limiter: rate.NewLimiter(rate.Limit(10), 100)},
    ),
)
```

### 4.2 Retry Best Practices

| Practice | Why |
|----------|-----|
| Cap max retries (e.g., 5-15) | Prevents infinite retry loops |
| Use exponential backoff | Prevents thundering herd on transient failures |
| Log retries with count | Enables monitoring and alerting |
| Forget on success | Resets backoff for next failure |
| Distinguish retryable vs fatal errors | Do not retry validation errors |

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

---

## Part 5: Graceful Shutdown

### 5.1 Shutdown Sequence

A controller must shut down cleanly to avoid data loss and duplicate processing:

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

The graceful shutdown is already built into our controller via the context cancellation pattern. The key points are:

1. `ctx.Done()` stops the informers
2. `defer c.queue.ShutDown()` in `Run()` drains the queue
3. Workers check `shutdown` from `queue.Get()` and exit
4. `defer cancel()` in `main()` ensures cleanup on any exit path

---

## Part 6: Leader Election

### 6.1 Why Leader Election?

When you run multiple replicas of your controller for high availability, only **one** should be actively reconciling at a time. Leader election uses a Kubernetes Lease resource to coordinate:

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

### 6.2 Leader Election Parameters

| Parameter | Typical Value | Description |
|-----------|--------------|-------------|
| LeaseDuration | 15s | How long a non-leader waits before trying to acquire |
| RenewDeadline | 10s | How long the leader has to renew before losing the lease |
| RetryPeriod | 2s | How often to retry acquiring the lease |
| ReleaseOnCancel | true | Release lease on graceful shutdown |

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Processing events directly in handlers | Blocks the informer, dropped events | Always enqueue keys; process in workers |
| Not setting OwnerReferences | Orphaned resources on CRD deletion | Always set controller owner reference |
| Comparing events instead of states | Misses events on restart | Compare desired vs actual state only |
| No rate limiting on queue | Overwhelms API Server on failure loops | Use `NewRateLimitingQueue` |
| Single worker thread | Slow reconciliation under load | Use 2-4 workers for production |
| Not handling tombstones | Panic on `DeletedFinalStateUnknown` | Type-check and unwrap tombstones |
| Hardcoded namespace | Controller only works in one namespace | Use namespace from object key |
| No graceful shutdown | Lost in-flight work, duplicate processing | Handle SIGTERM, drain queue |
| Ignoring `IsNotFound` errors | Retrying forever for deleted resources | Check error type, skip not-found |
| Direct API calls in hot paths | High API Server load | Use Listers from informer cache |

---

## Quiz

1. **What is the difference between "level-triggered" and "edge-triggered" reconciliation?**
   <details>
   <summary>Answer</summary>
   Edge-triggered reacts to individual change events ("a pod was added"). Level-triggered reacts to the current state difference ("there should be 3 replicas but only 2 exist"). Kubernetes controllers use level-triggered reconciliation because it is self-healing: if the controller crashes and misses events, it will still converge to the correct state on the next reconciliation because it compares desired vs. actual state, not event history.
   </details>

2. **Why do controllers enqueue string keys instead of passing objects directly to workers?**
   <details>
   <summary>Answer</summary>
   Three reasons: (a) Deduplication -- if the same object changes 10 times before processing, only the latest state matters; (b) Rate limiting works on keys, not objects; (c) The worker reads the latest state from the cache at processing time, which may be newer than the state at enqueue time. This ensures the controller always acts on the most current information.
   </details>

3. **What happens when a WebApp CR is deleted if we have set OwnerReferences on the Deployment and Service?**
   <details>
   <summary>Answer</summary>
   Kubernetes garbage collection automatically deletes all resources that have an OwnerReference pointing to the deleted WebApp. This is called "cascading deletion." The controller does not need to explicitly delete the Deployment and Service -- the garbage collector handles it. The default policy is "Background" deletion, where the owner is deleted immediately and dependents are cleaned up asynchronously.
   </details>

4. **Explain why `WaitForCacheSync` is critical before processing items.**
   <details>
   <summary>Answer</summary>
   Without waiting for cache sync, the informer's local cache is incomplete. The controller would read partial state from the Lister, conclude that resources are missing, and try to create duplicates. For example, if the Deployment cache has not synced yet, the controller would see no Deployment for a WebApp and create one, even though one already exists. This causes conflicts and wasted API calls.
   </details>

5. **A controller has 3 workers and processes a key that fails. What happens to that key?**
   <details>
   <summary>Answer</summary>
   The key is re-enqueued via `AddRateLimited`, which applies exponential backoff. The default rate limiter starts at 5ms and doubles on each failure up to a maximum of 1000 seconds. Any available worker (not necessarily the same one) will pick up the key after the backoff period. If the key fails more than `maxRetries` times (5 in our implementation), it is dropped with `Forget` and the error is logged.
   </details>

6. **Why does the controller watch Deployments and Services in addition to WebApps?**
   <details>
   <summary>Answer</summary>
   The controller must react when owned resources change. If someone manually deletes the Deployment that the controller created, the controller needs to detect this and recreate it. By watching Deployments and Services and mapping changes back to the parent WebApp (via OwnerReferences), the controller can reconcile the parent whenever its children change. Without this, the controller would only react to WebApp spec changes, not to drift in the actual state.
   </details>

7. **What is the purpose of `queue.Forget(key)` vs `queue.Done(key)`?**
   <details>
   <summary>Answer</summary>
   `Done(key)` tells the queue that processing of this key is complete and it can be dequeued again (it is a concurrency mechanism). `Forget(key)` resets the rate limiter for this key, clearing the backoff counter. You always call `Done` (usually via defer). You call `Forget` only on success -- when the item should not carry any failure history forward. If you call `AddRateLimited` without `Forget`, the backoff increases. If you call `Forget` first, then `AddRateLimited`, the backoff resets.
   </details>

---

## Hands-On Exercise

**Task**: Build, deploy, and test a complete custom controller that watches WebApp CRs and creates Deployments and Services.

**Setup**:
```bash
# Create a cluster
kind create cluster --name controller-lab

# Apply the WebApp CRD from Module 1.2
# (use the simplified version below)
cat << 'EOF' | k apply -f -
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

**Steps**:

1. **Create the project**:
```bash
mkdir -p ~/extending-k8s/webapp-controller && cd ~/extending-k8s/webapp-controller
go mod init github.com/example/webapp-controller
go get k8s.io/client-go@latest k8s.io/apimachinery@latest k8s.io/api@latest k8s.io/klog/v2@latest
```

2. **Create the source files** from the code in Parts 3.2, 3.3, and 3.4

3. **Build and run**:
```bash
go build -o webapp-controller .
./webapp-controller -v=2
```

4. **In another terminal, create a WebApp**:
```bash
cat << 'EOF' | k apply -f -
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

5. **Verify the controller creates resources**:
```bash
# Check WebApp status
k get webapp demo-app

# Check created Deployment
k get deployment demo-app
k describe deployment demo-app | grep "Controlled By"

# Check created Service
k get svc demo-app

# Check events
k get events --sort-by=.lastTimestamp | grep webapp
```

6. **Test self-healing**:
```bash
# Delete the Deployment — controller should recreate it
k delete deployment demo-app
sleep 5
k get deployment demo-app

# Scale the WebApp
k patch webapp demo-app --type=merge -p '{"spec":{"replicas":5}}'
sleep 5
k get deployment demo-app
```

7. **Test deletion cascade**:
```bash
k delete webapp demo-app
sleep 5
k get deployment demo-app     # Should be gone (GC'd via OwnerRef)
k get svc demo-app             # Should be gone
```

8. **Cleanup**:
```bash
kind delete cluster --name controller-lab
```

**Success Criteria**:
- [ ] Controller compiles and starts without errors
- [ ] Cache sync completes (check logs)
- [ ] Creating a WebApp triggers Deployment + Service creation
- [ ] Deployment has correct OwnerReference pointing to WebApp
- [ ] Deleting the Deployment triggers controller to recreate it
- [ ] Updating WebApp replicas updates the Deployment
- [ ] Deleting the WebApp cascades deletion to Deployment + Service
- [ ] Kubernetes Events are recorded for create/update actions
- [ ] Ctrl+C triggers graceful shutdown

---

## Next Module

[Module 1.4: The Operator Pattern & Kubebuilder](module-1.4-kubebuilder.md) - Use the Kubebuilder framework to build operators with less boilerplate and more structure.

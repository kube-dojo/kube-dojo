---
title: "Module 1.5: Advanced Operator Development"
slug: k8s/extending/module-1.5-advanced-operators
sidebar:
  order: 6
---
> **Complexity**: `[COMPLEX]` - Production-grade operator patterns
>
> **Time to Complete**: 5 hours
>
> **Prerequisites**: Module 1.4 (Kubebuilder), Go testing fundamentals

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Implement** finalizers that cleanly remove external resources (DNS records, cloud load balancers) before a custom resource is deleted
2. **Design** structured status conditions following the Kubernetes API conventions so users can diagnose issues with `kubectl describe`
3. **Configure** leader election and multi-replica deployments so your operator survives node failures without split-brain
4. **Construct** envtest integration tests that validate the full reconciliation lifecycle including finalizer cleanup

---

## Why This Module Matters

The operator you built in Module 1.4 works, but it is not production-ready. What happens when a user deletes a WebApp that has provisioned external resources (a DNS record, a database, a cloud load balancer)? Without **finalizers**, those resources become orphans. How does a user know *why* their WebApp is not ready? Without **status conditions**, they have to read controller logs. How does an SRE debug a failing reconciliation at 3 AM? Without **Kubernetes Events**, they are blind.

This module adds the pieces that separate a demo operator from a production operator: finalizers for cleanup, structured status conditions, Kubernetes Events for observability, leader election for high availability, and envtest for comprehensive integration testing. These patterns are used by every serious operator in the CNCF ecosystem -- from Cert-Manager to Crossplane to Cluster API.

> **The Moving-Out Analogy**
>
> Deleting a Kubernetes resource without a finalizer is like moving out of an apartment without cleaning up. You leave, but your furniture, your mail forwarding, and your utility accounts are still there. A finalizer is the "moving-out checklist" -- it tells Kubernetes: "Before you actually delete me, let me clean up my external dependencies first." The resource stays in a `Terminating` state until the controller confirms the cleanup is done.

---

## What You'll Learn

By the end of this module, you will be able to:
- Implement finalizers for external resource cleanup
- Use structured status conditions following Kubernetes conventions
- Emit Kubernetes Events for operational visibility
- Configure leader election for HA deployments
- Watch owned resources and react to changes
- Write comprehensive integration tests with envtest

---

## Did You Know?

- **Finalizers are not just for deletion**: While their primary use is cleanup, finalizers also serve as a "hold" mechanism. Kubernetes will not remove the object from etcd until all finalizers are removed. Some operators use this to prevent accidental deletion of critical resources.

- **The Kubernetes conditions API was formalized in KEP-1623**: Before this, every operator invented its own condition format. Now there is a standard: `metav1.Condition` with Type, Status, Reason, Message, ObservedGeneration, and LastTransitionTime. Using it means your CRD works with standard Kubernetes tooling.

- **envtest spins up a real API Server and etcd**: It is not a mock. Your tests talk to an actual API Server binary. This means your integration tests catch real issues like RBAC problems, validation failures, and race conditions that unit tests would miss.

---

## Part 1: Finalizers

### 1.1 How Finalizers Work

```
User runs: kubectl delete webapp my-app
    │
    ▼
API Server sets deletionTimestamp (object is "terminating")
    │
    ├── Finalizers list is NOT empty?
    │       │
    │       ▼
    │   Object stays in etcd with deletionTimestamp set
    │   Controller sees the deletionTimestamp
    │   Controller performs cleanup
    │   Controller removes its finalizer from the list
    │       │
    │       ├── More finalizers remain? → Wait for other controllers
    │       │
    │       └── No finalizers left? ─────────────┐
    │                                             │
    ├── Finalizers list IS empty? ────────────────┤
    │                                             │
    │                                             ▼
    │                                    Object removed from etcd
    │                                    Garbage collector deletes owned resources
    └─────────────────────────────────────────────────────────────
```

### 1.2 Implementation

> **Stop and think**: If the cleanup logic fails and you return an error, the controller will back off and retry. If you instead removed the finalizer *before* executing the cleanup, what would happen to the external resources if the controller crashed during the cleanup process?

```go
// internal/controller/webapp_controller.go

const webappFinalizer = "apps.kubedojo.io/finalizer"

func (r *WebAppReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
	logger := log.FromContext(ctx)

	// Fetch the WebApp
	webapp := &appsv1beta1.WebApp{}
	if err := r.Get(ctx, req.NamespacedName, webapp); err != nil {
		if errors.IsNotFound(err) {
			return ctrl.Result{}, nil
		}
		return ctrl.Result{}, err
	}

	// ───── Finalizer Logic ─────

	// Check if the object is being deleted
	if !webapp.DeletionTimestamp.IsZero() {
		// Object is being deleted
		if controllerutil.ContainsFinalizer(webapp, webappFinalizer) {
			// Run cleanup logic
			logger.Info("Running finalizer cleanup", "webapp", webapp.Name)

			if err := r.cleanupExternalResources(ctx, webapp); err != nil {
				// If cleanup fails, don't remove the finalizer — retry
				logger.Error(err, "Failed to clean up external resources")
				return ctrl.Result{}, err
			}

			// Cleanup succeeded — remove the finalizer
			controllerutil.RemoveFinalizer(webapp, webappFinalizer)
			if err := r.Update(ctx, webapp); err != nil {
				return ctrl.Result{}, err
			}
			logger.Info("Finalizer removed, object will be deleted")
		}
		// Object is being deleted and our finalizer is gone — nothing to do
		return ctrl.Result{}, nil
	}

	// Object is NOT being deleted — ensure finalizer is present
	if !controllerutil.ContainsFinalizer(webapp, webappFinalizer) {
		controllerutil.AddFinalizer(webapp, webappFinalizer)
		if err := r.Update(ctx, webapp); err != nil {
			return ctrl.Result{}, err
		}
		logger.Info("Added finalizer")
		// Return and let the update trigger a new reconciliation
		return ctrl.Result{}, nil
	}

	// ───── Normal Reconciliation ─────
	// (rest of your reconcile logic from Module 1.4)

	return r.reconcileNormal(ctx, webapp)
}

func (r *WebAppReconciler) cleanupExternalResources(ctx context.Context, webapp *appsv1beta1.WebApp) error {
	logger := log.FromContext(ctx)

	// Example: Clean up external DNS records
	if webapp.Spec.Ingress != nil && webapp.Spec.Ingress.Host != "" {
		logger.Info("Cleaning up DNS record", "host", webapp.Spec.Ingress.Host)
		// In a real operator, call your DNS provider API here
		// if err := dnsClient.DeleteRecord(webapp.Spec.Ingress.Host); err != nil {
		//     return err
		// }
	}

	// Example: Clean up monitoring dashboards
	logger.Info("Cleaning up monitoring resources", "webapp", webapp.Name)
	// if err := monitoringClient.DeleteDashboard(webapp.Name); err != nil {
	//     return err
	// }

	// Example: Clean up external storage
	logger.Info("Cleaning up storage", "webapp", webapp.Name)

	return nil
}
```

### 1.3 Finalizer Best Practices

| Practice | Why |
|----------|-----|
| Use a domain-qualified name | Avoids collisions: `apps.kubedojo.io/finalizer` |
| Check `DeletionTimestamp` first | Always handle deletion before normal reconciliation |
| Return early after adding finalizer | Let the watch trigger a clean re-reconcile |
| Log cleanup actions | Essential for debugging stuck deletions |
| Handle cleanup errors gracefully | Return error to retry, but avoid infinite loops |
| Set a timeout on cleanup | External APIs can hang; use context with timeout |

---

## Part 2: Status Conditions

### 2.1 The Standard Condition Format

Kubernetes defines a standard condition structure in `metav1.Condition`:

```go
type Condition struct {
    // Type of condition (e.g., "Ready", "Available", "Degraded")
    Type string

    // Status: "True", "False", or "Unknown"
    Status ConditionStatus

    // ObservedGeneration: the generation this condition was set for
    ObservedGeneration int64

    // LastTransitionTime: when the status last changed
    LastTransitionTime Time

    // Reason: machine-readable CamelCase reason
    Reason string

    // Message: human-readable description
    Message string
}
```

### 2.2 Condition Types for Our Operator

Define conditions that cover the key states:

```go
const (
	// ConditionTypeReady indicates the WebApp is fully operational.
	ConditionTypeReady = "Ready"

	// ConditionTypeDeploymentReady indicates the Deployment is ready.
	ConditionTypeDeploymentReady = "DeploymentReady"

	// ConditionTypeServiceReady indicates the Service is configured.
	ConditionTypeServiceReady = "ServiceReady"

	// ConditionTypeIngressReady indicates the Ingress is configured.
	ConditionTypeIngressReady = "IngressReady"
)

// Reasons for conditions
const (
	ReasonReconciling      = "Reconciling"
	ReasonAvailable        = "Available"
	ReasonDeploymentFailed = "DeploymentFailed"
	ReasonServiceFailed    = "ServiceFailed"
	ReasonScalingUp        = "ScalingUp"
	ReasonScalingDown      = "ScalingDown"
	ReasonImageUpdating    = "ImageUpdating"
	ReasonCleanupPending   = "CleanupPending"
	ReasonCleanupComplete  = "CleanupComplete"
)
```

### 2.3 Setting Conditions

> **Pause and predict**: We set `ObservedGeneration` to `webapp.Generation`. If a user updates the WebApp spec (incrementing its generation), but the controller hasn't processed it yet, how does this field help the user or a CD pipeline understand the current status?

```go
func (r *WebAppReconciler) updateConditions(ctx context.Context,
	webapp *appsv1beta1.WebApp,
	deployment *appsv1.Deployment) error {

	// Deployment condition
	deploymentCondition := metav1.Condition{
		Type:               ConditionTypeDeploymentReady,
		ObservedGeneration: webapp.Generation,
		LastTransitionTime: metav1.Now(),
	}

	if deployment == nil {
		deploymentCondition.Status = metav1.ConditionFalse
		deploymentCondition.Reason = ReasonReconciling
		deploymentCondition.Message = "Deployment has not been created yet"
	} else if deployment.Status.ReadyReplicas == *deployment.Spec.Replicas {
		deploymentCondition.Status = metav1.ConditionTrue
		deploymentCondition.Reason = ReasonAvailable
		deploymentCondition.Message = fmt.Sprintf(
			"Deployment has %d/%d replicas ready",
			deployment.Status.ReadyReplicas,
			*deployment.Spec.Replicas)
	} else {
		deploymentCondition.Status = metav1.ConditionFalse
		deploymentCondition.Reason = ReasonScalingUp
		deploymentCondition.Message = fmt.Sprintf(
			"Deployment has %d/%d replicas ready, scaling in progress",
			deployment.Status.ReadyReplicas,
			*deployment.Spec.Replicas)
	}

	// Service condition (always true if we got this far)
	serviceCondition := metav1.Condition{
		Type:               ConditionTypeServiceReady,
		Status:             metav1.ConditionTrue,
		ObservedGeneration: webapp.Generation,
		LastTransitionTime: metav1.Now(),
		Reason:             ReasonAvailable,
		Message:            "Service is configured",
	}

	// Overall Ready condition
	readyCondition := metav1.Condition{
		Type:               ConditionTypeReady,
		ObservedGeneration: webapp.Generation,
		LastTransitionTime: metav1.Now(),
	}

	allReady := deploymentCondition.Status == metav1.ConditionTrue &&
		serviceCondition.Status == metav1.ConditionTrue

	if allReady {
		readyCondition.Status = metav1.ConditionTrue
		readyCondition.Reason = ReasonAvailable
		readyCondition.Message = "All components are ready"
		webapp.Status.Phase = "Running"
	} else {
		readyCondition.Status = metav1.ConditionFalse
		readyCondition.Reason = ReasonReconciling
		readyCondition.Message = "One or more components are not ready"
		webapp.Status.Phase = "Deploying"
	}

	// Apply conditions using the standard helper
	meta.SetStatusCondition(&webapp.Status.Conditions, deploymentCondition)
	meta.SetStatusCondition(&webapp.Status.Conditions, serviceCondition)
	meta.SetStatusCondition(&webapp.Status.Conditions, readyCondition)

	webapp.Status.ObservedGeneration = webapp.Generation

	return r.Status().Update(ctx, webapp)
}
```

### 2.4 Reading Conditions

```bash
# View conditions
kubectl get webapp my-app -o jsonpath='{range .status.conditions[*]}{.type}{"\t"}{.status}{"\t"}{.reason}{"\t"}{.message}{"\n"}{end}'

# Example output:
# DeploymentReady   True    Available       Deployment has 3/3 replicas ready
# ServiceReady      True    Available       Service is configured
# Ready             True    Available       All components are ready

# Check if ready using JSONPath
kubectl get webapp my-app -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}'
```

### 2.5 Condition Conventions

| Convention | Rule |
|-----------|------|
| Positive polarity | "Ready" not "NotReady", "Available" not "Unavailable" |
| Reason is CamelCase | `ScalingUp`, not `scaling_up` or `Scaling Up` |
| Message is human-readable | Full sentences, include counts and details |
| ObservedGeneration | Always set to `obj.Generation` |
| LastTransitionTime | Only changes when Status changes, not on every update |
| Unknown status | Use when the controller cannot determine the state |

---

## Part 3: Kubernetes Events

### 3.1 Why Events?

Events are the operational log of your operator visible to users via `kubectl describe` and `kubectl get events`. They answer the question: "What happened and when?"

### 3.2 Setting Up the Event Recorder

In Kubebuilder, add the recorder to your reconciler:

```go
// internal/controller/webapp_controller.go
type WebAppReconciler struct {
	client.Client
	Scheme   *runtime.Scheme
	Recorder record.EventRecorder
}
```

Register it in `cmd/main.go`:

```go
if err = (&controller.WebAppReconciler{
    Client:   mgr.GetClient(),
    Scheme:   mgr.GetScheme(),
    Recorder: mgr.GetEventRecorderFor("webapp-controller"),
}).SetupWithManager(mgr); err != nil {
    os.Exit(1)
}
```

### 3.3 Emitting Events

```go
func (r *WebAppReconciler) reconcileNormal(ctx context.Context,
	webapp *appsv1beta1.WebApp) (ctrl.Result, error) {

	// On Deployment creation
	r.Recorder.Eventf(webapp, corev1.EventTypeNormal,
		"DeploymentCreated",
		"Created Deployment %s with %d replicas",
		webapp.Name, *webapp.Spec.Replicas)

	// On scaling
	r.Recorder.Eventf(webapp, corev1.EventTypeNormal,
		"Scaled",
		"Scaled Deployment from %d to %d replicas",
		oldReplicas, *webapp.Spec.Replicas)

	// On image update
	r.Recorder.Eventf(webapp, corev1.EventTypeNormal,
		"ImageUpdated",
		"Updated container image from %s to %s",
		oldImage, webapp.Spec.Image)

	// On errors
	r.Recorder.Eventf(webapp, corev1.EventTypeWarning,
		"ReconcileError",
		"Failed to create Deployment: %v", err)

	// On cleanup
	r.Recorder.Event(webapp, corev1.EventTypeNormal,
		"CleanupComplete",
		"External resources cleaned up successfully")

	// ...
}
```

### 3.4 Event Types and When to Use Them

| Type | When | Example |
|------|------|---------|
| `EventTypeNormal` | Routine operations | Created Deployment, Scaled, Updated |
| `EventTypeWarning` | Problems that need attention | Failed to create, Retry limit reached |

```bash
# View events for a specific resource
kubectl describe webapp my-app | grep -A 20 "Events:"

# View all events sorted by time
kubectl get events --sort-by=.lastTimestamp --field-selector involvedObject.kind=WebApp
```

---

## Part 4: Leader Election

### 4.1 How Leader Election Works in controller-runtime

> **Stop and think**: If network latency spikes and the leader pod fails to renew its lease within the `RenewDeadline`, the standby pod might take over. What happens to the old leader pod's controllers once it reconnects and realizes it lost the lease?

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Leader Election                                    │
│                                                                     │
│   Pod A (leader)              Pod B (standby)                       │
│   ┌──────────────┐           ┌──────────────┐                      │
│   │ Manager      │           │ Manager      │                      │
│   │              │           │              │                      │
│   │ Controllers: │           │ Controllers: │                      │
│   │ ✓ Running    │           │ ✗ Blocked    │                      │
│   │              │           │              │                      │
│   │ Lease:       │           │ Lease:       │                      │
│   │ HELD ────────┼───────── │ WAITING      │                      │
│   └──────────────┘    │     └──────────────┘                      │
│                       │                                             │
│                       ▼                                             │
│              ┌───────────────────┐                                  │
│              │  Lease Resource   │                                  │
│              │  (in K8s API)     │                                  │
│              │                   │                                  │
│              │  holder: pod-a    │                                  │
│              │  renewTime: now   │                                  │
│              │  leaseDuration: 15s│                                 │
│              └───────────────────┘                                  │
│                                                                     │
│   If Pod A dies:                                                    │
│   1. Pod A stops renewing the lease                                 │
│   2. After leaseDuration (15s), Pod B acquires                      │
│   3. Pod B starts controllers                                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 Enabling Leader Election

In the Manager configuration, leader election is already supported:

```go
mgr, err := ctrl.NewManager(ctrl.GetConfigOrDie(), ctrl.Options{
    // ...
    LeaderElection:          true,
    LeaderElectionID:        "webapp-operator.kubedojo.io",
    LeaderElectionNamespace: "webapp-system",  // Optional: defaults to controller namespace
})
```

Deploy with multiple replicas:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webapp-operator
  namespace: webapp-system
spec:
  replicas: 2          # Two replicas for HA
  selector:
    matchLabels:
      app: webapp-operator
  template:
    spec:
      containers:
      - name: manager
        args:
        - --leader-elect=true
```

### 4.3 Leader Election Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| LeaderElectionID | Required | Unique ID for the lease resource |
| LeaseDuration | 15s | How long a lease lasts |
| RenewDeadline | 10s | How long the leader has to renew |
| RetryPeriod | 2s | How often standby pods check |
| LeaderElectionNamespace | Pod namespace | Where the Lease is created |

---

## Part 5: Watching Owned Resources

### 5.1 Advanced Watch Configuration

Beyond the basic `Owns()` from Module 1.4, you can configure more sophisticated watches:

```go
import (
	"sigs.k8s.io/controller-runtime/pkg/handler"
	"sigs.k8s.io/controller-runtime/pkg/reconcile"
	"sigs.k8s.io/controller-runtime/pkg/source"
)

func (r *WebAppReconciler) SetupWithManager(mgr ctrl.Manager) error {
	return ctrl.NewControllerManagedBy(mgr).
		For(&appsv1beta1.WebApp{}).
		Owns(&appsv1.Deployment{}).
		Owns(&corev1.Service{}).
		// Watch ConfigMaps with a custom mapping function
		Watches(
			&corev1.ConfigMap{},
			handler.EnqueueRequestsFromMapFunc(
				r.findWebAppsForConfigMap,
			),
		).
		// Set maximum concurrent reconciliations
		WithOptions(controller.Options{
			MaxConcurrentReconciles: 3,
		}).
		Named("webapp").
		Complete(r)
}

// findWebAppsForConfigMap maps a ConfigMap to WebApps that reference it.
func (r *WebAppReconciler) findWebAppsForConfigMap(
	ctx context.Context,
	configMap client.Object,
) []reconcile.Request {
	logger := log.FromContext(ctx)

	// List all WebApps
	webappList := &appsv1beta1.WebAppList{}
	if err := r.List(ctx, webappList, client.InNamespace(configMap.GetNamespace())); err != nil {
		logger.Error(err, "Unable to list WebApps")
		return nil
	}

	var requests []reconcile.Request
	for _, webapp := range webappList.Items {
		// Check if this WebApp references the ConfigMap
		for _, env := range webapp.Spec.Env {
			if env.ValueFrom == configMap.GetName() {
				requests = append(requests, reconcile.Request{
					NamespacedName: types.NamespacedName{
						Name:      webapp.Name,
						Namespace: webapp.Namespace,
					},
				})
				break
			}
		}
	}

	return requests
}
```

### 5.2 Watch Predicates

Filter which events trigger reconciliation:

```go
import "sigs.k8s.io/controller-runtime/pkg/predicate"

func (r *WebAppReconciler) SetupWithManager(mgr ctrl.Manager) error {
	return ctrl.NewControllerManagedBy(mgr).
		For(&appsv1beta1.WebApp{},
			builder.WithPredicates(predicate.GenerationChangedPredicate{}),
		).
		Owns(&appsv1.Deployment{}).
		Owns(&corev1.Service{}).
		Named("webapp").
		Complete(r)
}
```

| Predicate | Effect |
|-----------|--------|
| `GenerationChangedPredicate` | Only reconcile when spec changes (ignores status-only updates) |
| `LabelChangedPredicate` | Only when labels change |
| `AnnotationChangedPredicate` | Only when annotations change |
| `ResourceVersionChangedPredicate` | Any change (default behavior) |

You can combine predicates:

```go
builder.WithPredicates(
    predicate.Or(
        predicate.GenerationChangedPredicate{},
        predicate.LabelChangedPredicate{},
    ),
)
```

---

## Part 6: Integration Testing with envtest

### 6.1 What is envtest?

envtest starts a real API Server (and etcd) locally. Your tests talk to a real Kubernetes API, not a mock. This catches:
- RBAC permission issues
- CRD validation failures
- Race conditions between controllers
- Webhook interaction problems

### 6.2 Test Suite Setup

```go
// internal/controller/suite_test.go
package controller

import (
	"context"
	"path/filepath"
	"testing"
	"time"

	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
	"k8s.io/client-go/kubernetes/scheme"
	"k8s.io/client-go/rest"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/envtest"
	logf "sigs.k8s.io/controller-runtime/pkg/log"
	"sigs.k8s.io/controller-runtime/pkg/log/zap"

	appsv1beta1 "github.com/kubedojo/webapp-operator/api/v1beta1"
)

var (
	cfg       *rest.Config
	k8sClient client.Client
	testEnv   *envtest.Environment
	ctx       context.Context
	cancel    context.CancelFunc
)

func TestControllers(t *testing.T) {
	RegisterFailHandler(Fail)
	RunSpecs(t, "Controller Suite")
}

var _ = BeforeSuite(func() {
	logf.SetLogger(zap.New(zap.WriteTo(GinkgoWriter), zap.UseDevMode(true)))

	ctx, cancel = context.WithCancel(context.TODO())

	// Start envtest (real API Server + etcd)
	testEnv = &envtest.Environment{
		CRDDirectoryPaths:     []string{filepath.Join("..", "..", "config", "crd", "bases")},
		ErrorIfCRDPathMissing: true,
	}

	var err error
	cfg, err = testEnv.Start()
	Expect(err).NotTo(HaveOccurred())
	Expect(cfg).NotTo(BeNil())

	// Register our types
	err = appsv1beta1.AddToScheme(scheme.Scheme)
	Expect(err).NotTo(HaveOccurred())

	// Create a client
	k8sClient, err = client.New(cfg, client.Options{Scheme: scheme.Scheme})
	Expect(err).NotTo(HaveOccurred())
	Expect(k8sClient).NotTo(BeNil())

	// Start the controller manager
	mgr, err := ctrl.NewManager(cfg, ctrl.Options{
		Scheme: scheme.Scheme,
	})
	Expect(err).NotTo(HaveOccurred())

	err = (&WebAppReconciler{
		Client:   mgr.GetClient(),
		Scheme:   mgr.GetScheme(),
		Recorder: mgr.GetEventRecorderFor("webapp-controller"),
	}).SetupWithManager(mgr)
	Expect(err).NotTo(HaveOccurred())

	// Run the manager in a goroutine
	go func() {
		defer GinkgoRecover()
		err = mgr.Start(ctx)
		Expect(err).NotTo(HaveOccurred())
	}()
})

var _ = AfterSuite(func() {
	cancel()
	err := testEnv.Stop()
	Expect(err).NotTo(HaveOccurred())
})
```

### 6.3 Writing Tests

```go
// internal/controller/webapp_controller_test.go
package controller

import (
	"time"

	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/types"

	appsv1beta1 "github.com/kubedojo/webapp-operator/api/v1beta1"
)

var _ = Describe("WebApp Controller", func() {
	const (
		timeout  = 30 * time.Second
		interval = 250 * time.Millisecond
	)

	Context("When creating a WebApp", func() {
		It("should create a Deployment and Service", func() {
			webappName := "test-create"
			namespace := "default"
			replicas := int32(3)

			// Create the WebApp
			webapp := &appsv1beta1.WebApp{
				ObjectMeta: metav1.ObjectMeta{
					Name:      webappName,
					Namespace: namespace,
				},
				Spec: appsv1beta1.WebAppSpec{
					Image:    "nginx:1.27",
					Replicas: &replicas,
					Port:     80,
				},
			}
			Expect(k8sClient.Create(ctx, webapp)).To(Succeed())

			// Verify Deployment is created
			deploymentKey := types.NamespacedName{
				Name:      webappName,
				Namespace: namespace,
			}
			deployment := &appsv1.Deployment{}
			Eventually(func() error {
				return k8sClient.Get(ctx, deploymentKey, deployment)
			}, timeout, interval).Should(Succeed())

			Expect(*deployment.Spec.Replicas).To(Equal(int32(3)))
			Expect(deployment.Spec.Template.Spec.Containers[0].Image).To(Equal("nginx:1.27"))

			// Verify OwnerReference is set
			Expect(deployment.OwnerReferences).To(HaveLen(1))
			Expect(deployment.OwnerReferences[0].Kind).To(Equal("WebApp"))
			Expect(deployment.OwnerReferences[0].Name).To(Equal(webappName))

			// Verify Service is created
			serviceKey := types.NamespacedName{
				Name:      webappName,
				Namespace: namespace,
			}
			service := &corev1.Service{}
			Eventually(func() error {
				return k8sClient.Get(ctx, serviceKey, service)
			}, timeout, interval).Should(Succeed())

			Expect(service.Spec.Ports[0].Port).To(Equal(int32(80)))
		})
	})

	Context("When updating a WebApp", func() {
		It("should update the Deployment replicas", func() {
			webappName := "test-update"
			namespace := "default"
			replicas := int32(2)

			// Create initial WebApp
			webapp := &appsv1beta1.WebApp{
				ObjectMeta: metav1.ObjectMeta{
					Name:      webappName,
					Namespace: namespace,
				},
				Spec: appsv1beta1.WebAppSpec{
					Image:    "nginx:1.27",
					Replicas: &replicas,
					Port:     80,
				},
			}
			Expect(k8sClient.Create(ctx, webapp)).To(Succeed())

			// Wait for Deployment
			deploymentKey := types.NamespacedName{
				Name:      webappName,
				Namespace: namespace,
			}
			deployment := &appsv1.Deployment{}
			Eventually(func() error {
				return k8sClient.Get(ctx, deploymentKey, deployment)
			}, timeout, interval).Should(Succeed())

			// Update replicas
			newReplicas := int32(5)
			Eventually(func() error {
				if err := k8sClient.Get(ctx, types.NamespacedName{
					Name: webappName, Namespace: namespace,
				}, webapp); err != nil {
					return err
				}
				webapp.Spec.Replicas = &newReplicas
				return k8sClient.Update(ctx, webapp)
			}, timeout, interval).Should(Succeed())

			// Verify Deployment updated
			Eventually(func() int32 {
				if err := k8sClient.Get(ctx, deploymentKey, deployment); err != nil {
					return -1
				}
				return *deployment.Spec.Replicas
			}, timeout, interval).Should(Equal(int32(5)))
		})
	})

	Context("When deleting a WebApp with a finalizer", func() {
		It("should clean up and allow deletion", func() {
			webappName := "test-delete"
			namespace := "default"
			replicas := int32(1)

			// Create WebApp
			webapp := &appsv1beta1.WebApp{
				ObjectMeta: metav1.ObjectMeta{
					Name:      webappName,
					Namespace: namespace,
				},
				Spec: appsv1beta1.WebAppSpec{
					Image:    "nginx:1.27",
					Replicas: &replicas,
					Port:     80,
				},
			}
			Expect(k8sClient.Create(ctx, webapp)).To(Succeed())

			// Wait for finalizer to be added
			Eventually(func() []string {
				if err := k8sClient.Get(ctx, types.NamespacedName{
					Name: webappName, Namespace: namespace,
				}, webapp); err != nil {
					return nil
				}
				return webapp.Finalizers
			}, timeout, interval).Should(ContainElement(webappFinalizer))

			// Delete the WebApp
			Expect(k8sClient.Delete(ctx, webapp)).To(Succeed())

			// Verify it eventually gets deleted
			Eventually(func() bool {
				err := k8sClient.Get(ctx, types.NamespacedName{
					Name: webappName, Namespace: namespace,
				}, webapp)
				return errors.IsNotFound(err)
			}, timeout, interval).Should(BeTrue())
		})
	})

	Context("When checking status conditions", func() {
		It("should set conditions correctly", func() {
			webappName := "test-conditions"
			namespace := "default"
			replicas := int32(1)

			webapp := &appsv1beta1.WebApp{
				ObjectMeta: metav1.ObjectMeta{
					Name:      webappName,
					Namespace: namespace,
				},
				Spec: appsv1beta1.WebAppSpec{
					Image:    "nginx:1.27",
					Replicas: &replicas,
					Port:     80,
				},
			}
			Expect(k8sClient.Create(ctx, webapp)).To(Succeed())

			// Check that conditions are eventually set
			Eventually(func() int {
				if err := k8sClient.Get(ctx, types.NamespacedName{
					Name: webappName, Namespace: namespace,
				}, webapp); err != nil {
					return 0
				}
				return len(webapp.Status.Conditions)
			}, timeout, interval).Should(BeNumerically(">=", 2))

			// Verify condition types exist
			condTypes := make([]string, len(webapp.Status.Conditions))
			for i, c := range webapp.Status.Conditions {
				condTypes[i] = c.Type
			}
			Expect(condTypes).To(ContainElement("DeploymentReady"))
			Expect(condTypes).To(ContainElement("ServiceReady"))
		})
	})
})
```

### 6.4 Running Tests

```bash
# Install envtest binaries (API Server and etcd)
make envtest
ENVTEST=$(go env GOPATH)/bin/setup-envtest

# Download the binaries
$ENVTEST use --print-path latest

# Run tests
make test

# Or run directly with more output
KUBEBUILDER_ASSETS=$($ENVTEST use --print-path latest) \
  go test ./internal/controller/ -v -ginkgo.v
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Not removing finalizer on cleanup success | Object stuck in Terminating forever | Always remove finalizer after successful cleanup |
| Removing finalizer before cleanup | External resources orphaned | Run cleanup first, remove finalizer only on success |
| Setting LastTransitionTime on every reconcile | Flapping conditions, noisy alerts | Only update time when Status actually changes |
| Using `EventTypeWarning` for normal operations | Confuses monitoring/alerting | Use Warning only for problems |
| Not setting ObservedGeneration on conditions | Users cannot tell if condition is current | Always set to `obj.Generation` |
| Tests without Eventually | Flaky tests due to async reconciliation | Always use `Eventually` for controller state checks |
| Not testing deletion path | Finalizer bugs found in production | Write explicit deletion tests |
| Hardcoded timeouts in tests | Tests fail on slow CI, pass locally | Use generous timeouts (30s+) with short poll intervals |
| Forgetting to register types with scheme | envtest cannot find your CRD | Call `AddToScheme` in `BeforeSuite` |

---

## Quiz

1. **Scenario**: A user runs `kubectl delete webapp critical-db`. The terminal hangs, and the WebApp remains in a `Terminating` state indefinitely. When you check `kubectl get webapp critical-db -o yaml`, you see a `deletionTimestamp` is set and the `finalizers` list contains `apps.kubedojo.io/finalizer`. As the operator developer, how do you troubleshoot this, and what is the most likely cause within your controller code?
   <details>
   <summary>Answer</summary>
   Since the `deletionTimestamp` is set and the finalizer is present, Kubernetes is waiting for your controller to remove the finalizer before it can purge the object from etcd. The most likely cause is that your controller's cleanup logic (e.g., deleting an external cloud resource) is returning an error or hanging indefinitely, which prevents the code from ever reaching the `RemoveFinalizer` step. To troubleshoot, you should inspect the operator's pod logs for cleanup-related error messages or timeouts. You must also ensure that any network calls made during cleanup utilize a context with a strict timeout to prevent the reconcile loop from blocking forever.
   </details>

2. **Scenario**: Your team is debating how to manage the `Conditions` array in the `WebApp` status. A developer proposes simply writing `webapp.Status.Conditions = append(webapp.Status.Conditions, newCondition)` to add the `Ready` status, arguing it is simpler and requires fewer dependencies. Why should you reject this proposal and insist on using `meta.SetStatusCondition`?
   <details>
   <summary>Answer</summary>
   You should reject the proposal because simply appending to the slice will quickly lead to duplicate condition types, creating a massive array that breaks Kubernetes API conventions. The `meta.SetStatusCondition` helper function handles the complex logic of finding an existing condition by its `Type` and updating it in-place. Furthermore, it intelligently manages the `LastTransitionTime` field, only updating it when the actual `Status` string changes from "True" to "False" or vice versa. Manually manipulating the slice risks noisy timestamp churn, duplicate entries, and severe bugs in downstream tools that parse these conditions.
   </details>

3. **Scenario**: An SRE pages you at 3 AM because a WebApp is failing to provision. They tell you, "The status conditions say `Ready: False` with reason `Reconciling`, but that doesn't tell me what is actually broken right now." Where should you instruct the SRE to look to find the step-by-step history of what the operator attempted to do, and why is this information not placed in the status conditions?
   <details>
   <summary>Answer</summary>
   You should instruct the SRE to use `kubectl describe webapp <name>` or `kubectl get events` to view the Kubernetes Events associated with the object. Status conditions are designed to represent the current, static state of the resource (e.g., "Is the database ready?"), not the chronological log of actions taken to achieve that state. Events provide a temporal, point-in-time record of operations, such as warning messages about failed API calls or scale events, which are crucial for debugging real-time failures. Mixing historical logs into the status conditions would violate API conventions and bloat the resource object in etcd.
   </details>

4. **Scenario**: You are reviewing a pull request for a new envtest integration test. The author has written a test that creates a `WebApp`, immediately fetches the expected `Deployment`, and uses standard `Expect(err).NotTo(HaveOccurred())` to verify the Deployment exists. The CI pipeline is failing randomly on this test, but the author claims it passes locally. Why is this test fundamentally flawed in the context of controller testing, and how must it be fixed?
   <details>
   <summary>Answer</summary>
   The test is flawed because controller reconciliation happens asynchronously in a separate goroutine, meaning the `Deployment` will not exist the exact millisecond after the `WebApp` is created. When the test runs locally, the machine might be fast enough for the controller to occasionally win the race condition, but in a slower CI environment, the direct assertion fails immediately. The author must fix this by wrapping the fetch and assertion in a Ginkgo `Eventually` block. `Eventually` polls the API server repeatedly over a specified timeout period, correctly accommodating the asynchronous nature of the Kubernetes controller loop until the resource is successfully reconciled.
   </details>

5. **Scenario**: You deploy your operator with two replicas and leader election enabled. A cluster administrator forces a node restart, killing the pod that was actively acting as the leader. The standby pod is healthy on another node, but you notice that new Custom Resources are completely ignored for about 15 seconds before they finally get processed. A junior engineer suggests there is a bug in the operator's failover logic. How do you explain this behavior to them based on leader election mechanics?
   <details>
   <summary>Answer</summary>
   You should explain that this delay is expected and not a bug, as it is a fundamental safety mechanism of leader election. When the leader pod is abruptly killed, it cannot cleanly release its hold on the Lease object in the API server. The standby pod is continuously polling, but it must wait for the leader's `leaseDuration` (which defaults to 15 seconds) to fully expire before it is allowed to acquire the Lease. During this expiration window, the Lease remains locked to prevent a split-brain scenario where two pods reconcile simultaneously. Once the lease expires, the standby pod successfully acquires it, starts its controllers, and begins processing the backlog of Custom Resources.
   </details>

6. **Scenario**: Your controller's finalizer calls a function to delete an external cloud load balancer. During a production incident, the cloud provider's API goes down for an hour. A user deletes their `WebApp`, triggering the finalizer, but the cloud API returns a 503 error. What exact action should your reconcile loop take when it receives this error, and what will happen to the `WebApp` object during the outage?
   <details>
   <summary>Answer</summary>
   Your reconcile loop must return the error directly back to the controller manager (`return ctrl.Result{}, err`) and it must absolutely not remove the finalizer. Because the finalizer remains attached, the `WebApp` object will safely stay in the `Terminating` state in etcd for the duration of the outage. By returning the error, you trigger the controller-runtime's exponential backoff queue, which will automatically retry the reconciliation loop later. Once the cloud API recovers, a subsequent retry will successfully delete the load balancer, remove the finalizer, and allow Kubernetes to finally purge the `WebApp`.
   </details>

7. **Scenario**: You configure your controller to watch both the `WebApp` (primary resource) and `Deployment` (owned resource). To optimize performance, you apply the `GenerationChangedPredicate` to all watches. Later, you notice a bug: if a user manually scales down the `Deployment`, your operator fails to scale it back up to the desired state defined in the `WebApp`. Why did your optimization cause this bug, and how should you adjust your watch predicates?
   <details>
   <summary>Answer</summary>
   Applying `GenerationChangedPredicate` to the `Deployment` watch caused the bug because Kubernetes only increments the `metadata.generation` field when a resource's spec changes, not when its status changes. When the `Deployment` status changes (e.g., ready replicas drop due to a pod failure or manual intervention), the generation remains the same, so the predicate silently drops the event and prevents reconciliation. You should only apply `GenerationChangedPredicate` to the primary `WebApp` resource to filter out noisy status updates, while allowing all events (or using more specific label predicates) for the owned `Deployment` resources so your controller can properly react to state deviations.
   </details>

---

## Hands-On Exercise

**Task**: Enhance the operator from Module 1.4 with finalizers, status conditions, Kubernetes events, and envtest integration tests.

**Setup**:
```bash
# Use the operator from Module 1.4
cd ~/extending-k8s/webapp-operator

# Ensure dependencies are up to date
go mod tidy

# Ensure envtest binaries are installed
make envtest
```

**Steps**:

1. **Add the finalizer constant and modify the Reconcile function** to handle deletion as shown in Part 1.2

2. **Add structured conditions** by implementing the `updateConditions` function from Part 2.3

3. **Add the EventRecorder** to the Reconciler struct and emit events for:
   - Deployment created
   - Deployment updated (replicas changed)
   - Image updated
   - Cleanup started
   - Cleanup completed
   - Errors (as Warnings)

4. **Wire up leader election** in `cmd/main.go` with the `--leader-elect` flag

5. **Create the envtest suite** in `internal/controller/suite_test.go` (Part 6.2)

6. **Write at least 4 integration tests** (Part 6.3):
   - Creating a WebApp creates Deployment + Service
   - Updating replicas updates the Deployment
   - Deleting a WebApp with finalizer works correctly
   - Status conditions are set properly

7. **Run the tests**:
```bash
make test
```

8. **Run the operator and test manually**:
```bash
kind create cluster --name advanced-operator-lab
make install
make run

# In another terminal
cat << 'EOF' | kubectl apply -f -
apiVersion: apps.kubedojo.io/v1beta1
kind: WebApp
metadata:
  name: advanced-demo
spec:
  image: nginx:1.27
  replicas: 2
  port: 80
EOF

# Checkpoint: Wait for the operator to successfully reconcile the resource
kubectl wait --for=condition=Ready webapp/advanced-demo --timeout=60s

# Check events
kubectl describe webapp advanced-demo

# Check conditions
kubectl get webapp advanced-demo -o jsonpath='{range .status.conditions[*]}{.type}: {.status} ({.reason}){"\n"}{end}'

# Delete and watch cleanup
kubectl delete webapp advanced-demo
kubectl get events --sort-by=.lastTimestamp | tail -10
```

9. **Cleanup**:
```bash
kind delete cluster --name advanced-operator-lab
```

**Success Criteria**:
- [ ] Finalizer is added on creation
- [ ] Finalizer prevents immediate deletion; cleanup runs first
- [ ] Status conditions include DeploymentReady, ServiceReady, and Ready
- [ ] ObservedGeneration is set correctly
- [ ] Kubernetes Events are visible in `kubectl describe`
- [ ] Leader election flag is wired up
- [ ] All 4 envtest integration tests pass
- [ ] `make test` exits cleanly

---

## Next Module

[Module 1.6: Admission Webhooks](../module-1.6-admission-webhooks/) - Intercept and modify API requests with mutating and validating webhooks.
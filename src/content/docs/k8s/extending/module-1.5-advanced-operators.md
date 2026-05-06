---
title: "Module 1.5: Advanced Operator Development"
slug: k8s/extending/module-1.5-advanced-operators
revision_pending: false
sidebar:
  order: 6
---

# Module 1.5: Advanced Operator Development

> **Complexity**: `[COMPLEX]` - Production-grade operator patterns
>
> **Time to Complete**: 5 hours
>
> **Prerequisites**: Module 1.4 (Kubebuilder), Go testing fundamentals, and a Kubernetes 1.35+ cluster for manual validation

---

## Learning Outcomes

After completing this module, you will be able to:

1. **Implement** finalizers that cleanly remove external resources such as DNS records, cloud load balancers, and monitoring objects before a custom resource is deleted.
2. **Design** structured status conditions that follow Kubernetes API conventions so users can diagnose readiness, generation drift, and reconciliation failures with `kubectl describe`.
3. **Configure** leader election, owned-resource watches, and event recording so a multi-replica operator remains observable and avoids split-brain reconciliation.
4. **Construct** envtest integration tests that validate creation, update, status, and finalizer cleanup across the full reconciliation lifecycle.

## Why This Module Matters

Hypothetical scenario: your platform team has promoted the WebApp operator from Module 1.4 into a shared development cluster, and teams now rely on it to create Deployments, Services, optional Ingress objects, DNS records, and monitoring dashboards. The first deletion looks harmless: a developer runs `kubectl delete webapp checkout`, the custom resource disappears from their usual listing, and everyone moves on. Later, the DNS name still points to an old endpoint, an external dashboard remains in the monitoring system, and the next deployment fails because the operator never cleaned up resources that Kubernetes itself did not own.

That failure is the dividing line between a demo controller and a production operator. Kubernetes garbage collection can remove dependent Kubernetes objects when owner references are correct, but it cannot call your DNS provider, delete a managed database, or remove a dashboard in another API. Finalizers give your controller a deliberate cleanup window before the API server purges the custom resource from etcd, status conditions give users a current diagnosis without forcing them into controller logs, events give a short operational timeline, and leader election prevents two controller replicas from racing over the same desired state.

This module rewrites the WebApp operator around those production responsibilities. You will keep the reconciliation model from Module 1.4, but you will add deletion handling before normal reconciliation, condition updates after the operator evaluates child resources, event emission at the moments users need an audit trail, high-availability settings for the manager, watch rules for related resources, and envtest coverage that exercises the controller against a real API server and etcd. The aim is not to memorize snippets; the aim is to evaluate where each pattern belongs in the lifecycle and to avoid designs that look correct until the first outage or stuck deletion.

## Finalizers: Making Deletion a Reconciliation Path

Finalizers work because Kubernetes deletion is not a single operation when finalizers are present. When a user deletes an object, the API server sets `metadata.deletionTimestamp`, keeps the object in storage, and waits until every entry in `metadata.finalizers` has been removed. Your controller sees the same object again, but it now represents a cleanup request rather than a normal desired-state request. That means finalizer logic must run before the rest of reconciliation, because creating or updating child resources while the parent is terminating usually creates more work for the cleanup path.

The useful mental model is a moving-out checklist. Kubernetes is ready to remove the apartment record, but your controller says, "hold the record until I return the keys, cancel the utilities, and forward the mail." If cleanup succeeds, the controller removes only its own finalizer and lets the API server continue deletion. If cleanup fails, the finalizer stays attached, the object remains in the terminating state, and controller-runtime retries the reconcile request with backoff. That retry behavior is why finalizer cleanup should be idempotent: deleting a missing DNS record should usually be treated as success, while a transient provider error should return an error so the queue tries again.

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

Pause and predict: if the cleanup logic fails and you remove the finalizer anyway, what will Kubernetes do next, and which system will still remember the external resource? The answer is the core safety rule for finalizers. Removing the finalizer is the acknowledgement that cleanup is complete, so it must be the last successful step, not the first hopeful step.

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

The implementation has two intentionally separate branches. The deletion branch handles an object with `DeletionTimestamp` first, because no new desired state should be created while teardown is pending. The normal branch makes sure the finalizer exists before any external resources are created, then returns so the update event triggers a clean second pass. That early return avoids mixing "I changed object metadata" with "I created child resources" in one reconcile call, which makes conflicts and retries easier to reason about.

| Practice | Why |
|----------|-----|
| Use a domain-qualified name | Avoids collisions: `apps.kubedojo.io/finalizer` |
| Check `DeletionTimestamp` first | Always handle deletion before normal reconciliation |
| Return early after adding finalizer | Let the watch trigger a clean re-reconcile |
| Log cleanup actions | Essential for debugging stuck deletions |
| Handle cleanup errors gracefully | Return error to retry, but avoid infinite loops |
| Set a timeout on cleanup | External APIs can hang; use context with timeout |

Finalizers also change how you think about timeouts and partial failure. A cloud API outage should not cause data loss, so returning an error and keeping the object in `Terminating` is usually the correct behavior. A permanent "not found" response from the external API is different: if the resource is already gone, the cleanup intent has been satisfied, and the controller can remove the finalizer. The operator should make those distinctions explicitly, because deleting a custom resource is often the moment when users have the least patience for ambiguous behavior.

Finalizer ownership should also be narrow. Your controller should remove only the finalizer string it owns, leaving other controllers' finalizers intact. That matters when several systems coordinate around one resource, such as a backup controller, a policy controller, and the WebApp operator. If your code overwrites the whole finalizer list, you can accidentally tell the API server that other cleanup work is done when it has not even started. Use helper functions that add or remove a single entry, and treat update conflicts as normal retries rather than exceptional corruption.

The most reliable cleanup functions are written like reconciliation functions. They read enough external state to determine whether work remains, take one safe action, and return a precise result. For example, a DNS deletion helper can look up the expected record, return success if the record is already missing, delete it if it exists and matches the WebApp owner metadata, and return an error if the provider cannot answer. That structure makes retries safe and makes logs meaningful, because every retry is another attempt to drive the external system toward the desired "absent" state.

You should avoid long blocking cleanup inside one reconcile call when the external API has slow operations. If deleting a managed database requires a multi-minute asynchronous operation, the finalizer can initiate deletion, write a condition such as `CleanupPending`, emit a Normal event, and requeue after a short delay to poll progress. The object remains in `Terminating`, but the controller does not hold a goroutine indefinitely or hide progress from users. The important rule is that the finalizer stays present until the external system has reached the safe terminal state.

Finalizers are not a replacement for owner references. For Kubernetes children such as Deployments and Services, owner references allow built-in garbage collection to do the right thing after the parent is deleted. For resources outside the cluster, or resources you intentionally do not own through Kubernetes metadata, finalizers are the hook that lets your controller participate in deletion. Production operators often use both: owner references for in-cluster dependents and finalizers for external systems or cleanup ordering that garbage collection cannot express.

When a deletion becomes stuck, resist the reflex to remove the finalizer manually. Manual removal is sometimes the right emergency action, but it should be treated as an operator override with a known cleanup debt, not as the normal fix. First read the object's events, controller logs, and status conditions to identify whether the cleanup function is failing, timing out, or waiting on a dependency. If you do patch the finalizer away during an incident, record the external resource identifiers so a human can complete cleanup afterward.

There is also a user-experience side to finalizers. A WebApp that sits in `Terminating` with no status update and no event looks broken even when the controller is carefully protecting external resources. A good deletion path sets a condition or phase that names cleanup progress, emits a cleanup-start event, logs the external identifiers being cleaned, and emits a cleanup-complete event before removing the finalizer. Users do not need every internal retry, but they do need enough surface area to distinguish "working as designed" from "stuck forever."

## Status Conditions and Events: Current State Plus Timeline

Status conditions and Kubernetes Events solve related but different observability problems. A condition answers, "what is true about this object right now, and is that statement based on the latest spec generation?" An event answers, "what notable action or warning happened recently?" If you overload conditions with history, status becomes noisy and hard for automation to parse. If you rely only on events, users lose a stable readiness signal because events expire and are not a durable contract for controllers or deployment pipelines.

Kubernetes provides `metav1.Condition` as the standard shape for modern custom resources. The most important fields are not just `Type` and `Status`; `ObservedGeneration` tells users whether the controller has processed the latest spec, `Reason` gives automation a stable CamelCase token, `Message` gives humans enough detail to act, and `LastTransitionTime` marks actual status changes rather than every reconcile loop. When these fields are set carefully, `kubectl describe`, dashboards, and GitOps tools can all answer better questions without scraping logs.

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

The WebApp operator needs conditions that mirror the resources it manages and one aggregate condition that users can treat as the primary readiness answer. `DeploymentReady` and `ServiceReady` make it clear which child resource is blocking readiness, while `Ready` summarizes whether the WebApp as a whole is usable. These condition names use positive polarity because positive conditions compose better: `Ready=False` is easier to reason about than `NotReady=True`, especially when automation waits for a condition to become true.

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

Before running the next function in your head, pause and predict: if a user changes the WebApp image and `metadata.generation` increments, what should a pipeline infer when `Ready=True` still has the previous `ObservedGeneration`? It should treat that readiness as stale for the new spec. The old application may still be healthy, but the controller has not yet proven the new requested state.

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

The example uses `meta.SetStatusCondition` instead of appending to the slice because condition arrays are keyed by `Type` in practice. Appending on every reconcile creates duplicates, timestamp churn, and confusing output where one condition says `Ready=True` while a later condition of the same type says `Ready=False`. The helper also protects `LastTransitionTime` semantics by updating the transition time when the status value changes, not merely because the controller recalculated the same state.

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

| Convention | Rule |
|-----------|------|
| Positive polarity | "Ready" not "NotReady", "Available" not "Unavailable" |
| Reason is CamelCase | `ScalingUp`, not `scaling_up` or `Scaling Up` |
| Message is human-readable | Full sentences, include counts and details |
| ObservedGeneration | Always set to `obj.Generation` |
| LastTransitionTime | Only changes when Status changes, not on every update |
| Unknown status | Use when the controller cannot determine the state |

Events fill the gap between stable status and detailed logs. A user who runs `kubectl describe webapp my-app` should see key moments such as a Deployment being created, replicas being scaled, an image being changed, cleanup starting, cleanup completing, or an error blocking reconciliation. Events are intentionally short-lived operational records, so they should not be the only source of truth, but they are often the fastest way for an SRE to see what the operator recently attempted without access to the operator Pod logs.

```go
// internal/controller/webapp_controller.go
type WebAppReconciler struct {
	client.Client
	Scheme   *runtime.Scheme
	Recorder record.EventRecorder
}
```

```go
if err = (&controller.WebAppReconciler{
    Client:   mgr.GetClient(),
    Scheme:   mgr.GetScheme(),
    Recorder: mgr.GetEventRecorderFor("webapp-controller"),
}).SetupWithManager(mgr); err != nil {
    os.Exit(1)
}
```

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

The event taxonomy should be boring and predictable. Use `Normal` for successful routine operations that explain progress, and use `Warning` when a user may need to act or when an external dependency is preventing convergence. Avoid emitting a new event on every reconcile loop for the same unchanged state, because high-frequency events become noise and can hide the warning that actually matters.

A useful condition set is small enough to understand during an incident. It is tempting to create a condition for every helper function because conditions look structured and easy to query. That usually produces status pages where everything is technically present but nothing is decisive. Prefer conditions that map to user-facing readiness boundaries: the Deployment has enough ready replicas, the Service exists and points at the right selector, the Ingress or route is admitted, cleanup is pending, and the whole WebApp is ready. Internal details belong in logs, metrics, or Events unless a user can act on them directly.

Reason values deserve the same discipline as API field names. They are machine-readable strings that users may place in alerts or dashboards, so avoid embedding counts, object names, or changing text inside the reason. Put stable categories such as `ScalingUp`, `ImageUpdating`, `DeploymentFailed`, or `CleanupPending` in `Reason`, then put the contextual detail in `Message`. That split gives automation a stable branch condition while still giving humans enough information to decide whether to wait, inspect a child resource, or escalate an external dependency.

`ObservedGeneration` is one of the easiest fields to set and one of the easiest to omit. When a user edits the spec, Kubernetes increments `metadata.generation`, but status does not become true for that new generation until the controller observes and reconciles it. A deployment pipeline that waits only for `Ready=True` can be fooled by stale readiness from the previous spec. A pipeline that also checks `Ready.ObservedGeneration == metadata.generation` can distinguish "the old version is healthy" from "the requested version has converged."

Status updates should be separated from spec updates in your mental model and, where possible, in your client calls. The status subresource exists so controllers can update observed state without racing with users editing desired state. When you call `r.Status().Update`, you are saying that the spec is still owned by the user and the status is owned by the controller. That separation is part of the Kubernetes API contract, and it helps avoid accidental writes that overwrite a user's recent spec change.

Events should be emitted at state transitions, not at every observation of the same state. If the Deployment already exists and still has the desired replica count, another "DeploymentCreated" event is misleading. If a reconcile loop observes that replicas changed from two to five and applies the update, an event is useful because it explains a user-visible action. The same rule applies to warnings: emit a warning when an API call fails or reconciliation is blocked, but do not flood the event stream with identical warnings on every quick retry if backoff and logs already carry the details.

Conditions, events, and logs form a layered debugging path. Conditions answer the first question a user asks, Events answer what recently changed, and logs answer why the controller chose a specific internal branch. You do not need to put every log detail into the API object. You do need to make sure the first two layers are enough for someone without cluster-admin log access to decide whether the problem is a missing Deployment, a scaling delay, a Service mismatch, an external cleanup failure, or stale status after a new spec generation.

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

## Leader Election and Watch Design

A controller deployment with two replicas is not automatically highly available. Without leader election, both replicas can reconcile the same resource at the same time, each reading stale state, each trying to update child resources, and each writing status. Kubernetes optimistic concurrency will reject some writes, but that is not a design for correctness. Leader election gives the manager a single active controller process while allowing standby replicas to take over after the lease expires.

The safety tradeoff is a short failover delay. If the leader Pod disappears without releasing the Lease, the standby Pod must wait until the lease duration expires before it can acquire leadership. That pause is intentional because it prevents split-brain reconciliation when a leader is slow, partitioned, or temporarily unable to renew. For an operator that manages external resources, a brief pause is usually much better than two replicas issuing conflicting create and delete calls against an outside API.

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

Think through the failure path before changing lease settings: if network latency spikes and the leader Pod fails to renew within the deadline, the standby can acquire the lease, and the old leader must stop controllers when it realizes the lease was lost. Shorter durations improve failover time but increase sensitivity to API server latency. Longer durations reduce false failovers but lengthen the period where no controller is actively processing work after a hard crash.

```go
mgr, err := ctrl.NewManager(ctrl.GetConfigOrDie(), ctrl.Options{
    // ...
    LeaderElection:          true,
    LeaderElectionID:        "webapp-operator.kubedojo.io",
    LeaderElectionNamespace: "webapp-system",  // Optional: defaults to controller namespace
})
```

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

| Parameter | Default | Description |
|-----------|---------|-------------|
| LeaderElectionID | Required | Unique ID for the lease resource |
| LeaseDuration | 15s | How long a lease lasts |
| RenewDeadline | 10s | How long the leader has to renew |
| RetryPeriod | 2s | How often standby pods check |
| LeaderElectionNamespace | Pod namespace | Where the Lease is created |

Watch design is the other half of production reconciliation. `For(&WebApp{})` tells the controller to reconcile when the primary resource changes, while `Owns(&Deployment{})` and `Owns(&Service{})` enqueue the owning WebApp when owned children change. Custom watches are useful when a WebApp depends on a resource it does not own, such as a ConfigMap selected by name. The risk is fan-out: a single ConfigMap update can enqueue many WebApps, so the mapping function should be simple, bounded, and scoped to a namespace unless the operator is intentionally cluster-wide.

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

Predicates are filters, not correctness features, and they can easily hide events your controller needs. `GenerationChangedPredicate` is useful on the primary custom resource because status updates do not change generation and should not necessarily trigger another full pass. Applying the same predicate to owned Deployments can be wrong if you expect to react to readiness changes, Pod failures, or other status-driven signals. A good watch strategy filters the noisy event source, not the event source that carries evidence of drift.

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

```go
builder.WithPredicates(
    predicate.Or(
        predicate.GenerationChangedPredicate{},
        predicate.LabelChangedPredicate{},
    ),
)
```

Which approach would you choose here and why: filtering WebApp status-only updates, filtering Deployment status updates, or leaving owned-resource watches unfiltered until you measure queue pressure? The safest default is usually to filter the primary resource only, then add narrower predicates after you can prove which events are noisy and which events are required for convergence. Operators fail more painfully when they miss drift than when they reconcile one extra time.

Leader election does not make individual reconciliation code thread-safe; it reduces the number of active managers that run the controller. Inside one manager, `MaxConcurrentReconciles` can still allow several WebApps to reconcile at the same time. That is usually desirable, but it means shared clients for external systems must be safe for concurrent use, and cleanup code should avoid global mutable state. If a provider API has strict rate limits, use per-request context deadlines and explicit throttling rather than assuming leader election serializes all work.

The Lease object is also an operational dependency. If your operator loses permission to create or update Leases in its leader election namespace, a multi-replica deployment may start but never run controllers. That failure should be visible in Pod logs and deployment readiness, yet it often surprises teams because RBAC for the custom resource is tested while coordination resources are forgotten. When you enable leader election, review the manager Role or ClusterRole for Lease access in the selected namespace and include that path in deployment validation.

Watch mapping functions should be designed for the largest namespace you expect to support, not just the small demo namespace. Listing every WebApp on every ConfigMap update may be fine for a lab, but it becomes expensive when hundreds of WebApps reference different configuration objects. You can reduce work with labels, indexes, or a field relationship recorded in status, depending on the controller-runtime version and project design. The important question is whether the watch mapping scales with relevant dependents or with every object in the namespace.

Predicates should be reviewed alongside status design. A predicate that drops status updates can be correct when status is purely informational, but it can be wrong when status is the signal that should trigger repair. Deployment readiness changes, Pod availability, and endpoint updates are often status-driven, so owned-resource predicates need more care than primary-resource predicates. If you add a predicate, write down which events it intentionally drops and which reconciliation invariant remains protected without those events.

High availability also changes how you read duplicate-looking logs. During failover, a standby manager may start controllers and reconcile objects that were already queued before the old leader died. That is normal because the queue is an at-least-once mechanism, not exactly-once delivery. The controller code must tolerate repeated requests by reading current state and applying idempotent changes. If a duplicate reconcile causes external resources to be recreated, the bug is in the reconciliation or external idempotency design, not in leader election.

For many operators, the best first tuning value is not a shorter lease duration; it is better observability around leadership. Expose manager metrics, log leadership transitions, and make sure Pod readiness reflects whether the manager is healthy. Then measure how long failover actually takes in your cluster under normal API server latency. Only after that measurement should you tune lease duration, renew deadline, and retry period, because aggressive settings can trade a visible failover pause for intermittent leadership churn that is harder to diagnose.

## Integration Testing with envtest

Unit tests can validate helper functions, but they cannot prove that your CRD schema, scheme registration, status subresource updates, manager startup, ownership links, and asynchronous reconciliation cooperate with the Kubernetes API. `envtest` starts a real API server and etcd locally, then gives your test process a REST config. That makes the tests slower than pure unit tests, but it catches the exact class of bugs that operators often ship: missing RBAC, invalid CRD paths, incorrect status updates, forgotten schemes, and tests that assume reconciliation is synchronous.

The most important testing habit is to assert eventually, not immediately. A controller reacts to watch events, reads from caches, writes through the API server, and may requeue. A direct `Get` immediately after `Create` is a race disguised as a test. Ginkgo's `Eventually` expresses the contract correctly: after the WebApp is created, the Deployment should appear within a reasonable timeout, and the test should poll until the asynchronous system reaches that state or truly fails.

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

	ctx, cancel = context.WithCancel(context.Background())

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

Suite setup is also where many operator tests accidentally become mocks. If you forget to register your API type with the scheme, the client cannot decode your custom resource. If the CRD directory path is wrong and the test does not fail on a missing path, you can run against an API server that has no idea your resource exists. If the manager never starts, assertions against created child objects will never pass because the reconciler is not running. Each line in the setup protects one of those contracts.

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

The deletion test is the one many teams skip, and it is the one that catches finalizer mistakes before users find stuck resources. It waits for the finalizer to appear, deletes the WebApp, and then waits until a `Get` returns `IsNotFound`. In a real operator you would usually add a fake external client and assert that cleanup was called before the finalizer disappeared. For this module, the structural test still proves the controller can enter the deletion branch and release the object.

envtest should not become the only testing layer. Helper functions that build Deployment specs, compute labels, or classify external errors are usually faster and clearer as unit tests. envtest is strongest when the behavior depends on Kubernetes API machinery: CRD validation, owner references, status subresource writes, manager startup, finalizer deletion, and asynchronous reconciliation. A balanced test suite keeps pure logic fast while using envtest for the lifecycle paths where a fake client would hide important behavior.

When envtest fails, read the failure through the reconciliation timeline. A missing child Deployment can mean the manager never started, the WebApp type was not registered, the CRD was not installed, RBAC prevented a write, the reconcile loop returned early after adding a finalizer, or the test used the wrong namespace. Each possibility maps to a different setup or controller branch. Adding logs to the test manager and using `Eventually` blocks that return useful errors will save more time than increasing timeouts blindly.

The finalizer test can be made more realistic by injecting a cleanup collaborator. Instead of calling a real cloud API, define an interface for external cleanup and provide a fake implementation in tests. The fake can record calls, return a transient error once, and then succeed on retry. That lets envtest prove the controller keeps the finalizer after a cleanup failure and removes it only after a later success. The lesson is the same as production design: external side effects belong behind interfaces that can be reasoned about under retries.

Status condition tests should check more than the number of conditions. A robust test fetches the WebApp after reconciliation, finds the `Ready` condition by type, verifies the status and reason, and compares `ObservedGeneration` to the WebApp generation. If the test updates the spec, it can first observe stale status and then wait for the condition to catch up to the new generation. That pattern catches a subtle but important class of bugs where the operator reports readiness without proving it processed the latest desired state.

Event tests are possible but should be selective. Events are useful for user experience, yet they are not a durable source of truth, and their storage behavior can vary across clusters. In envtest, you can assert that the recorder is configured or use a fake recorder for unit-level checks around event emission branches. For this module's main integration path, prioritize finalizer behavior, child-resource creation, status, and update handling, because those are durable API contracts that directly affect correctness.

Manual testing after envtest still has value because it exercises packaging and permissions that the local suite may not cover. Installing the CRD into a Kind cluster, running the manager, applying a WebApp, waiting for readiness, reading events, and deleting the resource shows whether manifests, RBAC, leader-election flags, and generated YAML are coherent. Treat manual testing as a packaging smoke test, not as a substitute for automated lifecycle tests. The result you want is confidence from both directions: repeatable tests for behavior and a quick cluster run for deployment wiring.

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

## Patterns & Anti-Patterns

The strongest operator designs keep the reconciliation contract narrow: every pass observes current state, compares it to desired state, makes one bounded set of changes, records status, and exits. Finalizers, conditions, events, leader election, watches, and envtest are not separate decorations around that loop. They are guardrails that keep the loop correct when deletion, outages, user questions, replica failover, child-resource drift, and asynchronous tests enter the system.

| Pattern | When to Use It | Why It Works |
|---------|----------------|--------------|
| Idempotent finalizer cleanup | Any operator that creates resources outside Kubernetes garbage collection | Retries become safe because a repeated cleanup call reaches the same final state |
| Positive, generation-aware conditions | Any custom resource consumed by humans, GitOps tools, or automation | Users can distinguish stale success from current success after a spec change |
| Event recording at lifecycle transitions | Creation, scaling, image updates, cleanup, and warning paths | The object carries a recent operational timeline visible through standard Kubernetes tools |
| Leader election with at least two replicas | Operators that must survive node failure or voluntary disruption | One active reconciler prevents split-brain while standby Pods provide failover |
| envtest coverage around lifecycle behavior | Controllers with CRDs, owner references, status updates, and finalizers | Tests exercise a real API server instead of assuming Kubernetes behavior in mocks |

The main anti-pattern is treating controller code as ordinary CRUD code. A controller is an eventually consistent repair loop, so it must tolerate duplicate requests, stale reads, conflict retries, external API failures, and deleted objects that still exist temporarily because finalizers are holding them. Patterns that work in a request-response service can become dangerous here if they assume one call, one change, and one final answer.

There is a useful review habit for advanced operator work: name the invariant before reviewing the code. For finalizers, the invariant is that external resources are absent before the custom resource is purged. For conditions, the invariant is that status describes the latest observed generation. For leader election, the invariant is that only one active manager reconciles at a time. For envtest, the invariant is that asynchronous controller behavior is observed through the API server. Code is much easier to review when each helper is judged against the invariant it protects.

Another review habit is to separate correctness from convenience. A short predicate, a manual condition append, or a finalizer patch may make a local test pass, but the production question is whether the behavior remains correct under retries, conflicts, and outages. Advanced operator development is mostly about those uncomfortable edges. If you can explain what happens when the API server is slow, the cloud provider returns an error, the leader Pod dies, and the test runs on a slow CI worker, the design is usually on solid ground.

The same standard applies after the first release. Operators become part of the cluster control plane from the user's point of view, so regressions in deletion, readiness, or failover feel like platform failures rather than application bugs. Keep a small runbook beside the code that explains stuck finalizers, stale observed generations, missing events, leader election lease problems, and envtest setup failures. That runbook forces the design to remain explainable, and explainable controllers are much easier to operate during real incidents.

| Anti-Pattern | What Goes Wrong | Better Alternative |
|--------------|-----------------|--------------------|
| Removing a finalizer before cleanup | The API server deletes the custom resource and the external resource becomes orphaned | Run cleanup first, treat not-found cleanup as success, then remove only your finalizer |
| Appending conditions manually | Duplicate condition types accumulate and readiness automation reads contradictory state | Use `meta.SetStatusCondition` and maintain one condition per type |
| Emitting warning events for normal progress | Dashboards and humans learn to ignore warnings that should indicate action | Use `Normal` for expected transitions and `Warning` for blocked reconciliation |
| Applying aggressive predicates everywhere | Status changes or child-resource drift are filtered out before the controller can repair them | Filter the primary resource carefully and measure owned-resource noise before filtering |
| Testing reconciliation with immediate assertions | CI becomes flaky because the controller loop is asynchronous | Use `Eventually` around API observations that depend on reconciliation |

## Decision Framework

Use this decision framework when you review an operator change. Start by asking whether the operator manages anything Kubernetes cannot garbage-collect. If it does, add a finalizer before creating that external resource and test deletion explicitly. Then ask whether a user can diagnose current readiness without logs. If they cannot, add structured conditions with `ObservedGeneration`. Next ask whether a user can see the recent action history. If they cannot, emit targeted events for lifecycle transitions and warnings.

```
Need to add production behavior?
    │
    ├── External resource outside owner references?
    │       └── Add idempotent finalizer cleanup and deletion tests
    │
    ├── Users or pipelines need current readiness?
    │       └── Add positive conditions with ObservedGeneration
    │
    ├── Users need a recent action timeline?
    │       └── Emit Normal and Warning Events at meaningful transitions
    │
    ├── Operator needs multiple replicas?
    │       └── Enable leader election and tune lease settings conservatively
    │
    ├── Related resources should trigger repair?
    │       └── Add owned or mapped watches with cautious predicates
    │
    └── Behavior crosses API-server boundaries?
            └── Cover it with envtest and Eventually assertions
```

The decision is rarely "turn on every advanced feature." A namespaced toy controller that only creates owned Deployments may not need custom mapped watches, and a single-cluster learning operator may not need tuned lease timings. A production platform operator that provisions external resources, updates status consumed by deployment automation, and runs across nodes needs the full set. The practical skill is matching the feature to the failure mode you are trying to prevent.

| Concern | Minimal Operator | Production Operator | Review Question |
|---------|------------------|---------------------|-----------------|
| Cleanup | Owner references only | Finalizers plus idempotent external cleanup | What survives after the custom resource is deleted? |
| Readiness | Phase string or logs | Standard conditions with observed generation | Can automation tell whether status matches the latest spec? |
| Observability | Controller logs | Events plus conditions plus logs | Can a user diagnose the object without Pod log access? |
| Availability | One replica | Multiple replicas with leader election | What happens when the active Pod dies? |
| Testing | Unit tests for helpers | envtest lifecycle tests | Does the test use the same API machinery as the controller? |

## Did You Know?

- **Finalizers predate many modern operator conventions**: the field is part of Kubernetes object metadata, so it applies broadly to built-in and custom resources rather than being an operator-specific extension.
- **`metav1.Condition` standardizes six key fields**: `Type`, `Status`, `ObservedGeneration`, `LastTransitionTime`, `Reason`, and `Message` give tools a shared contract for readiness and diagnostics.
- **controller-runtime leader election uses Lease resources**: the default timing values include a 15 second lease duration, a 10 second renew deadline, and a 2 second retry period unless you configure them differently.
- **envtest is not a fake client**: it starts real API server and etcd binaries, which is why it can catch CRD validation, scheme registration, status subresource, and reconciliation timing problems.

## Common Mistakes

| Mistake | Why It Happens | How to Fix It |
|---------|----------------|---------------|
| Not removing finalizer on cleanup success | The code runs cleanup but never acknowledges completion to the API server | Always remove your finalizer after successful cleanup and update the object |
| Removing finalizer before cleanup | The developer treats finalizer removal as the start of deletion instead of the completion signal | Run cleanup first, handle not-found as success, and remove the finalizer last |
| Setting `LastTransitionTime` on every reconcile | The controller rebuilds conditions manually and resets timestamps even when status is unchanged | Use `meta.SetStatusCondition` or equivalent logic that updates transition time only on status changes |
| Using `EventTypeWarning` for normal operations | Every lifecycle event feels important during development, so warnings become noisy | Reserve Warning events for problems and use Normal events for successful transitions |
| Not setting `ObservedGeneration` on conditions | Status is written without connecting it to the spec generation that produced it | Always set condition and top-level observed generation from `obj.Generation` |
| Tests without `Eventually` | The test assumes reconciliation is synchronous because the local machine is fast | Poll expected API state with `Eventually` and realistic timeouts |
| Not testing deletion path | Creation and update paths feel more visible, so finalizer bugs hide until a user deletes a resource | Add an envtest case that waits for the finalizer, deletes the object, and observes final removal |
| Forgetting to register types with the scheme | envtest starts, but the client cannot encode or decode the custom resource | Call your API package's `AddToScheme` during suite setup before creating the client |

## Quiz

<details><summary>Scenario: A user runs `kubectl delete webapp critical-db`, and the WebApp remains in `Terminating` with `apps.kubedojo.io/finalizer` still present. What should you inspect first, and what controller behavior is most likely blocking deletion?</summary>

The `deletionTimestamp` plus finalizer means Kubernetes is waiting for your controller to finish cleanup and remove its finalizer. Inspect the operator logs around the cleanup path, then check any external API calls that deletion depends on, such as DNS or load balancer deletion. The likely blocker is that `cleanupExternalResources` is returning an error, hanging without a timeout, or never reaching `controllerutil.RemoveFinalizer`. The correct fix is not to patch the finalizer away blindly; fix or safely bypass the cleanup failure, then let the controller remove the finalizer after cleanup has succeeded or the external resource is confirmed absent.

</details>

<details><summary>Scenario: A developer proposes appending a new `Ready` condition on every reconcile because it is simpler than using `meta.SetStatusCondition`. Why should you reject that design?</summary>

Conditions are intended to behave like a keyed set by `Type`, not a historical log. Appending creates duplicate `Ready` entries, leaves stale values in the array, and can confuse users or automation that reads the first matching condition. It also makes `LastTransitionTime` noisy because the code tends to reset timestamps even when the status did not actually transition. `meta.SetStatusCondition` updates the existing condition for the type and preserves Kubernetes condition conventions, so it is the safer design.

</details>

<details><summary>Scenario: An SRE sees `Ready=False` with reason `Reconciling`, but they need to know whether the operator created a Deployment, scaled it, or hit an API error. Which signal should they inspect, and why is that not all stored in conditions?</summary>

They should inspect Kubernetes Events with `kubectl describe webapp <name>` or `kubectl get events` filtered to the WebApp. Conditions represent current state, while Events represent recent point-in-time actions and warnings. Putting every historical action into conditions would bloat the status object and make readiness harder to parse. The operator should keep a stable condition such as `Ready=False` and use Events to show the timeline that led to the current state.

</details>

<details><summary>Scenario: A PR adds an envtest that creates a WebApp and immediately expects the Deployment to exist with a direct `Get`. The test passes locally but fails randomly in CI. What is the flaw, and how should the test be rewritten?</summary>

The test treats reconciliation as synchronous, but the controller processes events asynchronously through the manager and API server. On a fast laptop the Deployment may appear before the assertion, while a slower CI job exposes the race. The test should wrap the `Get` in `Eventually`, using a timeout and polling interval that give the controller time to observe the WebApp and create the child Deployment. Immediate assertions are still fine for pure object fields after a successful `Get`, but not for state that depends on reconciliation.

</details>

<details><summary>Scenario: You deploy two operator replicas with leader election enabled, then the leader node restarts. New WebApps wait about 15 seconds before reconciliation resumes. Is this a bug, and how do you explain the delay?</summary>

That delay is expected when the old leader disappears without releasing the Lease. The standby Pod must wait until the lease duration expires before acquiring leadership, otherwise a slow or partitioned old leader could overlap with the new leader and create split-brain reconciliation. The default timing favors correctness over instant failover. If the delay is unacceptable, tune leader election settings cautiously and test API server latency, because overly aggressive settings can cause unnecessary leadership churn.

</details>

<details><summary>Scenario: A cloud provider API returns 503 while the finalizer is deleting an external load balancer. What should the reconcile loop return, and what happens to the WebApp during the outage?</summary>

The reconcile loop should return the error and keep the finalizer attached. The WebApp remains in `Terminating`, which is the safe state because Kubernetes will not purge the custom resource while cleanup is incomplete. controller-runtime will retry the request with backoff, giving the provider time to recover. Once cleanup succeeds or the load balancer is confirmed already absent, the controller can remove the finalizer and allow deletion to finish.

</details>

<details><summary>Scenario: You add `GenerationChangedPredicate` to both the WebApp watch and the owned Deployment watch. After a manual Deployment change, the operator does not repair the drift. Why did the predicate cause this, and what should you change?</summary>

`GenerationChangedPredicate` only passes events when `metadata.generation` changes, and that can drop events your controller needs from owned resources. If the operator depends on Deployment status or other updates to detect drift, filtering the owned watch prevents reconciliation from being enqueued. Keep the predicate on the primary WebApp when you want to ignore status-only updates there, but leave the Deployment watch unfiltered or use a narrower predicate that preserves the drift signals you need. Optimization should follow measured queue pressure, not remove correctness signals by default.

</details>

## Hands-On Exercise

Exercise scenario: enhance the WebApp operator from Module 1.4 with finalizers, status conditions, Kubernetes events, leader election, owned-resource watches, and envtest integration tests. Work in a disposable repository or branch, because this exercise touches controller code, manager setup, manifests, and tests. The goal is to prove that the operator can create, update, report, and delete safely rather than only compile.

```bash
# Use the operator from Module 1.4
cd ~/extending-k8s/webapp-operator

# Ensure dependencies are up to date
go mod tidy

# Ensure envtest binaries are installed
make envtest
```

Task 1 is to add the finalizer constant and modify `Reconcile` so deletion is handled before normal reconciliation. Add the finalizer before creating external resources, return after the metadata update, and make cleanup idempotent. The success signal is that a new WebApp gains the finalizer and a deleted WebApp does not disappear until cleanup has completed.

Task 2 is to add structured conditions by implementing the `updateConditions` function from this module. The conditions should include `DeploymentReady`, `ServiceReady`, and aggregate `Ready`, each with `ObservedGeneration`, a CamelCase reason, and a useful message. The success signal is that `kubectl describe` and JSONPath output show current condition values tied to the latest generation.

Task 3 is to add the `EventRecorder` to the reconciler and emit events for Deployment creation, replica updates, image updates, cleanup start, cleanup completion, and warning paths. Keep events concise and avoid emitting repeated progress events when nothing changed. The success signal is that `kubectl describe webapp advanced-demo` shows a useful recent timeline.

Task 4 is to wire leader election through `cmd/main.go` and the manager deployment. Run two replicas only when the controller is deployed in-cluster, because local `make run` development usually uses a single process. The success signal is that one replica holds the Lease while the other waits, and reconciliation resumes after the leader Pod is removed.

Task 5 is to create the envtest suite in `internal/controller/suite_test.go` and write lifecycle tests for creation, replica updates, deletion with a finalizer, and status conditions. Use `Eventually` for every assertion that depends on reconciliation. The success signal is a stable `make test` run that passes repeatedly rather than only on the fastest local attempt.

```bash
make test
```

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

```bash
kind delete cluster --name advanced-operator-lab
```

Success criteria:

- [ ] Finalizer is added on creation.
- [ ] Finalizer prevents immediate deletion and cleanup runs first.
- [ ] Status conditions include `DeploymentReady`, `ServiceReady`, and `Ready`.
- [ ] `ObservedGeneration` is set correctly on status and conditions.
- [ ] Kubernetes Events are visible in `kubectl describe`.
- [ ] Leader election flag is wired up for multi-replica deployment.
- [ ] At least four envtest integration tests cover creation, update, deletion, and conditions.
- [ ] `make test` exits cleanly.

## Sources

- https://kubernetes.io/docs/concepts/overview/working-with-objects/finalizers/
- https://kubernetes.io/docs/reference/using-api/api-concepts/
- https://kubernetes.io/docs/concepts/architecture/garbage-collection/
- https://kubernetes.io/docs/reference/kubernetes-api/common-definitions/object-meta/
- https://kubernetes.io/docs/reference/kubernetes-api/cluster-resources/event-v1/
- https://kubernetes.io/docs/reference/kubernetes-api/cluster-resources/lease-v1/
- https://pkg.go.dev/k8s.io/apimachinery/pkg/apis/meta/v1#Condition
- https://pkg.go.dev/k8s.io/apimachinery/pkg/api/meta#SetStatusCondition
- https://pkg.go.dev/sigs.k8s.io/controller-runtime/pkg/envtest
- https://pkg.go.dev/sigs.k8s.io/controller-runtime/pkg/manager
- https://pkg.go.dev/sigs.k8s.io/controller-runtime/pkg/builder
- https://book.kubebuilder.io/reference/envtest

## Next Module

[Module 1.6: Admission Webhooks](../module-1.6-admission-webhooks/) - Intercept and modify API requests with mutating and validating webhooks.

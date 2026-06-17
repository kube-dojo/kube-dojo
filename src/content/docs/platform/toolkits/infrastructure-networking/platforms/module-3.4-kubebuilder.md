---
revision_pending: false
title: "Module 3.4: Kubebuilder - Building Kubernetes Operators"
slug: platform/toolkits/infrastructure-networking/platforms/module-3.4-kubebuilder
sidebar:
  order: 5
---
> **Toolkit Track** | Complexity: `[COMPLEX]` | Time: ~55 minutes

## Overview

Kubebuilder is easiest to understand when you stop treating it as the main idea. The main idea is the Kubernetes Operator pattern: you define a domain-specific API, users write desired state into that API, and a controller keeps reconciling the cluster until observed reality matches that desired state. Kubebuilder is the scaffolding and SDK that helps Go teams create that API and controller with less boilerplate. It gives you a project layout, generators, markers, manifests, RBAC helpers, webhook wiring, tests, and a controller-runtime entry point, but the durable skill is still API design plus reconciliation discipline.

The operator mental model is the same one Kubernetes already uses for built-in resources. A Deployment does not create Pods because a human clicks a button in the control plane; the Deployment controller watches Deployment and ReplicaSet state, notices differences, and repeatedly drives the system toward the declared target. A custom operator applies that same pattern to a domain your platform owns, such as a database, tenant workspace, internal application, certificate bundle, backup policy, or cluster add-on. The custom resource stores intent, the controller implements the operating procedure, and status reports what the controller has actually observed.

This module uses Kubebuilder as the worked example because it exposes the controller-runtime model directly. By the end, you should be able to read a generated Kubebuilder project without being distracted by file count, explain why `Reconcile` must be level-triggered and idempotent, design a CRD that separates `spec` from `status`, and identify where owner references, finalizers, conditions, webhooks, RBAC markers, caches, schemes, and leader election fit in a production controller. The goal is not to memorize a scaffold. The goal is to understand why the scaffold exists.

**What You'll Learn**: This module focuses on the operator concepts and controller-runtime mechanics you need before the Kubebuilder scaffold starts to feel predictable:
- Why operators exist and what problems they solve
- The CRD plus controller model behind the Operator pattern
- Controller-runtime internals: Manager, Reconciler, client, cache, informers, scheme, and webhooks
- Kubernetes API machinery concepts: groups, versions, kinds, resources, subresources, status, conditions, and observed generation
- How Kubebuilder scaffolds a controller-runtime project
- Building, testing, packaging, and deploying a small WebApp operator
- How Kubebuilder compares with Operator SDK and Metacontroller at the capability level

**Prerequisites**: You will get more from the worked example if you already have the following Kubernetes and Go context:
- [CKA Module 1.5: CRDs and Operators](/k8s/cka/part1-cluster-architecture/module-1.5-crds-operators/)
- Go programming basics, especially structs, interfaces, pointers, contexts, and error handling
- Familiarity with Kubernetes manifests, `kubectl`, Deployments, Services, RBAC, and namespaces

---

## What You'll Be Able to Do

After completing this module, you will be able to explain and implement these operator-development tasks with the scaffold as support rather than as a crutch:

- **Implement custom Kubernetes controllers using Kubebuilder with reconciliation loops and CRD generation**
- **Configure RBAC, webhooks, and finalizers for production-grade Kubernetes operators**
- **Deploy custom operators with leader election, health probes, and metrics exposition**
- **Evaluate Kubebuilder's code-generation approach against Operator SDK for custom controller development**

---

## Why This Module Matters

Kubernetes is powerful because it lets teams declare intent and delegate convergence to controllers. You say "run three replicas of this container," and the Deployment controller keeps trying to make that true even when nodes fail, Pods are deleted, or new ReplicaSets need to roll out. Platform engineering becomes more effective when you can extend that same contract to your own domain. Instead of publishing a runbook that says "create a database, wire a Secret, create a Service, configure backups, and update status in a ticket," you publish an API that says "this is the database I want," then let a controller perform the operational work repeatedly and observably.

The practical reason this matters is not fashion. Many platform problems are too stateful for a one-shot script and too domain-specific for a generic Kubernetes primitive. A script can create the first batch of objects, but it does not naturally notice that a Secret changed, a child Deployment was deleted, an external backup job failed, or a user updated a field that requires a safe migration. A CI pipeline can sequence a deployment, but it usually exits when the job ends. An operator stays resident, watches the API, responds to changes, and treats drift as normal input rather than an exceptional condition.

The analogy is a thermostat, but with an important twist. A thermostat does not remember which exact minute the room became cold and replay a "turn on heat" event forever. It reads current temperature, compares it with the desired temperature, and acts if there is a gap. A Kubernetes controller should work the same way. It receives events because events are efficient hints, but the reconcile function should be written as if the only thing that matters is current desired state and current observed state. That level-triggered mindset is what makes controllers recover from missed events, duplicate events, stale cache reads, restarts, and partial previous attempts.

> **Landscape snapshot — as of 2026-06**
>
> Kubebuilder is NOT a standalone CNCF project. It is a Kubernetes SIG subproject (kubernetes-sigs/kubebuilder), part of the Kubernetes ecosystem, Apache-2.0. Do NOT label it CNCF Sandbox/Incubating/Graduated. (Kubernetes itself is CNCF Graduated; Kubebuilder is a k8s sub-project — state this precisely.)
>
> Latest release as of 2026-06: v4.15.0 (2026-06-15). Say "verify at github.com/kubernetes-sigs/kubebuilder/releases".
>
> Built on controller-runtime (sigs.k8s.io/controller-runtime). Verify scaffolded code/markers (+kubebuilder:object:root=true, the Reconciler signature) against current Kubebuilder — do not invent fields.

---

## Why Build Operators

An operator is appropriate when the resource you manage has lifecycle behavior that cannot be safely represented by a static manifest alone. A Deployment is a good fit for "keep these Pods running," because Kubernetes already knows how to roll out ReplicaSets, track readiness, and garbage-collect children. A database cluster, certificate issuer, tenant environment, network attachment, or application platform may need extra domain rules. The controller may need to create several child objects, wait for one object before creating another, call an external API, preserve user data during resize, rotate credentials, retry failed cleanup, or expose a meaningful `Ready` condition to other automation.

The important distinction is between storing configuration and managing behavior. A ConfigMap can store a database backup policy, but it does not make backups happen. A CRD can store a backup policy as a typed Kubernetes object, and a controller can interpret that object continuously. When the policy changes, the controller sees a new generation. When a child Job fails, the controller sees the status. When the parent is deleted, a finalizer can delay deletion while the controller cleans up external state. Those behaviors are the reason the Operator pattern exists.

Operators also improve ownership boundaries. Without an operator, a platform team often gives application teams a bundle of YAML templates, shell scripts, and documentation. The application team must learn which fields are safe, which fields are coupled, which order matters, and which symptoms mean the platform is unhealthy. With a well-designed operator, the platform team exposes a smaller API surface. The application team declares the inputs that are actually theirs, while the controller owns the mechanical details and reports status through Kubernetes-native fields that can be watched by GitOps, alerting, and release automation.

Hypothetical scenario: a platform team maintains an internal `TenantWorkspace` resource. Before the operator exists, onboarding requires a checklist: create a namespace, bind RBAC, install default NetworkPolicies, create a quota, create a GitOps Application, and post the namespace name in a chat channel. The work is repetitive, but the failure mode is not just boredom. If one step is missed, the tenant may deploy without network isolation or without the quota that protects neighboring teams. After the team introduces a controller, a tenant request becomes one manifest, and the controller reconciles the namespace, policies, quota, bindings, and status every time it observes drift.

That scenario is useful because it shows what an operator should and should not hide. It should hide accidental complexity: object ordering, retries, labels, owner references, and cleanup. It should not hide the contract. The CRD must still make the tenant-facing choices explicit, validation must reject unsupported combinations, status must explain what the controller observed, and the controller must be safe to run more than once. If the API is vague, the operator simply turns confusion into automated confusion.

```
OPERATOR MATURITY LADDER
================================================================

Level 1: Documentation
  "Follow these steps carefully."
  Failure mode: people skip, reorder, or misread steps.

Level 2: Script
  "Run this command with these flags."
  Failure mode: one-shot execution does not keep watching drift.

Level 3: Pipeline
  "Merge a change and wait for the job."
  Failure mode: job history is not the current state of the system.

Level 4: Operator
  "Declare desired state and let a controller converge."
  Benefit: continuous, observable, domain-aware reconciliation.

================================================================
```

---

## The Operator Pattern: API Plus Controller

The smallest useful operator has two halves. The first half is a custom API, usually implemented as a CustomResourceDefinition. The CRD tells the Kubernetes API server how to store and validate objects of a new kind. The second half is a controller, usually running as a Deployment, that watches those objects and changes the world to match them. The CRD without the controller is just typed storage. The controller without a clear API is just an automation program with no stable contract. Together, they become a Kubernetes-native product surface.

In that contract, `spec` is desired state. It belongs to the user or to a higher-level automation system such as GitOps. If a user writes `spec.replicas: 3`, the controller should treat that as intent, not as a suggestion that can be silently rewritten. `status` is observed state. It belongs to the controller, and it should answer questions like "what did the controller see," "is the latest desired state applied," "what condition blocks progress," and "which child resource is currently responsible for serving traffic." The status subresource exists so status can be updated independently from spec, with separate RBAC and less risk of accidental intent changes.

This separation is one of the most important API design habits in Kubernetes. A beginner controller often reads a custom resource, notices a default is missing, and writes back into spec from the reconcile loop. That creates surprising ownership, can fight with server-side apply, and may trigger unnecessary generation changes. Prefer schema defaults, admission webhooks, or explicit user fields for desired state. Use status for facts the controller has observed. If the controller wants to say "I processed this version of spec," it should set `status.observedGeneration` or set conditions whose `observedGeneration` matches `metadata.generation`.

Groups, versions, and kinds are the naming system that makes this API work. The `kind` is the object shape users recognize, such as `WebApp`. The API group scopes ownership, such as `webapp.example.com`. The version, such as `v1`, marks the versioned contract for that group and kind. A resource name is the plural endpoint served by the API server, such as `webapps`. A GroupVersionKind identifies the type of object in manifests and Go schemes, while a GroupVersionResource identifies the REST endpoint clients call. Controllers mostly think in typed Go objects, but the API server stores and serves resources through those group-version-resource endpoints.

CRD schema design deserves as much attention as controller code. A loose schema lets invalid intent enter the cluster and forces the controller to reject it later through status, which is slower and more confusing for users. A useful schema declares required fields, ranges, enums, map/list semantics, defaults, and printer columns. Kubebuilder markers are comments in Go source that controller-tools reads to generate those CRD details. That is why a small marker above a field can become OpenAPI validation in the final YAML manifest, and why reviewing API types is reviewing production behavior.

Status conditions are the controller's user interface during waiting, failure, and recovery. A single `phase` string is tempting, but it usually collapses too much information. Conditions let a controller report multiple facts at once, such as `Ready`, `Progressing`, `BackupConfigured`, or `ExternalAccountReady`, each with status, reason, message, timestamps, and observed generation. A good condition is written for both humans and automation. Humans need a clear reason and message. Automation needs stable condition types and a way to know whether the condition reflects the latest spec.

Finalizers solve a different lifecycle problem. Kubernetes deletion is normally fast: the object gets a deletion timestamp, dependents may be garbage-collected, and the object eventually disappears. If your controller created external state that Kubernetes cannot garbage-collect, such as a DNS record, cloud database, or SaaS account, deletion must pause until cleanup finishes. A finalizer is a string on the object that tells Kubernetes not to fully remove it yet. The controller sees the deletion timestamp, performs idempotent cleanup, removes its finalizer, and lets deletion continue. Finalizers must be boring and reliable, because a stuck finalizer becomes a stuck delete.

Owner references connect parent and child objects inside the cluster. If a `WebApp` owns a Deployment and Service in the same namespace, setting controller owner references lets Kubernetes garbage collection remove children when the parent is deleted, and lets controller-runtime map child changes back to the parent when you declare `.Owns(&appsv1.Deployment{})`. Owner references are not a substitute for finalizers. Owner references are for Kubernetes-visible dependent objects. Finalizers are for ordered cleanup, especially when the cleanup target is outside the Kubernetes garbage collector's reach.

---

## Reconciliation Is Level-Triggered

A reconciliation loop should answer one question every time it runs: given the current desired state and the current observed state, what is the smallest safe action that moves the system closer to convergence? That question is different from "which event did I just receive?" Events are hints that wake the controller. They are not a reliable audit log, and they are not the source of truth. The source of truth is the current object graph the controller reads through the Kubernetes API and its cache.

Level-triggered design means the same reconcile call should be safe after a create event, an update event, a child-object event, a resync, a restart, or a manual requeue. If the Deployment already exists with the desired image and replica count, the controller does nothing. If the Deployment is missing, the controller creates it. If the Deployment exists but has the wrong image, the controller patches it. If the Service is correct but status is stale, the controller updates status. If all of those are already true, the controller exits cleanly. The code describes convergence, not event history.

Idempotence is the engineering property that makes this safe. An idempotent reconcile can run repeatedly without producing extra side effects after the first successful convergence. Creating a child object only when it is missing is idempotent. Patching a field only when the current value differs is idempotent. Appending a random suffix to a Secret name on every run is not idempotent. Charging a credit card, creating a cloud database, or rotating credentials on every reconcile is not idempotent unless you store and check enough state to know the action has already been performed.

The controller-runtime return values reinforce this model. Returning an empty result and nil error means "I am done until another event or scheduled requeue happens." Returning an error means "the work failed; retry with backoff." Returning `RequeueAfter` means "wake me after this duration even if no watched object changes," which is useful for polling an external system that does not emit Kubernetes events. Returning `Requeue: true` requests another reconciliation soon, but it should not be used as a substitute for modeling state correctly. If a controller constantly requeues itself because it cannot tell whether work is complete, the API is missing observable state.

There is one subtle consequence learners often miss: reads may be slightly stale. controller-runtime commonly uses a split client, where reads come from a shared cache and writes go directly to the API server. After a successful create or update, the cache may not immediately show the new state until the watch stream catches up. A correct reconciler tolerates that lag. It may return and let the next event observe the update, or it may use direct reads intentionally in a narrow case. What it should not do is assume that an immediate cached read after a write proves the write failed.

```
LEVEL-TRIGGERED RECONCILE SHAPE
================================================================

1. Load the parent object by namespace/name.
2. If it is gone, return successfully.
3. If it is deleting, run finalizer cleanup and update finalizers.
4. Derive desired child resources from spec.
5. Read current children and external observations.
6. Create, patch, or delete only what differs.
7. Write status that describes what was observed.
8. Return a result that matches the remaining work.

================================================================
```

---

## Controller-Runtime Architecture

Kubebuilder projects are controller-runtime projects. The generated `cmd/main.go` builds a Manager, registers schemes, configures metrics and health probes, optionally enables leader election, wires reconcilers, and starts the process. The Manager is the shared runtime for controllers. It owns the cache, client, scheme, REST mapper, webhook server, metrics server, health endpoints, and lifecycle for runnables. In production, that Manager is usually the long-running process inside the operator Deployment.

The Reconciler is the code you own most directly. controller-runtime calls its `Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error)` method with a request that usually contains a namespace and name. The request is deliberately small. It does not contain the full object, because the controller should load current state during reconciliation. This is the first guardrail toward level-triggered design: the framework gives you the key, and your code reads the present.

The cache is backed by informers and watches. It maintains local copies of objects the Manager is configured to watch, which makes ordinary `Get` and `List` calls fast and reduces API server load. The client hides that split for common use: reads often come from cache, while writes go to the API server. That convenience is powerful, but it also means you must understand cache scope. If your controller lists all Secrets in all namespaces by accident, the cache may try to watch far more data than you intended. If your controller needs one namespace or a carefully selected set of object types, configure the Manager and watches accordingly.

The scheme connects Go types to Kubernetes API identities. Built-in Kubernetes types, your custom API types, and any external types your controller reads must be added to the scheme before the client can encode, decode, or set owner references for them reliably. When Kubebuilder scaffolds an API package, it generates a `SchemeBuilder` and an `init` registration function for your `WebApp` and `WebAppList` types. When `cmd/main.go` calls your API package's `AddToScheme`, it teaches the Manager how to handle those objects.

Watches decide what enqueues reconcile requests. The most common setup is `For(&webappv1.WebApp{})`, which watches the parent resource, and `Owns(&appsv1.Deployment{})`, which watches child resources owned by the parent. A child Deployment update does not ask the Deployment reconciler to run; it maps the child event back to the owning `WebApp` request. Predicates can filter events before they reach the queue, such as ignoring status-only updates for a parent when status writes would otherwise create noisy loops.

The work queue deduplicates requests. If five events arrive for the same namespace and name while the object is already queued, the controller does not need five separate runs to process them. It needs at least one run that reads current state. That deduplication is another reason event-specific logic is fragile. By the time your reconcile starts, several changes may have collapsed into one request, and the correct response is to inspect the current object graph rather than infer meaning from an individual event.

```
CONTROLLER-RUNTIME RECONCILE LOOP
================================================================

API server watch stream
        |
        v
Informer and cache maintain local object state
        |
        v
Event handlers and predicates decide whether to enqueue
        |
        v
Work queue stores namespace/name reconcile requests
        |
        v
Reconciler loads current desired and observed state
        |
        v
Client writes changes to the Kubernetes API server
        |
        v
Status update reports what the controller observed

================================================================
```

Webhooks are part of the same runtime, but they serve a different purpose from reconciliation. A validating webhook rejects invalid requests before they are persisted. A defaulting webhook fills default values during admission. A conversion webhook translates between API versions when a CRD serves more than one version. Reconciliation handles ongoing convergence after an object exists. If a rule can be enforced synchronously and deterministically at write time, validation or defaulting may be the right layer. If a rule depends on current cluster state, external systems, or long-running work, reconciliation is usually the right layer.

---

## Kubebuilder Scaffolding Walkthrough

Kubebuilder scaffolding is opinionated boilerplate for the architecture described above. The scaffold gives you a Go module, a Manager entry point, an API package, a controller package, Kustomize configuration, RBAC generation, CRD generation, tests, and a Makefile. The generated files are not magic. Each file exists because a controller-runtime operator needs a place to define API types, register those types in a scheme, implement reconcile logic, generate manifests, and package the manager for deployment.

Start by creating a project. The exact installation method can change, so treat the Kubebuilder book and release page as the source of truth for the binary. The commands below show the common development flow and use a deliberately small `WebApp` domain so the controller logic stays readable. In a real platform operator, spend more time on API design before running the scaffolder, because generated code is easy to change but a published API contract is expensive to repair.

```bash
# Install Kubebuilder using the method recommended by the Kubebuilder book.
# This URL resolves to a binary for your operating system and architecture.
curl -L -o kubebuilder "https://go.kubebuilder.io/dl/latest/$(go env GOOS)/$(go env GOARCH)"
chmod +x kubebuilder
sudo mv kubebuilder /usr/local/bin/

mkdir webapp-operator
cd webapp-operator

kubebuilder init --domain example.com --repo github.com/example/webapp-operator
kubebuilder create api --group webapp --version v1 --kind WebApp
```

After answering yes to creating both the resource and controller, the project has a shape like this:

```text
webapp-operator/
├── api/
│   └── v1/
│       ├── webapp_types.go
│       └── groupversion_info.go
├── cmd/
│   └── main.go
├── config/
│   ├── crd/
│   ├── default/
│   ├── manager/
│   ├── rbac/
│   └── samples/
├── internal/
│   └── controller/
│       ├── webapp_controller.go
│       └── suite_test.go
├── Dockerfile
├── Makefile
├── PROJECT
└── go.mod
```

The `api/v1` directory defines the Kubernetes API type. It is where you decide the schema users will write and the status shape your controller will publish. The `internal/controller` directory defines the reconciler. It is where you compare desired state with observed state and perform Kubernetes API writes. The `config` directory contains generated and customizable manifests for CRDs, RBAC, the manager Deployment, sample custom resources, and Kustomize overlays. The `PROJECT` file records scaffold metadata used by Kubebuilder plugins and update workflows.

Kubebuilder markers are comments, but they are comments with build-time meaning. A marker such as `+kubebuilder:object:root=true` tells the object generator that a Go type represents a Kubernetes Kind and needs runtime object support. A marker such as `+kubebuilder:subresource:status` tells CRD generation to enable a status subresource. Validation markers become OpenAPI schema rules. RBAC markers become ClusterRole or Role rules. This marker system keeps API intent close to the Go types and controller code that rely on it, which makes reviews easier than maintaining all generated YAML by hand.

The scaffolder does not absolve you from reviewing generated output. Running `make manifests` after changing API types updates the CRD, RBAC, and webhook manifests. Running `make generate` updates generated Go code such as deep-copy methods. A responsible operator author checks both the Go diff and the generated manifest diff, because a small marker change can widen permissions, change validation, alter printer columns, or affect whether status updates are authorized separately from spec updates.

---

## Build a WebApp Operator

The example API will manage a simple web application by creating a Deployment and a Service for each `WebApp` custom resource. This is intentionally small, but it contains the core mechanics you need in larger operators: desired state in spec, observed state in status, generated validation, owner references on children, RBAC markers, and a reconciler that creates or updates children when they drift. Do not copy this API as a universal application platform. Use it to learn the controller shape.

### API Type Definition

Edit `api/v1/webapp_types.go` so the custom resource has a narrow desired state and a useful status. The `Image`, `Replicas`, and `Port` fields are user intent. The `AvailableReplicas`, `ObservedGeneration`, and `Conditions` fields are controller-owned observations. The conditions list uses the standard `metav1.Condition` shape so other Kubernetes-aware tools can interpret it consistently.

```go
package v1

import (
    metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// WebAppSpec defines the desired state of WebApp.
type WebAppSpec struct {
    // Image is the container image to deploy.
    // +kubebuilder:validation:Required
    // +kubebuilder:validation:MinLength=1
    Image string `json:"image"`

    // Replicas is the desired number of pods.
    // +kubebuilder:default=1
    // +kubebuilder:validation:Minimum=1
    // +kubebuilder:validation:Maximum=10
    Replicas *int32 `json:"replicas,omitempty"`

    // Port is the container port exposed by the Service.
    // +kubebuilder:default=8080
    // +kubebuilder:validation:Minimum=1
    // +kubebuilder:validation:Maximum=65535
    Port int32 `json:"port,omitempty"`
}

// WebAppStatus defines the observed state of WebApp.
type WebAppStatus struct {
    // AvailableReplicas is the number of ready pods observed on the Deployment.
    AvailableReplicas int32 `json:"availableReplicas,omitempty"`

    // ObservedGeneration is the latest metadata.generation processed by the controller.
    ObservedGeneration int64 `json:"observedGeneration,omitempty"`

    // Conditions represent the latest observations for this WebApp.
    // +optional
    // +listType=map
    // +listMapKey=type
    Conditions []metav1.Condition `json:"conditions,omitempty"`
}

// +kubebuilder:object:root=true
// +kubebuilder:subresource:status
// +kubebuilder:printcolumn:name="Image",type=string,JSONPath=`.spec.image`
// +kubebuilder:printcolumn:name="Replicas",type=integer,JSONPath=`.spec.replicas`
// +kubebuilder:printcolumn:name="Available",type=integer,JSONPath=`.status.availableReplicas`
// +kubebuilder:printcolumn:name="Age",type="date",JSONPath=".metadata.creationTimestamp"

// WebApp is the Schema for the webapps API.
type WebApp struct {
    metav1.TypeMeta   `json:",inline"`
    metav1.ObjectMeta `json:"metadata,omitempty"`

    Spec   WebAppSpec   `json:"spec,omitempty"`
    Status WebAppStatus `json:"status,omitempty"`
}

// +kubebuilder:object:root=true

// WebAppList contains a list of WebApp.
type WebAppList struct {
    metav1.TypeMeta `json:",inline"`
    metav1.ListMeta `json:"metadata,omitempty"`
    Items           []WebApp `json:"items"`
}

func init() {
    SchemeBuilder.Register(&WebApp{}, &WebAppList{})
}
```

Run generation after editing the API type. The CRD is the user-facing contract, so inspect it before deploying. Confirm that the status subresource exists, the schema contains validation for the fields you intended to validate, and the printer columns show useful information for a quick `kubectl get`.

```bash
make manifests
make generate
```

### Controller Reconcile Function

The reconciler below manages two child resources. The Deployment runs the container image and replica count declared by the `WebApp`. The Service selects the same Pods and exposes the declared target port. The code is intentionally direct so you can see the pattern: fetch the parent, handle deletion, reconcile each child, update status, and return. Larger controllers often split these steps into helpers, use patches instead of full updates, and add more careful condition management, but the shape is the same.

```go
package controller

import (
    "context"

    appsv1 "k8s.io/api/apps/v1"
    corev1 "k8s.io/api/core/v1"
    apierrors "k8s.io/apimachinery/pkg/api/errors"
    metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
    "k8s.io/apimachinery/pkg/runtime"
    "k8s.io/apimachinery/pkg/types"
    "k8s.io/apimachinery/pkg/util/intstr"
    ctrl "sigs.k8s.io/controller-runtime"
    "sigs.k8s.io/controller-runtime/pkg/client"
    "sigs.k8s.io/controller-runtime/pkg/controller/controllerutil"
    "sigs.k8s.io/controller-runtime/pkg/log"

    webappv1 "github.com/example/webapp-operator/api/v1"
)

type WebAppReconciler struct {
    client.Client
    Scheme *runtime.Scheme
}

// +kubebuilder:rbac:groups=webapp.example.com,resources=webapps,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=webapp.example.com,resources=webapps/status,verbs=get;update;patch
// +kubebuilder:rbac:groups=webapp.example.com,resources=webapps/finalizers,verbs=update
// +kubebuilder:rbac:groups=apps,resources=deployments,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups="",resources=services,verbs=get;list;watch;create;update;patch;delete

func (r *WebAppReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
    logger := log.FromContext(ctx)

    webapp := &webappv1.WebApp{}
    if err := r.Get(ctx, req.NamespacedName, webapp); err != nil {
        if apierrors.IsNotFound(err) {
            return ctrl.Result{}, nil
        }
        return ctrl.Result{}, err
    }

    deploy := &appsv1.Deployment{}
    deployName := types.NamespacedName{Name: webapp.Name, Namespace: webapp.Namespace}
    if err := r.Get(ctx, deployName, deploy); err != nil {
        if !apierrors.IsNotFound(err) {
            return ctrl.Result{}, err
        }

        deploy = r.buildDeployment(webapp)
        if err := ctrl.SetControllerReference(webapp, deploy, r.Scheme); err != nil {
            return ctrl.Result{}, err
        }
        logger.Info("creating Deployment", "name", deploy.Name)
        return ctrl.Result{}, r.Create(ctx, deploy)
    }

    desiredReplicas := int32(1)
    if webapp.Spec.Replicas != nil {
        desiredReplicas = *webapp.Spec.Replicas
    }

    if deploy.Spec.Replicas == nil || *deploy.Spec.Replicas != desiredReplicas ||
        deploy.Spec.Template.Spec.Containers[0].Image != webapp.Spec.Image {
        deploy.Spec.Replicas = &desiredReplicas
        deploy.Spec.Template.Spec.Containers[0].Image = webapp.Spec.Image
        logger.Info("updating Deployment", "name", deploy.Name)
        if err := r.Update(ctx, deploy); err != nil {
            return ctrl.Result{}, err
        }
    }

    svc := &corev1.Service{}
    svcName := types.NamespacedName{Name: webapp.Name, Namespace: webapp.Namespace}
    if err := r.Get(ctx, svcName, svc); err != nil {
        if !apierrors.IsNotFound(err) {
            return ctrl.Result{}, err
        }

        svc = r.buildService(webapp)
        if err := ctrl.SetControllerReference(webapp, svc, r.Scheme); err != nil {
            return ctrl.Result{}, err
        }
        logger.Info("creating Service", "name", svc.Name)
        return ctrl.Result{}, r.Create(ctx, svc)
    }

    webapp.Status.AvailableReplicas = deploy.Status.AvailableReplicas
    webapp.Status.ObservedGeneration = webapp.Generation
    if err := r.Status().Update(ctx, webapp); err != nil {
        return ctrl.Result{}, err
    }

    return ctrl.Result{}, nil
}

func (r *WebAppReconciler) buildDeployment(app *webappv1.WebApp) *appsv1.Deployment {
    replicas := int32(1)
    if app.Spec.Replicas != nil {
        replicas = *app.Spec.Replicas
    }

    labels := map[string]string{"app.kubernetes.io/name": app.Name, "app.kubernetes.io/managed-by": "webapp-operator"}
    return &appsv1.Deployment{
        ObjectMeta: metav1.ObjectMeta{
            Name:      app.Name,
            Namespace: app.Namespace,
            Labels:    labels,
        },
        Spec: appsv1.DeploymentSpec{
            Replicas: &replicas,
            Selector: &metav1.LabelSelector{MatchLabels: labels},
            Template: corev1.PodTemplateSpec{
                ObjectMeta: metav1.ObjectMeta{Labels: labels},
                Spec: corev1.PodSpec{
                    Containers: []corev1.Container{{
                        Name:  "app",
                        Image: app.Spec.Image,
                        Ports: []corev1.ContainerPort{{
                            ContainerPort: app.Spec.Port,
                        }},
                    }},
                },
            },
        },
    }
}

func (r *WebAppReconciler) buildService(app *webappv1.WebApp) *corev1.Service {
    return &corev1.Service{
        ObjectMeta: metav1.ObjectMeta{
            Name:      app.Name,
            Namespace: app.Namespace,
        },
        Spec: corev1.ServiceSpec{
            Selector: map[string]string{"app.kubernetes.io/name": app.Name},
            Ports: []corev1.ServicePort{{
                Port:       80,
                TargetPort: intstr.FromInt32(app.Spec.Port),
            }},
        },
    }
}

func (r *WebAppReconciler) SetupWithManager(mgr ctrl.Manager) error {
    return ctrl.NewControllerManagedBy(mgr).
        For(&webappv1.WebApp{}).
        Owns(&appsv1.Deployment{}).
        Owns(&corev1.Service{}).
        Complete(r)
}
```

The code has three production lessons hidden in a small example. First, `SetControllerReference` matters because it marks the Deployment and Service as controlled by the `WebApp`, enabling Kubernetes garbage collection and controller-runtime owner mapping. Second, the reconciler compares before updating; this prevents unnecessary writes and avoids turning its own updates into a constant source of new work. Third, status is updated through `r.Status().Update`, not through an ordinary spec update, because status is a separate controller-owned channel.

The example is still intentionally incomplete for serious production use. It does not preserve user-managed annotations on children, it does not patch status conditions with conflict retries, it does not handle every Service field drift, and it does not implement finalizer cleanup because all children are Kubernetes-owned objects. That is normal for a teaching controller. The important habit is to identify which behavior belongs in the sample and which behavior would need design before a real platform team promised this API to users.

---

## Finalizers, Status, And Conditions

Finalizers are easiest to design before you write any code. Ask one question for every object or external resource the controller creates: can Kubernetes garbage collection clean this up by following owner references? If yes, prefer owner references. If no, the controller may need a finalizer. A cloud DNS record, external database, backup bucket, or license allocation is invisible to Kubernetes garbage collection, so deletion of the parent custom resource must pause until the controller confirms that external state is removed or intentionally retained.

A correct finalizer flow is mechanical. During normal reconciliation, if the object is not being deleted and the finalizer is missing, add the finalizer. During deletion, if the deletion timestamp is set and the finalizer is present, run cleanup. Cleanup must be idempotent because it may run more than once. If the external resource is already gone, treat that as success. Only after cleanup is complete should the controller remove its finalizer. If cleanup fails, return an error or a timed requeue and write a condition explaining the block.

Status should make that lifecycle understandable. A user should not have to read controller logs to know that deletion is waiting for an external cleanup request, or that a reconcile has not processed the latest spec generation yet. For long-running resources, set a top-level condition such as `Ready` and use reasons that are stable enough for automation but specific enough for people. A message like "Deployment has no available replicas" is more useful than "failed." Pair conditions with `observedGeneration` so callers can distinguish a real failure on the latest spec from an old condition left over from a previous generation.

Conditions should not become a second spec. Avoid using status as an input that users must edit to make progress. The controller owns status, and users own spec. If the user needs to request a behavior, put it in spec. If the controller has observed a fact, put it in status. This boundary is especially important when GitOps is involved. GitOps tools usually apply desired state to spec and metadata; they should not be forced to fight a controller over status fields or infer readiness from logs.

---

## RBAC, Webhooks, Metrics, And Leader Election

RBAC markers are part of your controller's security boundary. The generated manager Pod runs under a Kubernetes ServiceAccount, and that ServiceAccount receives permissions from generated Role or ClusterRole manifests. A controller that reads `WebApp` objects, writes `WebApp` status, updates finalizers, and manages Deployments and Services needs exactly those verbs on exactly those resources. Overly broad RBAC can turn a controller bug into a cluster-wide incident. Under-specified RBAC will show up as authorization errors at runtime, often during the first reconcile that tries to create or update a child object.

Webhooks should be used where admission-time behavior improves the API contract. Defaulting webhooks can set fields that are too dynamic for static schema defaults. Validating webhooks can reject combinations that OpenAPI schema cannot express clearly. Conversion webhooks are necessary when a CRD serves multiple versions and objects must round-trip between them. The trap is to put long-running checks into admission. Admission should be fast and deterministic. If the answer depends on a cloud API that may time out or on child resources that may not exist yet, put that logic in reconciliation and report it through status.

Metrics and health probes are not optional decoration in a production operator. The generated manager usually exposes health and readiness endpoints so Kubernetes can restart or gate traffic to the manager process. It also exposes metrics for controller-runtime and custom instrumentation. At minimum, platform teams should watch reconcile error rates, queue depth or latency where available, workqueue retries, webhook errors, and process health. Good status helps users understand one object. Good metrics help operators understand whether the controller itself is healthy.

Leader election matters when you run more than one replica of the manager. Without coordination, two manager Pods could reconcile the same resource at the same time, racing on writes or duplicating external side effects. controller-runtime can use Kubernetes leader election so only the elected instance runs leader-elected controllers at a time. You still write idempotent reconcilers, because leadership can change and duplicate work can occur around failures, but leader election reduces unnecessary concurrency for controllers that are meant to have one active worker set.

---

## Testing With envtest

Kubebuilder's generated test setup commonly uses controller-runtime `envtest`, which starts a real Kubernetes API server and etcd locally for tests. That matters because many operator bugs live at the API boundary: schema validation, status subresources, object encoding, owner references, client behavior, and watches. A fake client can be useful for isolated helper tests, but it will not behave exactly like the API server. envtest gives you stronger feedback without requiring a full cluster for every controller test.

The first useful test for this example is not a unit test of every helper. It is a behavior test: when a `WebApp` custom resource exists, the controller should create a Deployment and Service that match the spec. The test writes the parent object through the Kubernetes client, waits until the child Deployment appears, checks the expected fields, then waits for the Service. The waiting pattern is important because controllers are asynchronous. A test that assumes child objects appear immediately will be flaky even if the controller is correct.

```go
var _ = Describe("WebApp Controller", func() {
    const (
        WebAppName      = "test-webapp"
        WebAppNamespace = "default"
        WebAppImage     = "nginx:1.25"
    )

    ctx := context.Background()

    It("creates a Deployment and Service for a new WebApp", func() {
        replicas := int32(2)
        webapp := &webappv1.WebApp{
            ObjectMeta: metav1.ObjectMeta{
                Name:      WebAppName,
                Namespace: WebAppNamespace,
            },
            Spec: webappv1.WebAppSpec{
                Image:    WebAppImage,
                Replicas: &replicas,
                Port:     8080,
            },
        }

        Expect(k8sClient.Create(ctx, webapp)).To(Succeed())

        deploy := &appsv1.Deployment{}
        Eventually(func() error {
            return k8sClient.Get(ctx, types.NamespacedName{
                Name: WebAppName, Namespace: WebAppNamespace,
            }, deploy)
        }, "10s", "1s").Should(Succeed())

        Expect(*deploy.Spec.Replicas).To(Equal(int32(2)))
        Expect(deploy.Spec.Template.Spec.Containers[0].Image).To(Equal(WebAppImage))

        svc := &corev1.Service{}
        Eventually(func() error {
            return k8sClient.Get(ctx, types.NamespacedName{
                Name: WebAppName, Namespace: WebAppNamespace,
            }, svc)
        }, "10s", "1s").Should(Succeed())

        Expect(svc.Spec.Ports[0].Port).To(Equal(int32(80)))
    })
})
```

Run the generated test target after adding the controller behavior. Depending on the scaffold, the Makefile may download or locate the API server and etcd binaries used by envtest. If tests fail before your reconcile code runs, check envtest binary setup and CRD installation in the test suite before debugging business logic.

```bash
make test
```

Add tests around failure and drift, not only creation. A useful second test updates the `WebApp` image and waits for the Deployment image to change. A useful third test deletes the child Deployment and waits for the controller to recreate it. A useful finalizer test sets a deletion timestamp path indirectly by deleting the parent and asserting cleanup behavior. These tests teach the real contract: reconciliation is continuous, not a create handler.

---

## Operator Packaging And Deployment

A Kubebuilder project usually packages the controller manager as a container image and deploys it with Kustomize manifests from `config/default`. The generated Makefile gives you targets for installing CRDs, building and pushing the image, and deploying the manager. Treat these targets as a development workflow, not as a substitute for release engineering. Production operators still need image provenance, dependency updates, RBAC review, upgrade notes, rollback plans, and compatibility testing against the Kubernetes versions you support.

```bash
make docker-build IMG=registry.example.com/platform/webapp-operator:v0.1.0
make docker-push IMG=registry.example.com/platform/webapp-operator:v0.1.0
make install
make deploy IMG=registry.example.com/platform/webapp-operator:v0.1.0
```

After deployment, verify that the manager Pod is running and that the CRD exists before applying a custom resource. This separates packaging problems from controller logic problems. If the manager is not running, inspect the Deployment, ServiceAccount, RBAC, image pull, and logs. If the CRD is missing, inspect `make install` and the generated CRD manifests. If the CRD exists and the manager runs but no child objects appear, inspect watches, RBAC, reconcile errors, and status conditions.

```bash
kubectl get crd webapps.webapp.example.com
kubectl get pods -n webapp-operator-system
kubectl logs -n webapp-operator-system deployment/webapp-operator-controller-manager
```

Apply a sample resource only after the API and manager are present. The sample is deliberately ordinary YAML because that is the user experience you are creating. A good operator should not require users to know which Deployment or Service objects it will create internally before they can request the application they want.

```yaml
apiVersion: webapp.example.com/v1
kind: WebApp
metadata:
  name: my-app
  namespace: default
spec:
  image: nginx:1.25
  replicas: 3
  port: 80
```

```bash
kubectl apply -f webapp.yaml
kubectl get webapp my-app
kubectl get deployment my-app
kubectl get service my-app
```

Self-healing is the simplest live demonstration of reconciliation. Delete the child Deployment and watch the controller recreate it because the parent `WebApp` still declares that the application should exist. This is not a trick; it is the contract. If you do not want users to edit or delete children directly, document that children are controller-owned and use labels, owner references, and admission policy where appropriate to reduce accidental edits.

```bash
kubectl delete deployment my-app
kubectl get deployment my-app --watch
```

---

## Current Landscape

Kubebuilder, Operator SDK, and Metacontroller all help teams implement controllers, but they sit at different layers of abstraction. Kubebuilder is a Go-first scaffolding toolkit for building Kubernetes APIs and controllers with controller-runtime. Operator SDK adds operator packaging workflows and supports Go, Helm, and Ansible styles, with strong ties to Operator Lifecycle Manager workflows. Metacontroller lets you define controller behavior around webhook hooks, so the reconciliation decision can be written in another language while Metacontroller handles much of the watch and child-management machinery.

The durable comparison is not "which tool wins." The durable comparison is where each tool asks you to place your API, reconcile logic, packaging, and operational responsibility. If your team needs full Go control over API types, watches, patches, webhooks, and test structure, Kubebuilder is a direct path. If your team is packaging for an Operator Lifecycle Manager environment or wants SDK workflows around Helm or Ansible operators, Operator SDK changes the surrounding workflow. If your team wants a lightweight parent-child controller without owning a full Go controller-runtime binary, Metacontroller changes the programming model by moving custom logic behind hooks.

| Capability | Kubebuilder | Operator SDK | Metacontroller |
|------------|-------------|--------------|----------------|
| Primary programming model | Go API types plus controller-runtime Reconciler | Go controller-runtime, Helm, or Ansible operator workflows | Webhook hooks for sync, finalize, and customization |
| CRD schema generation | Go types and Kubebuilder/controller-tools markers | Go projects use similar marker-driven generation; Helm and Ansible workflows differ | You bring CRDs and hook contracts; Metacontroller manages controller resources |
| Reconcile ownership | Your Go reconciler owns the loop directly | Depends on operator type; Go operators expose the loop directly | Metacontroller owns watch mechanics and calls your hook |
| Packaging emphasis | Kustomize manifests and manager image from scaffold | SDK workflow includes bundle and OLM-oriented commands | Install Metacontroller plus CompositeController or DecoratorController definitions |
| Webhooks | Generated webhook scaffolding for defaulting, validation, and conversion | Available in Go-based operators through controller-runtime patterns | Your hook server is the main extension point |
| Testing style | Go tests, envtest, controller-runtime clients | Go operators can use envtest; other operator types use their own checks | Test hook request and response behavior plus cluster integration |
| Good fit signal | Team wants direct Go control of a custom Kubernetes API | Team wants SDK packaging workflows or non-Go operator styles | Team wants webhook-driven child reconciliation with less custom controller code |

This Rosetta table should help you translate vocabulary. "Reconcile" in Kubebuilder usually means a Go method on your Reconciler. In Operator SDK Go projects, the same controller-runtime vocabulary appears because the Go path uses the same underlying libraries. In Metacontroller, the comparable decision point is the sync hook response: based on observed parent and child state, your hook returns desired child state. The tools differ, but the control-loop idea remains recognizable.

---

## Best Practices

Design the API before optimizing the controller. A rushed CRD can lock users into confusing field names, ambiguous ownership, and invalid states that are hard to deprecate. Write sample manifests first, explain each field in plain language, decide which fields are immutable, decide which defaults are safe, and define the status conditions a user will need during rollout and failure. Once the contract is clear, scaffolding the project is straightforward.

Keep reconciliation boring. Boring means idempotent, level-triggered, small-step, and observable. The reconciler should compare desired and observed state, make the smallest necessary change, and return. If it must call an external API, store enough information to avoid duplicate side effects. If it must wait, report why in status. If it must retry, let the queue and backoff help you. Clever event-specific shortcuts usually fail during restarts, cache lag, duplicate events, or partial previous writes.

Use server-side API machinery where it fits. CRD schema validation is better than accepting invalid spec and later reporting a controller error. Status subresources are better than mixing observed state with desired state. Owner references are better than hand-written child cleanup for same-namespace Kubernetes dependents. Finalizers are better than hoping an external resource disappears after the parent object is gone. RBAC markers are better than manually drifting permissions away from code.

Patch carefully and preserve user intent. If users are allowed to add annotations or labels to child objects, do not overwrite the whole object from a template on every reconcile. Use merge or server-side apply patterns that make ownership clear. Compare before writing so the controller does not generate unnecessary events. Be especially careful with fields that other controllers also own, such as Deployment status, Pod template defaults, Service cluster IPs, and annotations added by admission controllers.

Make status and metrics part of the first implementation, not a cleanup task. A controller that silently retries is painful to operate. A controller that reports `Ready=False` with a reason, message, and observed generation gives users a place to start. Metrics tell the platform team whether the controller is falling behind or failing broadly. Logs are still useful, but logs should explain details after status and metrics have already pointed you to the problem.

---

## Anti-Patterns

| Anti-Pattern | Why It's Bad | Better Approach |
|--------------|--------------|-----------------|
| Event-story reconciliation | Missed, duplicated, or collapsed events break logic that depends on exact event history | Read current desired and observed state every time |
| Spec mutation from the controller | The controller fights users and GitOps over desired state ownership | Use schema defaults, admission defaulting, or status fields |
| Status as a single vague phase | Users cannot tell which part is blocked or whether status reflects the latest spec | Use standard conditions with reasons, messages, and observed generation |
| External delete without a finalizer | Parent object can disappear before cleanup completes | Add a finalizer and make cleanup idempotent |
| Broad RBAC markers | A controller bug gets unnecessary power across the cluster | Generate least-privilege rules from reviewed markers |
| Full-object child overwrites | User or admission-managed fields are accidentally removed | Patch only fields the controller owns and compare before writing |
| Cache-blind assumptions | Immediate reads after writes may be stale, causing false failures or duplicate actions | Design for eventual cache consistency and use direct reads only deliberately |
| Tool-first API design | The scaffold shapes the product contract instead of user needs | Design manifests, validation, and status before committing to code shape |

---

## Did You Know?

- **A CRD alone is not an operator**: Kubernetes can store custom resources without any controller, but the declarative behavior appears only when a controller watches those resources and acts on them.
- **Status updates have separate permissions**: The status subresource lets a controller update observed state without needing to rewrite user-owned spec fields through the same API operation.
- **Owner references and finalizers solve different cleanup problems**: Owner references connect Kubernetes-visible dependents to a parent, while finalizers delay deletion so a controller can perform ordered or external cleanup.
- **A Reconcile request is intentionally small**: controller-runtime usually gives the reconciler a namespace and name, pushing the controller to load current state rather than rely on stale event payload assumptions.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Treating Kubebuilder as the pattern | Learners memorize generated files but cannot reason about reconciliation | Teach CRD desired state plus controller convergence first, then map it to the scaffold |
| Updating status on every pass | The controller creates noisy writes and may trigger avoidable reconciles | Compare status before writing and use predicates where appropriate |
| Forgetting `webapps/status` RBAC | The controller can read the parent but fails when reporting observed state | Add status RBAC markers and regenerate manifests |
| Using finalizers for ordinary child objects | Cleanup logic duplicates what Kubernetes garbage collection already does | Use owner references for Kubernetes dependents and reserve finalizers for ordered or external cleanup |
| Assuming cache reads are strongly current | Reconcile code can misinterpret normal watch lag as failed writes | Write idempotent logic and tolerate eventual cache convergence |
| Hiding every error in logs only | Users cannot understand object-level readiness through Kubernetes APIs | Write meaningful conditions and observed generation into status |
| Recreating children from scratch | Rollouts become disruptive and user-managed fields disappear | Patch changed fields and preserve fields owned by other actors |
| Publishing an unversioned mental model | Future API changes become breaking changes because compatibility was not planned | Use group/version discipline and design conversion before serving multiple versions |

---

## Quiz

### Question 1

Your team created a CRD named `Database`, but no controller watches it yet. A user applies a `Database` object and expects a StatefulSet to appear. What actually happens, and what is missing?

<details>
<summary>Show Answer</summary>

The Kubernetes API server stores and serves the `Database` object if the CRD schema accepts it, but no StatefulSet appears automatically. A CRD adds an API endpoint and schema; it does not implement behavior by itself. The missing half is a controller that watches `Database` objects, reads desired state from `spec`, creates or updates the required children, and writes observed state into `status`.

</details>

### Question 2

A reconciler receives an update event for a `WebApp`. Why should it read the current `WebApp`, Deployment, and Service instead of branching primarily on the event type?

<details>
<summary>Show Answer</summary>

Controller events are efficient hints, not a reliable event-sourcing log. Events can be duplicated, collapsed in the work queue, missed during downtime, or followed by additional changes before the reconciler runs. A level-triggered reconciler reads current desired and observed state, then makes the smallest safe change needed for convergence. That design survives restarts, stale cache reads, child drift, and manual edits better than event-story logic.

</details>

### Question 3

When should a controller use an owner reference, and when should it use a finalizer?

<details>
<summary>Show Answer</summary>

Use an owner reference when a Kubernetes object is a dependent child of a parent object and Kubernetes garbage collection can safely remove it after the parent is deleted. Use a finalizer when deletion must pause for controller-managed cleanup, especially for ordered teardown or external resources that Kubernetes garbage collection cannot see. Many operators use both: owner references for in-cluster children and finalizers for external cleanup.

</details>

### Question 4

A controller updates `status.availableReplicas`, but users still see an old `Ready=False` condition from a previous spec change. What field or convention helps consumers know whether status reflects the latest desired state?

<details>
<summary>Show Answer</summary>

Use observed generation. The controller can set `status.observedGeneration` to the parent object's `metadata.generation` after processing the latest spec, and individual conditions can also include `observedGeneration`. Consumers can compare condition observed generation with the object's current generation. If the condition was written for an older generation, it may not describe the current spec.

</details>

### Question 5

Why does a controller-runtime Manager matter in a Kubebuilder project?

<details>
<summary>Show Answer</summary>

The Manager is the shared runtime that starts controllers and provides common dependencies such as the client, cache, scheme, REST mapper, metrics, health probes, webhook server, and leader election integration. Kubebuilder scaffolds `cmd/main.go` around Manager setup so reconcilers can be registered consistently and run inside one managed process.

</details>

### Question 6

Your `WebApp` controller can create Deployments, but every status update fails with `forbidden`. Which part of the Kubebuilder project should you inspect first?

<details>
<summary>Show Answer</summary>

Inspect the RBAC markers and generated manifests. Status updates require permission on the status subresource, such as `resources=webapps/status,verbs=get;update;patch`. If the marker is missing or manifests were not regenerated with `make manifests`, the manager ServiceAccount may have permission to read the parent resource but not to update its status.

</details>

### Question 7

How would you explain the difference between Kubebuilder, Operator SDK, and Metacontroller without making a best-tool claim?

<details>
<summary>Show Answer</summary>

Describe where each tool places the controller logic and workflow. Kubebuilder scaffolds Go APIs and controller-runtime reconcilers directly. Operator SDK provides operator workflows that include Go-based operators and additional styles such as Helm or Ansible, plus packaging commands often used with OLM. Metacontroller runs controller machinery that calls webhook hooks for sync and finalize behavior. The right comparison is capability and responsibility, not popularity or universal superiority.

</details>

---

## Hands-On Exercise

### Objective

Scaffold a Kubebuilder project, implement the WebApp operator, test it with envtest, and run it against a local kind cluster. Keep the exercise focused on the control-loop behavior: a `WebApp` custom resource should produce a Deployment and Service, and deleting the child Deployment should cause the controller to recreate it.

### Environment Setup

```bash
# Prerequisites: Go, Docker, kind, kubectl, and Kubebuilder.
kind create cluster --name operator-lab

curl -L -o kubebuilder "https://go.kubebuilder.io/dl/latest/$(go env GOOS)/$(go env GOARCH)"
chmod +x kubebuilder
sudo mv kubebuilder /usr/local/bin/
```

### Tasks

1. **Scaffold the project**:
   ```bash
   mkdir webapp-operator
   cd webapp-operator
   kubebuilder init --domain example.com --repo github.com/example/webapp-operator
   kubebuilder create api --group webapp --version v1 --kind WebApp
   ```

2. **Define the API**: Edit `api/v1/webapp_types.go` with the WebAppSpec and WebAppStatus structs from this module. Run `make manifests generate` and inspect the generated CRD before deploying it.

3. **Implement the controller**: Edit `internal/controller/webapp_controller.go` with the reconcile logic from this module. Confirm that RBAC markers include the parent resource, status subresource, finalizers subresource, Deployments, and Services.

4. **Run tests**:
   ```bash
   make test
   ```

5. **Install CRDs and run locally**:
   ```bash
   make install
   make run
   ```

6. **Apply a WebApp resource in another terminal**:
   ```bash
   kubectl apply -f - <<EOF
   apiVersion: webapp.example.com/v1
   kind: WebApp
   metadata:
     name: test-app
   spec:
     image: nginx:1.25
     replicas: 2
     port: 80
   EOF
   ```

7. **Verify the operator works**:
   ```bash
   kubectl get webapp test-app
   kubectl get deployment test-app
   kubectl get service test-app
   ```

8. **Test self-healing**:
   ```bash
   kubectl delete deployment test-app
   kubectl get deployment test-app --watch
   ```

### Success Criteria

- [ ] Kubebuilder project scaffolded and compiles
- [ ] CRD installed in cluster: `kubectl get crd webapps.webapp.example.com`
- [ ] Creating a WebApp produces a Deployment and Service
- [ ] Deleting the Deployment triggers the controller to recreate it
- [ ] `make test` passes with envtest
- [ ] Status reports available replicas and an observed generation

### Bonus Challenge

Add a `serviceType` field to the WebApp spec with an enum that allows `ClusterIP` and `NodePort`. Make the controller set the Service type from that field, preserve existing Service fields it does not own, and write an envtest case that updates the custom resource and waits for the Service type to change.

---

## Cross-References

- **CRD Foundations**: [CKA Module 1.5: CRDs and Operators](/k8s/cka/part1-cluster-architecture/module-1.5-crds-operators/) covers the Kubernetes extension mechanics that operators build on.
- **Operator in the Wild**: [Module 15.5: etcd-operator](/platform/toolkits/data-ai-platforms/cloud-native-databases/module-15.5-etcd-operator/) shows a production operator managing a distributed database.
- **Declarative Infrastructure**: [Module 7.2: Crossplane](../module-7.2-crossplane/) uses the same controller-runtime reconciliation pattern, but for cloud resources instead of in-cluster workloads.

---

## Sources

- [Kubebuilder Book](https://book.kubebuilder.io/)
- [Kubebuilder GitHub repository](https://github.com/kubernetes-sigs/kubebuilder)
- [Kubebuilder releases](https://github.com/kubernetes-sigs/kubebuilder/releases)
- [Kubebuilder controller overview](https://book.kubebuilder.io/cronjob-tutorial/controller-overview.html)
- [Kubebuilder API type markers](https://book.kubebuilder.io/cronjob-tutorial/new-api)
- [Kubebuilder object marker reference](https://book.kubebuilder.io/reference/markers/object)
- [Kubebuilder RBAC marker reference](https://book.kubebuilder.io/reference/markers/rbac)
- [Kubebuilder CRD validation marker reference](https://book.kubebuilder.io/reference/markers/crd-validation)
- [Kubebuilder good practices](https://book.kubebuilder.io/reference/good-practices.html)
- [controller-runtime package documentation](https://pkg.go.dev/sigs.k8s.io/controller-runtime)
- [controller-runtime reconcile package](https://pkg.go.dev/sigs.k8s.io/controller-runtime/pkg/reconcile)
- [controller-runtime manager package](https://pkg.go.dev/sigs.k8s.io/controller-runtime/pkg/manager)
- [controller-runtime client package](https://pkg.go.dev/sigs.k8s.io/controller-runtime/pkg/client)
- [controller-runtime cache package](https://pkg.go.dev/sigs.k8s.io/controller-runtime/pkg/cache)
- [controller-runtime controllerutil package](https://pkg.go.dev/sigs.k8s.io/controller-runtime/pkg/controller/controllerutil)
- [Kubernetes Operator pattern](https://kubernetes.io/docs/concepts/extend-kubernetes/operator/)
- [Kubernetes Custom Resources](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/)
- [Kubernetes API concepts](https://kubernetes.io/docs/reference/using-api/api-concepts/)
- [Kubernetes owners and dependents](https://kubernetes.io/docs/concepts/overview/working-with-objects/owners-dependents/)
- [Kubernetes finalizers](https://kubernetes.io/docs/concepts/overview/working-with-objects/finalizers/)
- [Kubernetes API conventions](https://github.com/kubernetes/community/blob/main/contributors/devel/sig-architecture/api-conventions.md)
- [Operator SDK Go quickstart](https://sdk.operatorframework.io/docs/building-operators/golang/quickstart/)
- [Metacontroller CompositeController API](https://metacontroller.github.io/metacontroller/api/compositecontroller.html)
- [Metacontroller DecoratorController API](https://metacontroller.github.io/metacontroller/api/decoratorcontroller.html)

---

## Next Module

Continue to the next module in the Platforms Toolkit to expand your platform engineering skills.

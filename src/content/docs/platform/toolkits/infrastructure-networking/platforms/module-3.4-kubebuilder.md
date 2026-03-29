---
title: "Module 3.4: Kubebuilder - Building Kubernetes Operators"
slug: platform/toolkits/infrastructure-networking/platforms/module-3.4-kubebuilder
sidebar:
  order: 5
---
> **Toolkit Track** | Complexity: `[COMPLEX]` | Time: ~55 minutes

## Overview

A fintech team ran 200+ PostgreSQL instances across three cloud providers. Every failover, backup rotation, and version upgrade was a manual runbook -- 47 pages of copy-paste commands executed by on-call engineers at 3 AM. One night, a junior engineer ran the failover steps out of order and brought down the payment processing pipeline for 11 hours. Cost: $2.3 million in lost transactions and an SEC inquiry. Three months later, they had a Kubernetes operator that encoded every runbook step into a reconciliation loop. Failovers became self-healing. Upgrades became a one-line spec change. The 47-page runbook became 400 lines of Go. That operator was built with Kubebuilder.

**What You'll Learn**:
- Why operators exist and what problems they solve
- Kubebuilder project scaffolding and structure
- Controller-runtime internals: reconcile loop, cache, event handling
- Building a complete WebApp operator from scratch
- Testing operators with envtest
- Packaging and deploying operators

**Prerequisites**:
- [CKA Module 1.5: CRDs and Operators](../../../k8s/cka/part1-cluster-architecture/module-1.5-crds-operators/)
- Go programming basics (structs, interfaces, error handling)
- Familiarity with `kubectl` and YAML manifests

---

## Why This Module Matters

Kubernetes gives you primitives: Pods, Deployments, Services. But your business has domain-specific concepts: "a production database with read replicas, automated backups, and failover." Operators bridge that gap. They encode your operational knowledge as code -- turning tribal knowledge and runbooks into a control loop that never sleeps, never forgets a step, and never fat-fingers a command.

Kubebuilder is the official SDK for building operators in Go. It generates the boilerplate so you can focus on the logic that matters: your domain expertise.

> **Did You Know?**
> - Kubebuilder is maintained by the Kubernetes SIG API Machinery team -- the same people who design the Kubernetes API itself. It is the upstream foundation that Operator SDK builds on top of.
> - The controller-runtime library (which Kubebuilder uses) powers over 500 open-source operators, including Istio, Knative, and Cluster API. If you learn it once, you can read the source code of almost any major Kubernetes project.
> - A single reconciliation loop can replace thousands of lines of bash scripts. The etcd-operator (see [Module 15.5](../../toolkits/data-ai-platforms/cloud-native-databases/module-15.5-etcd-operator/)) reduced cluster management from a multi-day manual process to a single CRD apply.
> - Kubebuilder v4 (current) generates projects that conform to the Kubernetes API conventions document, meaning your CRDs behave exactly like built-in resources -- including strategic merge patch, server-side apply, and proper status subresources.

---

## Why Build Operators

Manual operations do not scale. Here is the progression every team goes through:

```
OPERATIONAL MATURITY LADDER
================================================================

Level 1: RUNBOOKS
  "Read page 12, run these 6 commands in order"
  Problem: Humans make mistakes at 3 AM

Level 2: SCRIPTS
  "Run ./failover.sh --cluster prod-east"
  Problem: No feedback loop, no self-healing

Level 3: CI/CD PIPELINES
  "Merge to trigger database upgrade pipeline"
  Problem: One-shot execution, no continuous reconciliation

Level 4: OPERATORS
  "Declare desired state, controller makes it so"
  Benefit: Continuous, self-healing, domain-aware

================================================================
Operators encode operational knowledge as code.
They watch, compare, and act -- forever.
```

An operator turns imperative runbooks into declarative intent. Instead of "run these 12 steps to create a database with replicas," you write:

```yaml
apiVersion: webapp.example.com/v1
kind: WebApp
spec:
  replicas: 3
  image: myapp:v2
```

The operator figures out the rest.

---

## Controller-Runtime Architecture

Before writing code, understand the machinery your operator runs on:

```
CONTROLLER-RUNTIME RECONCILE LOOP
================================================================

  ┌──────────────────────────────────────────────────────┐
  │                   INFORMER / CACHE                    │
  │  Watches API server, maintains local cached copy      │
  │  of all objects this controller cares about            │
  └──────────┬────────────────────────────┬───────────────┘
             │ Event: Create/Update/Delete │
             ▼                             │
  ┌─────────────────────┐                 │
  │   EVENT HANDLERS    │                 │
  │                     │                 │
  │  Filter events via  │                 │
  │  PREDICATES:        │                 │
  │  - GenerationChanged│                 │
  │  - Label matches    │                 │
  └─────────┬───────────┘                 │
            │ Enqueue Request              │
            ▼                              │
  ┌─────────────────────┐                 │
  │    WORK QUEUE       │                 │
  │  (deduplicated)     │                 │
  │  namespace/name     │                 │
  └─────────┬───────────┘                 │
            │                              │
            ▼                              │
  ┌─────────────────────┐                 │
  │  RECONCILE(req)     │    ┌──────────┐ │
  │                     │───▶│  CLIENT  │─┘
  │  1. Get current     │    │  (reads  │
  │  2. Compare desired │    │  from    │
  │  3. Create/Update   │    │  cache,  │
  │  4. Update status   │    │  writes  │
  │  5. Return result   │    │  to API  │
  │                     │    │  server) │
  └─────────────────────┘    └──────────┘

  Return values:
    ctrl.Result{}              → Done, wait for next event
    ctrl.Result{Requeue: true} → Retry immediately
    ctrl.Result{RequeueAfter:} → Retry after duration
    error                      → Retry with backoff

================================================================
```

Key concepts:
- **Cache**: Local in-memory copy of watched resources. Reads are fast (no API server round-trip). Writes always go to the API server.
- **Client**: Reads from cache, writes to API server. You never talk to etcd directly.
- **Work Queue**: Deduplicates events. If 10 events fire for the same object, you reconcile once.
- **Predicates**: Filters that prevent unnecessary reconciliations (e.g., ignore status-only updates).

---

## Kubebuilder Scaffolding Walkthrough

### Step 1: Initialize the Project

```bash
# Install kubebuilder (requires Go 1.21+)
# Download from https://kubebuilder.io or:
curl -L -o kubebuilder "https://go.kubebuilder.io/dl/latest/$(go env GOOS)/$(go env GOARCH)"
chmod +x kubebuilder && sudo mv kubebuilder /usr/local/bin/

# Create project directory
mkdir webapp-operator && cd webapp-operator

# Initialize the project
kubebuilder init --domain example.com --repo github.com/example/webapp-operator
```

This generates:
```
webapp-operator/
├── cmd/main.go              # Entry point, sets up manager
├── config/                  # Kustomize manifests for deployment
│   ├── default/             # Default configuration
│   ├── manager/             # Controller manager deployment
│   ├── rbac/                # RBAC rules (auto-generated)
│   └── crd/                 # CRD manifests (after API creation)
├── internal/controller/     # Your controller logic goes here
├── api/                     # Your API types go here
├── Dockerfile               # Multi-stage build
├── Makefile                 # Build, test, deploy targets
└── go.mod
```

### Step 2: Create the API and Controller

```bash
kubebuilder create api --group webapp --version v1 --kind WebApp
# Answer "y" to both "Create Resource" and "Create Controller"
```

This scaffolds two critical files:
- `api/v1/webapp_types.go` -- Your CRD struct definition
- `internal/controller/webapp_controller.go` -- Your reconcile logic

---

## Build a WebApp Operator

### API Type Definition

Edit `api/v1/webapp_types.go` to define what a WebApp looks like:

```go
package v1

import (
    metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// WebAppSpec defines the desired state of WebApp
type WebAppSpec struct {
    // Image is the container image to deploy
    // +kubebuilder:validation:Required
    Image string `json:"image"`

    // Replicas is the number of desired pods
    // +kubebuilder:default=1
    // +kubebuilder:validation:Minimum=1
    // +kubebuilder:validation:Maximum=10
    Replicas *int32 `json:"replicas,omitempty"`

    // Port is the container port to expose via Service
    // +kubebuilder:default=8080
    // +kubebuilder:validation:Minimum=1
    // +kubebuilder:validation:Maximum=65535
    Port int32 `json:"port,omitempty"`
}

// WebAppStatus defines the observed state of WebApp
type WebAppStatus struct {
    // AvailableReplicas is the number of ready pods
    AvailableReplicas int32 `json:"availableReplicas,omitempty"`

    // Conditions represent the latest observations
    // +optional
    Conditions []metav1.Condition `json:"conditions,omitempty"`
}

// +kubebuilder:object:root=true
// +kubebuilder:subresource:status
// +kubebuilder:printcolumn:name="Image",type=string,JSONPath=`.spec.image`
// +kubebuilder:printcolumn:name="Replicas",type=integer,JSONPath=`.spec.replicas`
// +kubebuilder:printcolumn:name="Available",type=integer,JSONPath=`.status.availableReplicas`
// +kubebuilder:printcolumn:name="Age",type="date",JSONPath=".metadata.creationTimestamp"

// WebApp is the Schema for the webapps API
type WebApp struct {
    metav1.TypeMeta   `json:",inline"`
    metav1.ObjectMeta `json:"metadata,omitempty"`

    Spec   WebAppSpec   `json:"spec,omitempty"`
    Status WebAppStatus `json:"status,omitempty"`
}

// +kubebuilder:object:root=true

// WebAppList contains a list of WebApp
type WebAppList struct {
    metav1.TypeMeta `json:",inline"`
    metav1.ListMeta `json:"metadata,omitempty"`
    Items           []WebApp `json:"items"`
}

func init() {
    SchemeBuilder.Register(&WebApp{}, &WebAppList{})
}
```

The `+kubebuilder` comment markers generate OpenAPI validation, print columns, and the status subresource. After editing, regenerate manifests:

```bash
make manifests  # Generates CRD YAML from Go types
make generate   # Generates DeepCopy methods
```

### Controller Reconcile Function

Edit `internal/controller/webapp_controller.go`:

```go
package controller

import (
    "context"

    appsv1 "k8s.io/api/apps/v1"
    corev1 "k8s.io/api/core/v1"
    "k8s.io/apimachinery/pkg/api/errors"
    metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
    "k8s.io/apimachinery/pkg/runtime"
    "k8s.io/apimachinery/pkg/types"
    "k8s.io/apimachinery/pkg/util/intstr"
    ctrl "sigs.k8s.io/controller-runtime"
    "sigs.k8s.io/controller-runtime/pkg/client"
    "sigs.k8s.io/controller-runtime/pkg/log"

    webappv1 "github.com/example/webapp-operator/api/v1"
)

type WebAppReconciler struct {
    client.Client
    Scheme *runtime.Scheme
}

// +kubebuilder:rbac:groups=webapp.example.com,resources=webapps,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=webapp.example.com,resources=webapps/status,verbs=get;update;patch
// +kubebuilder:rbac:groups=apps,resources=deployments,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups="",resources=services,verbs=get;list;watch;create;update;patch;delete

func (r *WebAppReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
    logger := log.FromContext(ctx)

    // Step 1: Fetch the WebApp instance
    webapp := &webappv1.WebApp{}
    if err := r.Get(ctx, req.NamespacedName, webapp); err != nil {
        if errors.IsNotFound(err) {
            logger.Info("WebApp deleted, nothing to do")
            return ctrl.Result{}, nil
        }
        return ctrl.Result{}, err
    }

    // Step 2: Reconcile Deployment
    deploy := &appsv1.Deployment{}
    deployName := types.NamespacedName{Name: webapp.Name, Namespace: webapp.Namespace}
    if err := r.Get(ctx, deployName, deploy); err != nil {
        if errors.IsNotFound(err) {
            deploy = r.buildDeployment(webapp)
            if err := ctrl.SetControllerReference(webapp, deploy, r.Scheme); err != nil {
                return ctrl.Result{}, err
            }
            logger.Info("Creating Deployment", "name", deploy.Name)
            return ctrl.Result{}, r.Create(ctx, deploy)
        }
        return ctrl.Result{}, err
    }
    // Update if spec changed
    if *deploy.Spec.Replicas != *webapp.Spec.Replicas ||
        deploy.Spec.Template.Spec.Containers[0].Image != webapp.Spec.Image {
        deploy.Spec.Replicas = webapp.Spec.Replicas
        deploy.Spec.Template.Spec.Containers[0].Image = webapp.Spec.Image
        logger.Info("Updating Deployment", "name", deploy.Name)
        if err := r.Update(ctx, deploy); err != nil {
            return ctrl.Result{}, err
        }
    }

    // Step 3: Reconcile Service
    svc := &corev1.Service{}
    svcName := types.NamespacedName{Name: webapp.Name, Namespace: webapp.Namespace}
    if err := r.Get(ctx, svcName, svc); err != nil {
        if errors.IsNotFound(err) {
            svc = r.buildService(webapp)
            if err := ctrl.SetControllerReference(webapp, svc, r.Scheme); err != nil {
                return ctrl.Result{}, err
            }
            logger.Info("Creating Service", "name", svc.Name)
            return ctrl.Result{}, r.Create(ctx, svc)
        }
        return ctrl.Result{}, err
    }

    // Step 4: Update Status
    webapp.Status.AvailableReplicas = deploy.Status.AvailableReplicas
    if err := r.Status().Update(ctx, webapp); err != nil {
        return ctrl.Result{}, err
    }

    return ctrl.Result{}, nil
}

func (r *WebAppReconciler) buildDeployment(app *webappv1.WebApp) *appsv1.Deployment {
    labels := map[string]string{"app": app.Name, "managed-by": "webapp-operator"}
    return &appsv1.Deployment{
        ObjectMeta: metav1.ObjectMeta{
            Name:      app.Name,
            Namespace: app.Namespace,
            Labels:    labels,
        },
        Spec: appsv1.DeploymentSpec{
            Replicas: app.Spec.Replicas,
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
            Selector: map[string]string{"app": app.Name},
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

Key patterns in this controller:
- **SetControllerReference**: Links child resources to the WebApp. When the WebApp is deleted, Kubernetes garbage-collects the Deployment and Service automatically.
- **Owns()**: Tells the framework to trigger reconciliation when owned Deployments or Services change. If someone manually deletes the Deployment, the operator recreates it.
- **Status subresource**: Updated separately from spec, preventing conflicts.

---

## Testing with envtest

Kubebuilder includes `envtest`, which spins up a real API server and etcd binary locally -- no cluster needed. Edit `internal/controller/webapp_controller_test.go`:

```go
var _ = Describe("WebApp Controller", func() {
    const (
        WebAppName      = "test-webapp"
        WebAppNamespace = "default"
        WebAppImage     = "nginx:1.25"
    )

    ctx := context.Background()

    It("should create Deployment and Service for a new WebApp", func() {
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

        // Create WebApp
        Expect(k8sClient.Create(ctx, webapp)).Should(Succeed())

        // Verify Deployment appears
        deploy := &appsv1.Deployment{}
        Eventually(func() error {
            return k8sClient.Get(ctx, types.NamespacedName{
                Name: WebAppName, Namespace: WebAppNamespace,
            }, deploy)
        }, "10s", "1s").Should(Succeed())

        Expect(*deploy.Spec.Replicas).To(Equal(int32(2)))
        Expect(deploy.Spec.Template.Spec.Containers[0].Image).To(Equal(WebAppImage))

        // Verify Service appears
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

Run tests:

```bash
make test  # Downloads envtest binaries, runs suite
```

This gives you real API server validation without Docker, kind, or any cluster. Tests run in seconds.

---

## Operator Packaging and Deployment

### Build and Push the Image

```bash
# Build the operator image
make docker-build IMG=myregistry/webapp-operator:v0.1.0

# Push to registry
make docker-push IMG=myregistry/webapp-operator:v0.1.0
```

### Deploy to a Cluster

```bash
# Install CRDs
make install

# Deploy the operator (creates namespace, RBAC, Deployment)
make deploy IMG=myregistry/webapp-operator:v0.1.0

# Verify
kubectl get pods -n webapp-operator-system
```

### Test It Live

```yaml
# Apply a WebApp resource
kubectl apply -f - <<EOF
apiVersion: webapp.example.com/v1
kind: WebApp
metadata:
  name: my-app
  namespace: default
spec:
  image: nginx:1.25
  replicas: 3
  port: 80
EOF
```

```bash
# Watch the operator create child resources
kubectl get webapp,deployment,service
# NAME                          IMAGE        REPLICAS   AVAILABLE   AGE
# webapp.webapp.example.com/my-app   nginx:1.25   3          3           30s

# Delete the Deployment -- the operator recreates it
kubectl delete deployment my-app
kubectl get deployment my-app  # Back within seconds
```

---

## Comparison: Operator Frameworks

| Feature | Kubebuilder | Operator SDK | Metacontroller | KUDO |
|---------|-------------|--------------|----------------|------|
| **Language** | Go | Go, Ansible, Helm | Any (webhooks) | YAML (declarative) |
| **Learning curve** | Steep (Go + K8s internals) | Moderate (wraps Kubebuilder) | Low (any language) | Low (YAML only) |
| **Power/flexibility** | Full control | Full control + OLM | Limited by webhook model | Limited to plan/phase |
| **Testing** | envtest (excellent) | envtest + scorecard | Manual | Manual |
| **Production readiness** | High (upstream SDK) | High (Red Hat backed) | Medium | Archived (CNCF) |
| **Best for** | Custom operators needing full control | Operator Lifecycle Manager integration | Polyglot teams, simple use cases | Stateful service plans |
| **Relationship** | Foundation | Built on Kubebuilder | Independent | Independent |

**When to choose what**:
- **Kubebuilder**: You write Go, you want full control, you value upstream alignment.
- **Operator SDK**: You need OLM (OperatorHub) packaging or want Ansible/Helm-based operators.
- **Metacontroller**: Your team does not write Go and needs simple sync/finalize hooks.
- **KUDO**: Archived. Avoid for new projects.

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Reading from API server instead of cache | Slow, hammers API server, may get rate-limited | Use the default client -- it reads from cache automatically |
| Not setting OwnerReferences | Child resources orphaned when parent deleted | Always call `ctrl.SetControllerReference()` |
| Updating spec and status in same call | Conflicts and lost updates | Use `r.Status().Update()` separately from `r.Update()` |
| Reconciling on status-only changes | Infinite loop: update status triggers reconcile triggers update | Add `GenerationChangedPredicate` to filter status-only events |
| Hardcoding namespace | Operator only works in one namespace | Read namespace from the request: `req.Namespace` |
| No RBAC markers | Controller crashes with 403 Forbidden | Add `+kubebuilder:rbac` comments, run `make manifests` |
| Ignoring `IsNotFound` on Get | Reconcile errors on deleted resources | Check `errors.IsNotFound(err)` and return cleanly |

---

## Quiz

### Question 1
What does `ctrl.SetControllerReference(owner, child, scheme)` do, and why is it critical?

<details>
<summary>Show Answer</summary>

It sets an **OwnerReference** on the child object pointing to the owner. This does two things:

1. **Garbage collection**: When the owner (WebApp) is deleted, Kubernetes automatically deletes all children (Deployment, Service).
2. **Watch propagation**: When using `.Owns()` in `SetupWithManager`, changes to owned objects trigger reconciliation of the owner.

Without it, deleting a WebApp would leave orphaned Deployments and Services running forever.

</details>

### Question 2
Why does the reconciler read from a cache instead of directly from the API server?

<details>
<summary>Show Answer</summary>

The **cache** (backed by informers/watches) provides:

1. **Performance**: Reads are local memory lookups, not API server HTTP calls
2. **Reduced load**: Hundreds of reconciliations per second without overwhelming the API server
3. **Consistency**: The cache is updated via a watch stream, so it stays current

The tradeoff is **eventual consistency** -- immediately after a write, the cache may not reflect the change. This is why reconciliation is idempotent: if the cache is stale, the next reconciliation fixes it.

</details>

### Question 3
What happens when you return `ctrl.Result{RequeueAfter: 30 * time.Second}` from Reconcile?

<details>
<summary>Show Answer</summary>

The controller framework will re-enqueue the reconciliation request after 30 seconds. This is useful for:

- **Polling external systems** that do not trigger Kubernetes events
- **Waiting for conditions** (e.g., a cloud resource provisioning)
- **Periodic checks** that cannot be event-driven

Unlike returning an error (which uses exponential backoff), `RequeueAfter` uses a fixed delay.

</details>

### Question 4
Your operator enters an infinite reconciliation loop. What is the most likely cause?

<details>
<summary>Show Answer</summary>

The most common cause: **updating the resource's spec or metadata inside Reconcile without a GenerationChangedPredicate**. Each update triggers a new event, which triggers another reconciliation, which triggers another update.

Fixes:
1. Add `builder.WithPredicates(predicate.GenerationChangedPredicate{})` -- this ignores events where only status/metadata changed
2. Only update when values actually differ (compare before writing)
3. Use the **status subresource** for observed state -- status updates do not increment `metadata.generation`

</details>

---

## Hands-On Exercise

### Objective
Scaffold a Kubebuilder project, implement the WebApp operator, test it, and deploy it to a kind cluster.

### Environment Setup

```bash
# Prerequisites: Go 1.21+, Docker, kind
kind create cluster --name operator-lab

# Install Kubebuilder
curl -L -o kubebuilder "https://go.kubebuilder.io/dl/latest/$(go env GOOS)/$(go env GOARCH)"
chmod +x kubebuilder && sudo mv kubebuilder /usr/local/bin/
```

### Tasks

1. **Scaffold the project**:
   ```bash
   mkdir webapp-operator && cd webapp-operator
   kubebuilder init --domain example.com --repo github.com/example/webapp-operator
   kubebuilder create api --group webapp --version v1 --kind WebApp
   ```

2. **Define the API**: Edit `api/v1/webapp_types.go` with the WebAppSpec and WebAppStatus structs from this module. Run `make manifests generate`.

3. **Implement the controller**: Edit `internal/controller/webapp_controller.go` with the reconcile logic from this module.

4. **Run tests**:
   ```bash
   make test
   ```

5. **Install CRDs and run locally** (against the kind cluster):
   ```bash
   make install   # Installs CRDs into cluster
   make run       # Runs controller locally against cluster
   ```

6. **Apply a WebApp resource** (in another terminal):
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
   kubectl get webapp
   kubectl get deployment test-app
   kubectl get service test-app
   ```

8. **Test self-healing**: Delete the Deployment and watch the operator recreate it:
   ```bash
   kubectl delete deployment test-app
   kubectl get deployment test-app  # Should reappear
   ```

### Success Criteria
- [ ] Kubebuilder project scaffolded and compiles
- [ ] CRD installed in cluster (`kubectl get crd webapps.webapp.example.com`)
- [ ] Creating a WebApp produces a Deployment and Service
- [ ] Deleting the Deployment triggers operator to recreate it
- [ ] `make test` passes with envtest

### Bonus Challenge
Add a `ServiceType` field to the WebApp spec (ClusterIP or NodePort) and make the controller set the Service type accordingly. Write an envtest case that validates the behavior.

---

## Cross-References

- **CRD Foundations**: [CKA Module 1.5: CRDs and Operators](../../../k8s/cka/part1-cluster-architecture/module-1.5-crds-operators/) covers the Kubernetes extension mechanics that operators build on.
- **Operator in the Wild**: [Module 15.5: etcd-operator](../../toolkits/data-ai-platforms/cloud-native-databases/module-15.5-etcd-operator/) shows a production operator managing a distributed database.
- **Declarative Infrastructure**: [Module 7.2: Crossplane](module-7.2-crossplane/) uses the same controller-runtime reconciliation pattern, but for cloud resources instead of in-cluster workloads.

---

## Further Reading

- [Kubebuilder Book](https://book.kubebuilder.io/) -- Official tutorial and reference
- [controller-runtime GoDoc](https://pkg.go.dev/sigs.k8s.io/controller-runtime) -- API reference
- [Programming Kubernetes (O'Reilly)](https://www.oreilly.com/library/view/programming-kubernetes/9781492047094/) -- Deep dive into the Kubernetes API machinery
- [Kubernetes API Conventions](https://github.com/kubernetes/community/blob/master/contributors/devel/sig-architecture/api-conventions.md) -- The rules your CRDs should follow

---

## Next Module

Continue to the next module in the Platforms Toolkit to expand your platform engineering skills.

---

*"The best operator is one your team forgets is running -- because it just works, every time, at 3 AM."*

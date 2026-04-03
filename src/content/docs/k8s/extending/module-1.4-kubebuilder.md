---
title: "Module 1.4: The Operator Pattern & Kubebuilder"
slug: k8s/extending/module-1.4-kubebuilder
sidebar:
  order: 5
---
> **Complexity**: `[COMPLEX]` - Framework-based operator development
>
> **Time to Complete**: 4 hours
>
> **Prerequisites**: Module 1.3 (Building Controllers with client-go), Go 1.22+, Docker

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Scaffold** a multi-group operator project with Kubebuilder, including CRD types, controllers, and webhook stubs
2. **Implement** a Reconciler using controller-runtime that handles create, update, and delete events with proper status reporting
3. **Generate** RBAC manifests, CRD YAMLs, and webhook configurations from Go markers and deploy them with `make deploy`
4. **Validate** operator behavior using envtest integration tests that run against a real API Server without a full cluster

---

## Why This Module Matters

In Module 1.3 you built a controller from scratch with raw client-go. It worked, but you wrote a lot of boilerplate: informer setup, workqueue wiring, unstructured-to-typed conversion, event recording plumbing. For one controller that is fine, but for a production operator with multiple CRDs, webhooks, RBAC, and tests, the boilerplate becomes a burden.

**Kubebuilder** eliminates this burden. It is the official Kubernetes project for building operators, and it generates the scaffolding while you focus on the business logic. Kubebuilder uses **controller-runtime** under the hood -- the same library powering Operator SDK, Cluster API, and hundreds of production operators. Learning Kubebuilder is not learning "a framework"; it is learning the standard way to build Kubernetes extensions.

> **The Kitchen Analogy**
>
> Module 1.3 was like cooking from scratch -- you bought raw ingredients (client-go), built your own stove (informer wiring), and cooked everything yourself. Kubebuilder is like a professional kitchen: the stove is installed, the mise en place is done, and the recipes are templated. You still decide what to cook (your reconciliation logic), but the infrastructure is handled. Knowing how to cook from scratch makes you a better chef, but using a professional kitchen makes you more productive.

---

## What You'll Learn

By the end of this module, you will be able to:
- Compare Kubebuilder and Operator SDK
- Scaffold a complete operator project with Kubebuilder v4
- Define API types with markers for CRD generation
- Implement a Reconciler with controller-runtime
- Use RBAC markers for automatic role generation
- Build, test, and deploy an operator to a cluster

---

## Did You Know?

- **Kubebuilder and Operator SDK share the same core**: Both use controller-runtime. Operator SDK adds features like OLM integration and Ansible/Helm operators, but for Go operators the two are nearly identical. Since 2023, Operator SDK officially recommends the Kubebuilder layout.

- **controller-runtime processes about 50,000 reconciliations per second** on commodity hardware. The framework handles concurrency, caching, and event deduplication so efficiently that most operators are bottlenecked by the API Server, not by controller-runtime.

- **The `//+kubebuilder:` markers are not comments**: They look like Go comments, but controller-gen parses them to generate CRDs, RBAC roles, and webhook configurations. Deleting a marker can break your entire deployment pipeline.

---

## Part 1: Kubebuilder vs Operator SDK

### 1.1 Comparison

| Feature | Kubebuilder | Operator SDK |
|---------|-------------|--------------|
| Maintained by | Kubernetes SIG API Machinery | Operator Framework (Red Hat) |
| Language support | Go only | Go, Ansible, Helm |
| Project layout | Kubebuilder layout | Kubebuilder layout (since v1.25+) |
| OLM integration | Manual | Built-in |
| Scorecard testing | No | Yes |
| Dependency | controller-runtime | controller-runtime |
| Best for | Go operators, learning | OLM distribution, multi-language |

**Bottom line**: If you write Go operators, start with Kubebuilder. If you need OLM packaging or Ansible/Helm operators, use Operator SDK (which uses Kubebuilder under the hood).

### 1.2 controller-runtime Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    controller-runtime                                │
│                                                                     │
│   ┌──────────────────────────────────────────────────────────┐     │
│   │                       Manager                             │     │
│   │                                                           │     │
│   │   • Creates shared cache (informers)                      │     │
│   │   • Manages controller lifecycle                          │     │
│   │   • Handles leader election                               │     │
│   │   • Runs webhook server                                   │     │
│   │   • Provides health/readiness endpoints                   │     │
│   └──────────────┬──────────────────┬────────────────────────┘     │
│                  │                  │                               │
│        ┌─────────▼────────┐  ┌─────▼──────────────┐               │
│        │   Controller 1   │  │   Controller 2     │               │
│        │                  │  │                    │               │
│        │  ┌────────────┐  │  │  ┌────────────┐   │               │
│        │  │ Reconciler │  │  │  │ Reconciler │   │               │
│        │  │ (YOUR CODE)│  │  │  │ (YOUR CODE)│   │               │
│        │  └────────────┘  │  │  └────────────┘   │               │
│        │                  │  │                    │               │
│        │  Watches:        │  │  Watches:          │               │
│        │  - Primary CR    │  │  - Primary CR      │               │
│        │  - Owned Deps    │  │  - Owned ConfigMaps│               │
│        └──────────────────┘  └────────────────────┘               │
│                                                                     │
│   ┌──────────────────────────────────────────────────────────┐     │
│   │                     Shared Cache                          │     │
│   │                                                           │     │
│   │   All controllers share the same informer cache.          │     │
│   │   One Watch per GVK, not per controller.                  │     │
│   └──────────────────────────────────────────────────────────┘     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Part 2: Scaffolding a Project

### 2.1 Install Kubebuilder

```bash
# Download latest Kubebuilder (v4+)
curl -L -o kubebuilder "https://go.kubebuilder.io/dl/latest/$(go env GOOS)/$(go env GOARCH)"
chmod +x kubebuilder
sudo mv kubebuilder /usr/local/bin/

# Verify
kubebuilder version
```

### 2.2 Initialize the Project

```bash
mkdir -p ~/extending-k8s/webapp-operator && cd ~/extending-k8s/webapp-operator

# Initialize with domain and repo
kubebuilder init --domain kubedojo.io --repo github.com/kubedojo/webapp-operator

# What was generated:
# ├── Dockerfile            # Multi-stage build for the operator
# ├── Makefile              # Build, test, deploy commands
# ├── PROJECT               # Kubebuilder metadata
# ├── cmd/
# │   └── main.go           # Entry point (Manager setup)
# ├── config/
# │   ├── default/          # Kustomize overlay combining everything
# │   ├── manager/          # Controller manager deployment
# │   ├── rbac/             # RBAC roles (auto-generated)
# │   └── prometheus/       # Metrics ServiceMonitor
# ├── hack/
# │   └── boilerplate.go.txt # License header for generated files
# └── internal/
#     └── controller/       # Controller implementations go here
```

### 2.3 Create an API (CRD + Controller)

```bash
kubebuilder create api --group apps --version v1beta1 --kind WebApp

# Answer:
#   Create Resource [y/n]: y
#   Create Controller [y/n]: y

# New files:
# ├── api/
# │   └── v1beta1/
# │       ├── groupversion_info.go  # API group registration
# │       ├── webapp_types.go       # YOUR TYPE DEFINITIONS
# │       └── zz_generated.deepcopy.go  # Generated (do not edit)
# └── internal/
#     └── controller/
#         ├── webapp_controller.go       # YOUR RECONCILER
#         └── webapp_controller_test.go  # Test scaffold
```

---

## Part 3: Defining API Types

### 3.1 The Types File

This is where you define what your CRD looks like. Every field gets a Go struct tag and optional Kubebuilder markers:

```go
// api/v1beta1/webapp_types.go
package v1beta1

import (
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// WebAppSpec defines the desired state of WebApp.
type WebAppSpec struct {
	// Image is the container image to deploy.
	// +kubebuilder:validation:Required
	// +kubebuilder:validation:MinLength=1
	// +kubebuilder:validation:MaxLength=255
	Image string `json:"image"`

	// Replicas is the desired number of pod replicas.
	// +kubebuilder:validation:Minimum=1
	// +kubebuilder:validation:Maximum=100
	// +kubebuilder:default=2
	Replicas *int32 `json:"replicas,omitempty"`

	// Port is the container port to expose.
	// +kubebuilder:validation:Minimum=1
	// +kubebuilder:validation:Maximum=65535
	// +kubebuilder:default=8080
	Port int32 `json:"port,omitempty"`

	// Env contains environment variables for the container.
	// +optional
	// +kubebuilder:validation:MaxItems=50
	Env []EnvVar `json:"env,omitempty"`

	// Resources defines CPU and memory limits.
	// +optional
	Resources *ResourceSpec `json:"resources,omitempty"`

	// Ingress configuration for external access.
	// +optional
	Ingress *IngressSpec `json:"ingress,omitempty"`
}

// EnvVar represents an environment variable.
type EnvVar struct {
	// +kubebuilder:validation:Required
	// +kubebuilder:validation:Pattern=`^[A-Z_][A-Z0-9_]*$`
	Name string `json:"name"`

	// +kubebuilder:validation:MaxLength=4096
	Value string `json:"value"`
}

// ResourceSpec defines resource limits.
type ResourceSpec struct {
	// +kubebuilder:default="100m"
	CPURequest string `json:"cpuRequest,omitempty"`
	// +kubebuilder:default="500m"
	CPULimit string `json:"cpuLimit,omitempty"`
	// +kubebuilder:default="128Mi"
	MemoryRequest string `json:"memoryRequest,omitempty"`
	// +kubebuilder:default="512Mi"
	MemoryLimit string `json:"memoryLimit,omitempty"`
}

// IngressSpec defines ingress configuration.
type IngressSpec struct {
	Enabled bool   `json:"enabled,omitempty"`
	Host    string `json:"host,omitempty"`
	// +kubebuilder:default="/"
	Path       string `json:"path,omitempty"`
	TLSEnabled bool   `json:"tlsEnabled,omitempty"`
}

// WebAppStatus defines the observed state of WebApp.
type WebAppStatus struct {
	// ReadyReplicas is the number of pods that are ready.
	ReadyReplicas int32 `json:"readyReplicas,omitempty"`

	// AvailableReplicas is the number of available pods.
	AvailableReplicas int32 `json:"availableReplicas,omitempty"`

	// Phase represents the current lifecycle phase.
	// +kubebuilder:validation:Enum=Pending;Deploying;Running;Degraded;Failed
	Phase string `json:"phase,omitempty"`

	// Conditions represent the latest observations.
	// +optional
	Conditions []metav1.Condition `json:"conditions,omitempty"`

	// ObservedGeneration is the last generation reconciled.
	ObservedGeneration int64 `json:"observedGeneration,omitempty"`
}

// +kubebuilder:object:root=true
// +kubebuilder:subresource:status
// +kubebuilder:subresource:scale:specpath=.spec.replicas,statuspath=.status.readyReplicas
// +kubebuilder:printcolumn:name="Image",type=string,JSONPath=`.spec.image`
// +kubebuilder:printcolumn:name="Desired",type=integer,JSONPath=`.spec.replicas`
// +kubebuilder:printcolumn:name="Ready",type=integer,JSONPath=`.status.readyReplicas`
// +kubebuilder:printcolumn:name="Phase",type=string,JSONPath=`.status.phase`
// +kubebuilder:printcolumn:name="Age",type=date,JSONPath=`.metadata.creationTimestamp`
// +kubebuilder:resource:shortName=wa,categories=all

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

### 3.2 Marker Reference

| Marker | Where | Effect |
|--------|-------|--------|
| `+kubebuilder:object:root=true` | Type | Marks as a root Kubernetes object |
| `+kubebuilder:subresource:status` | Type | Enables `/status` subresource |
| `+kubebuilder:subresource:scale:...` | Type | Enables `/scale` subresource |
| `+kubebuilder:printcolumn:...` | Type | Adds kubectl column |
| `+kubebuilder:resource:shortName=...` | Type | Sets short names and categories |
| `+kubebuilder:validation:Required` | Field | Field is required |
| `+kubebuilder:validation:Minimum=N` | Field | Numeric minimum |
| `+kubebuilder:validation:Maximum=N` | Field | Numeric maximum |
| `+kubebuilder:validation:MinLength=N` | Field | String minimum length |
| `+kubebuilder:validation:MaxLength=N` | Field | String maximum length |
| `+kubebuilder:validation:Pattern=...` | Field | Regex validation |
| `+kubebuilder:validation:Enum=...` | Field | Allowed values |
| `+kubebuilder:validation:MaxItems=N` | Field | Array max length |
| `+kubebuilder:default=...` | Field | Default value |
| `+optional` | Field | Field is optional |

### 3.3 Generate CRD and DeepCopy

```bash
# Generate deepcopy methods and CRD manifests
make generate    # Runs controller-gen object
make manifests   # Runs controller-gen rbac:roleName=manager-role crd webhook

# Check the generated CRD
cat config/crd/bases/apps.kubedojo.io_webapps.yaml
```

---

## Part 4: Implementing the Reconciler

### 4.1 The Reconcile Function

This is where your business logic lives. controller-runtime calls this function whenever a watched resource changes:

```go
// internal/controller/webapp_controller.go
package controller

import (
	"context"
	"fmt"
	"time"

	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/api/meta"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/apimachinery/pkg/util/intstr"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/controller/controllerutil"
	"sigs.k8s.io/controller-runtime/pkg/log"

	appsv1beta1 "github.com/kubedojo/webapp-operator/api/v1beta1"
)

// WebAppReconciler reconciles a WebApp object.
type WebAppReconciler struct {
	client.Client
	Scheme *runtime.Scheme
}

// +kubebuilder:rbac:groups=apps.kubedojo.io,resources=webapps,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=apps.kubedojo.io,resources=webapps/status,verbs=get;update;patch
// +kubebuilder:rbac:groups=apps.kubedojo.io,resources=webapps/finalizers,verbs=update
// +kubebuilder:rbac:groups=apps,resources=deployments,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups="",resources=services,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups="",resources=events,verbs=create;patch

func (r *WebAppReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
	logger := log.FromContext(ctx)

	// Step 1: Fetch the WebApp instance
	webapp := &appsv1beta1.WebApp{}
	if err := r.Get(ctx, req.NamespacedName, webapp); err != nil {
		if errors.IsNotFound(err) {
			// Object was deleted — nothing to do (owned resources are GC'd)
			logger.Info("WebApp not found, ignoring")
			return ctrl.Result{}, nil
		}
		return ctrl.Result{}, fmt.Errorf("fetching WebApp: %w", err)
	}

	// Step 2: Set defaults
	replicas := int32(2)
	if webapp.Spec.Replicas != nil {
		replicas = *webapp.Spec.Replicas
	}
	port := webapp.Spec.Port
	if port == 0 {
		port = 8080
	}

	// Step 3: Reconcile the Deployment
	deployment := &appsv1.Deployment{}
	deploymentName := types.NamespacedName{
		Name:      webapp.Name,
		Namespace: webapp.Namespace,
	}

	result, err := controllerutil.CreateOrUpdate(ctx, r.Client, deployment, func() error {
		// Set the deployment name/namespace if creating
		deployment.Name = webapp.Name
		deployment.Namespace = webapp.Namespace

		// Define labels
		labels := map[string]string{
			"app":                          webapp.Name,
			"app.kubernetes.io/managed-by": "webapp-operator",
			"app.kubernetes.io/part-of":    webapp.Name,
		}

		deployment.Spec = appsv1.DeploymentSpec{
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
		}

		// Add env vars if specified
		if len(webapp.Spec.Env) > 0 {
			envVars := make([]corev1.EnvVar, len(webapp.Spec.Env))
			for i, e := range webapp.Spec.Env {
				envVars[i] = corev1.EnvVar{Name: e.Name, Value: e.Value}
			}
			deployment.Spec.Template.Spec.Containers[0].Env = envVars
		}

		// Set owner reference for garbage collection
		return controllerutil.SetControllerReference(webapp, deployment, r.Scheme)
	})

	if err != nil {
		return ctrl.Result{}, fmt.Errorf("reconciling deployment: %w", err)
	}

	if result != controllerutil.OperationResultNone {
		logger.Info("Deployment reconciled",
			"name", deploymentName, "operation", result)
	}

	// Step 4: Reconcile the Service
	service := &corev1.Service{
		ObjectMeta: metav1.ObjectMeta{
			Name:      webapp.Name,
			Namespace: webapp.Namespace,
		},
	}

	svcResult, err := controllerutil.CreateOrUpdate(ctx, r.Client, service, func() error {
		service.Spec = corev1.ServiceSpec{
			Selector: map[string]string{"app": webapp.Name},
			Ports: []corev1.ServicePort{
				{
					Port:       port,
					TargetPort: intstr.FromInt32(port),
					Protocol:   corev1.ProtocolTCP,
				},
			},
			Type: corev1.ServiceTypeClusterIP,
		}
		return controllerutil.SetControllerReference(webapp, service, r.Scheme)
	})

	if err != nil {
		return ctrl.Result{}, fmt.Errorf("reconciling service: %w", err)
	}

	if svcResult != controllerutil.OperationResultNone {
		logger.Info("Service reconciled",
			"name", webapp.Name, "operation", svcResult)
	}

	// Step 5: Update status
	// Re-fetch the deployment to get current status
	if err := r.Get(ctx, deploymentName, deployment); err != nil {
		return ctrl.Result{}, fmt.Errorf("fetching deployment status: %w", err)
	}

	phase := "Pending"
	if deployment.Status.ReadyReplicas == replicas {
		phase = "Running"
	} else if deployment.Status.ReadyReplicas > 0 {
		phase = "Deploying"
	}

	// Set conditions
	readyCondition := metav1.Condition{
		Type:               "Ready",
		ObservedGeneration: webapp.Generation,
		LastTransitionTime: metav1.Now(),
	}
	if phase == "Running" {
		readyCondition.Status = metav1.ConditionTrue
		readyCondition.Reason = "AllReplicasReady"
		readyCondition.Message = fmt.Sprintf("All %d replicas are ready", replicas)
	} else {
		readyCondition.Status = metav1.ConditionFalse
		readyCondition.Reason = "ReplicasNotReady"
		readyCondition.Message = fmt.Sprintf("%d/%d replicas ready",
			deployment.Status.ReadyReplicas, replicas)
	}

	webapp.Status.ReadyReplicas = deployment.Status.ReadyReplicas
	webapp.Status.AvailableReplicas = deployment.Status.AvailableReplicas
	webapp.Status.Phase = phase
	webapp.Status.ObservedGeneration = webapp.Generation
	meta.SetStatusCondition(&webapp.Status.Conditions, readyCondition)

	if err := r.Status().Update(ctx, webapp); err != nil {
		return ctrl.Result{}, fmt.Errorf("updating status: %w", err)
	}

	// If not fully ready, requeue to check again
	if phase != "Running" {
		return ctrl.Result{RequeueAfter: 10 * time.Second}, nil
	}

	return ctrl.Result{}, nil
}

// SetupWithManager sets up the controller with the Manager.
func (r *WebAppReconciler) SetupWithManager(mgr ctrl.Manager) error {
	return ctrl.NewControllerManagedBy(mgr).
		For(&appsv1beta1.WebApp{}).          // Watch WebApp (primary)
		Owns(&appsv1.Deployment{}).           // Watch owned Deployments
		Owns(&corev1.Service{}).              // Watch owned Services
		Named("webapp").
		Complete(r)
}
```

### 4.2 Understanding `CreateOrUpdate`

The `controllerutil.CreateOrUpdate` function is a powerful helper:

```
CreateOrUpdate(ctx, client, object, mutateFn)
    │
    ├── Try to Get the object
    │       │
    │       ├── Not Found → call mutateFn() → Create
    │       │
    │       └── Found → call mutateFn() → Update (if changed)
    │
    └── Returns: OperationResultCreated, OperationResultUpdated, or OperationResultNone
```

The `mutateFn` is called in both cases. It sets the desired state. If the object exists and the mutated version differs from the current version, an Update is issued. This is the idempotent, declarative pattern in action.

### 4.3 Understanding Return Values

| Return Value | Meaning |
|-------------|---------|
| `ctrl.Result{}, nil` | Success, do not requeue |
| `ctrl.Result{Requeue: true}, nil` | Success, requeue immediately |
| `ctrl.Result{RequeueAfter: 10*time.Second}, nil` | Success, requeue after delay |
| `ctrl.Result{}, err` | Error, requeue with exponential backoff |

---

## Part 5: Building and Running

### 5.1 Local Development

```bash
# Generate code and manifests
make generate
make manifests

# Install CRDs into your cluster
make install

# Run the operator locally (outside the cluster)
make run

# In another terminal, create a WebApp
cat << 'EOF' | k apply -f -
apiVersion: apps.kubedojo.io/v1beta1
kind: WebApp
metadata:
  name: test-app
  namespace: default
spec:
  image: nginx:1.27
  replicas: 3
  port: 80
EOF

# Check results
k get webapp test-app
k get deployment test-app
k get svc test-app
```

### 5.2 Building the Container Image

```bash
# Build the image
make docker-build IMG=webapp-operator:v0.1.0

# Load into kind (if using kind)
kind load docker-image webapp-operator:v0.1.0

# Deploy to cluster
make deploy IMG=webapp-operator:v0.1.0

# Check the operator is running
k get pods -n webapp-operator-system
k logs -n webapp-operator-system -l control-plane=controller-manager -f
```

### 5.3 Makefile Targets Reference

| Target | What It Does |
|--------|-------------|
| `make generate` | Run controller-gen to generate DeepCopy |
| `make manifests` | Generate CRD, RBAC, webhook YAML |
| `make install` | Install CRDs into the cluster |
| `make uninstall` | Remove CRDs from the cluster |
| `make run` | Run the operator locally |
| `make docker-build` | Build the operator container image |
| `make docker-push` | Push the image to a registry |
| `make deploy` | Deploy the operator to the cluster |
| `make undeploy` | Remove the operator from the cluster |
| `make test` | Run unit and integration tests |

---

## Part 6: The Manager and Main Entry Point

### 6.1 Manager Configuration

Kubebuilder generates the main file, but understanding it is important:

```go
// cmd/main.go (simplified, key sections)
package main

import (
	"crypto/tls"
	"flag"
	"os"

	"k8s.io/apimachinery/pkg/runtime"
	utilruntime "k8s.io/apimachinery/pkg/util/runtime"
	clientgoscheme "k8s.io/client-go/kubernetes/scheme"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/healthz"
	metricsserver "sigs.k8s.io/controller-runtime/pkg/metrics/server"
	"sigs.k8s.io/controller-runtime/pkg/webhook"

	appsv1beta1 "github.com/kubedojo/webapp-operator/api/v1beta1"
	"github.com/kubedojo/webapp-operator/internal/controller"
)

var scheme = runtime.NewScheme()

func init() {
	utilruntime.Must(clientgoscheme.AddToScheme(scheme))
	utilruntime.Must(appsv1beta1.AddToScheme(scheme))
}

func main() {
	var metricsAddr string
	var probeAddr string
	var enableLeaderElection bool
	flag.StringVar(&metricsAddr, "metrics-bind-address", "0", "Metrics endpoint address")
	flag.StringVar(&probeAddr, "health-probe-bind-address", ":8081", "Health probe address")
	flag.BoolVar(&enableLeaderElection, "leader-elect", false, "Enable leader election")
	flag.Parse()

	mgr, err := ctrl.NewManager(ctrl.GetConfigOrDie(), ctrl.Options{
		Scheme: scheme,
		Metrics: metricsserver.Options{
			BindAddress: metricsAddr,
		},
		WebhookServer: webhook.NewServer(webhook.Options{
			Port: 9443,
		}),
		HealthProbeBindAddress: probeAddr,
		LeaderElection:         enableLeaderElection,
		LeaderElectionID:       "webapp-operator.kubedojo.io",
	})
	if err != nil {
		os.Exit(1)
	}

	// Register the WebApp controller
	if err = (&controller.WebAppReconciler{
		Client: mgr.GetClient(),
		Scheme: mgr.GetScheme(),
	}).SetupWithManager(mgr); err != nil {
		os.Exit(1)
	}

	// Health and readiness probes
	mgr.AddHealthzCheck("healthz", healthz.Ping)
	mgr.AddReadyzCheck("readyz", healthz.Ping)

	// Start the manager (blocks until context cancelled)
	if err := mgr.Start(ctrl.SetupSignalHandler()); err != nil {
		os.Exit(1)
	}
}
```

### 6.2 What the Manager Provides

| Feature | How |
|---------|-----|
| Shared cache | One informer per GVK, shared across controllers |
| Leader election | Kubernetes Lease-based, built in |
| Health probes | `/healthz` and `/readyz` endpoints |
| Metrics | Prometheus-compatible `/metrics` |
| Webhook server | HTTPS server for admission webhooks |
| Graceful shutdown | SIGTERM handling, drains controllers |

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Forgetting `make manifests` after changing markers | CRD not updated, RBAC wrong | Run `make manifests` after any marker change |
| Missing RBAC markers | Controller denied access to resources | Add `+kubebuilder:rbac` for every resource accessed |
| Not re-fetching before status update | Conflict errors on update | Use `r.Get()` before `r.Status().Update()` |
| Returning error on NotFound in Reconcile | Infinite retry for deleted objects | Return `nil` when the primary resource is gone |
| Ignoring `ObservedGeneration` | Controller appears stuck on status | Set `ObservedGeneration` to `obj.Generation` |
| Not using `controllerutil.SetControllerReference` | Orphaned child resources | Always set owner reference on created resources |
| Using `r.Update()` instead of `r.Status().Update()` for status | Status changes rejected or lost | Use the status sub-client for status updates |
| Hardcoded container names in deployment | Breaks when updating existing deployments | Use consistent, deterministic names |

---

## Quiz

1. **What is the purpose of the `//+kubebuilder:rbac` markers?**
   <details>
   <summary>Answer</summary>
   They tell controller-gen what RBAC permissions the controller needs. When you run `make manifests`, controller-gen reads these markers and generates ClusterRole/Role YAML in `config/rbac/`. Without them, the controller would be denied access to the resources it needs. Every resource type you access (Get, List, Watch, Create, Update, Delete) needs a corresponding RBAC marker.
   </details>

2. **How does `controllerutil.CreateOrUpdate` achieve idempotency?**
   <details>
   <summary>Answer</summary>
   It first tries to Get the object. If not found, it calls the mutate function and Creates the object. If found, it calls the mutate function on the existing object and only issues an Update if the mutated object differs from the current state. The mutate function defines the desired state, and CreateOrUpdate ensures convergence regardless of the current state. It returns OperationResultNone if no change was needed.
   </details>

3. **Explain the difference between `ctrl.Result{Requeue: true}` and returning an error.**
   <details>
   <summary>Answer</summary>
   `Requeue: true` with nil error means "the reconciliation was successful, but I want to check again soon" (e.g., waiting for a Deployment to become ready). The item is requeued immediately without backoff. Returning an error means "the reconciliation failed" and the item is requeued with exponential backoff. Use `RequeueAfter` for periodic checks and errors for actual failures.
   </details>

4. **Why does the Manager use a shared cache instead of separate informers per controller?**
   <details>
   <summary>Answer</summary>
   If you have 5 controllers all watching Pods, a shared cache opens only one Watch connection for Pods. Without sharing, you would have 5 Watch connections, 5 separate caches, and 5x the memory usage. The shared cache also means that all controllers see a consistent view of the cluster state, since they read from the same informer.
   </details>

5. **A WebApp has `generation: 5` but its status shows `observedGeneration: 3`. What does this mean?**
   <details>
   <summary>Answer</summary>
   It means the controller has not yet reconciled the latest spec changes. The `generation` field increments on every spec change (by the API Server). The `observedGeneration` is set by the controller to indicate which generation it last processed. A gap means either the controller is behind (busy processing other objects) or it encountered errors. Users and monitoring tools use this gap to detect stale reconciliation.
   </details>

6. **What happens when you call `Owns(&appsv1.Deployment{})` in `SetupWithManager`?**
   <details>
   <summary>Answer</summary>
   It tells controller-runtime to watch all Deployments and, for any Deployment that has an OwnerReference pointing to a WebApp, enqueue that WebApp for reconciliation. The handler automatically looks up the owner via the OwnerReference metadata. This is how the controller detects when someone modifies or deletes a child Deployment -- it triggers a reconciliation of the parent WebApp, which can then correct the drift.
   </details>

---

## Hands-On Exercise

**Task**: Scaffold and implement a complete operator using Kubebuilder that manages WebApp resources.

**Setup**:
```bash
kind create cluster --name kubebuilder-lab

# Install Kubebuilder if not already installed
curl -L -o kubebuilder "https://go.kubebuilder.io/dl/latest/$(go env GOOS)/$(go env GOARCH)"
chmod +x kubebuilder && sudo mv kubebuilder /usr/local/bin/
```

**Steps**:

1. **Scaffold the project**:
```bash
mkdir -p ~/extending-k8s/webapp-operator && cd ~/extending-k8s/webapp-operator
kubebuilder init --domain kubedojo.io --repo github.com/kubedojo/webapp-operator
kubebuilder create api --group apps --version v1beta1 --kind WebApp
```

2. **Replace the generated types** in `api/v1beta1/webapp_types.go` with the code from Part 3.1

3. **Replace the generated controller** in `internal/controller/webapp_controller.go` with the code from Part 4.1

4. **Generate and install**:
```bash
make generate
make manifests
make install
```

5. **Run locally and test**:
```bash
# Terminal 1: Run the operator
make run

# Terminal 2: Create a WebApp
cat << 'EOF' | k apply -f -
apiVersion: apps.kubedojo.io/v1beta1
kind: WebApp
metadata:
  name: kubebuilder-demo
spec:
  image: nginx:1.27
  replicas: 3
  port: 80
  env:
  - name: ENVIRONMENT
    value: production
EOF

# Verify
k get webapp kubebuilder-demo
k get deployment kubebuilder-demo
k get svc kubebuilder-demo
k get events --sort-by=.lastTimestamp | tail -10
```

6. **Test scaling**:
```bash
k scale webapp kubebuilder-demo --replicas=5
sleep 10
k get webapp kubebuilder-demo
k get deployment kubebuilder-demo
```

7. **Test self-healing**:
```bash
k delete deployment kubebuilder-demo
sleep 10
k get deployment kubebuilder-demo   # Should be recreated
```

8. **Build and deploy as container**:
```bash
make docker-build IMG=webapp-operator:v0.1.0
kind load docker-image webapp-operator:v0.1.0 --name kubebuilder-lab
make deploy IMG=webapp-operator:v0.1.0

# Stop the local run (Ctrl+C in terminal 1)
# Check the deployed operator
k get pods -n webapp-operator-system
```

9. **Cleanup**:
```bash
make undeploy
make uninstall
kind delete cluster --name kubebuilder-lab
```

**Success Criteria**:
- [ ] Kubebuilder scaffolds the project without errors
- [ ] `make generate` and `make manifests` complete successfully
- [ ] CRD installs and `k get webapps` works
- [ ] Creating a WebApp triggers Deployment + Service creation
- [ ] Printer columns show correct data
- [ ] Status subresource updates with readyReplicas and phase
- [ ] `kubectl scale` works via the scale subresource
- [ ] Self-healing works (deleted Deployment is recreated)
- [ ] Operator builds as a Docker image and deploys to cluster

---

## Next Module

[Module 1.5: Advanced Operator Development](../module-1.5-advanced-operators/) - Add finalizers, status conditions, Kubernetes events, and comprehensive testing with envtest.

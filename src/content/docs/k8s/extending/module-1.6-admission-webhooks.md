---
title: "Module 1.6: Admission Webhooks"
slug: k8s/extending/module-1.6-admission-webhooks
sidebar:
  order: 7
---
> **Complexity**: `[COMPLEX]` - Intercepting and modifying API requests
>
> **Time to Complete**: 4 hours
>
> **Prerequisites**: Module 1.1 (API Deep Dive), TLS/certificate basics

---

## Why This Module Matters

Admission webhooks give you a checkpoint at the front door of the Kubernetes API. Every CREATE, UPDATE, or DELETE request can be intercepted, inspected, and either modified (mutating) or rejected (validating) -- before the object is stored in etcd. This is how Istio injects sidecar containers without modifying your Deployment YAML. This is how OPA/Gatekeeper enforces policies like "no pods with root access." This is how cert-manager auto-populates certificate fields.

If CRDs let you add new resource types to Kubernetes, and controllers let you act on those resources after they are stored, then admission webhooks let you control what gets stored in the first place. Together, they give you complete control over the Kubernetes API.

> **The Nightclub Bouncer Analogy**
>
> A validating webhook is a bouncer at a nightclub. It checks your ID (validates the request) and either lets you in or turns you away. It cannot change your outfit. A mutating webhook is a stylist at the door -- it can add a wristband (inject a sidecar), change your name tag (add labels), or hand you a map (set defaults). The key rule: mutating webhooks run first, then validating webhooks check the final result.

---

## What You'll Learn

By the end of this module, you will be able to:
- Understand the difference between mutating and validating webhooks
- Implement a webhook server in Go using controller-runtime
- Handle the AdmissionReview request/response cycle
- Configure TLS using cert-manager for production deployments
- Set failure policies for webhook unavailability
- Debug webhook failures and connectivity issues

---

## Did You Know?

- **Every Pod in a cluster with Istio goes through a mutating webhook**: The `istio-sidecar-injector` webhook intercepts Pod creation and adds the Envoy proxy container. In a busy cluster, this webhook handles thousands of requests per minute -- and if it goes down, no new Pods can be created (unless the failure policy is set to `Ignore`).

- **Webhooks can see the requesting user**: The AdmissionReview includes the user info (name, groups, UID) from the authentication stage. This lets you build user-aware policies like "only members of the platform-team group can create resources in production namespaces."

- **ValidatingAdmissionPolicy (CEL-based) is replacing many webhooks**: Since Kubernetes 1.30, you can write validation policies directly in the cluster using CEL expressions, without running a webhook server. However, CEL cannot mutate objects, and complex validations still require webhooks.

---

## Part 1: Webhook Architecture

### 1.1 How Admission Webhooks Work

```
┌─────────────────────────────────────────────────────────────────────┐
│                 Admission Webhook Flow                                │
│                                                                     │
│   kubectl apply -f pod.yaml                                         │
│        │                                                            │
│        ▼                                                            │
│   ┌──────────────────────────────────────────────────────────┐     │
│   │  API Server                                               │     │
│   │                                                           │     │
│   │  1. Authentication ✓                                      │     │
│   │  2. Authorization ✓                                       │     │
│   │  3. Mutating Admission Webhooks                           │     │
│   │     ├── webhook-1: inject sidecar                         │     │
│   │     ├── webhook-2: add default labels                     │     │
│   │     └── webhook-3: set resource defaults                  │     │
│   │  4. Schema Validation ✓                                   │     │
│   │  5. Validating Admission Webhooks                         │     │
│   │     ├── webhook-4: enforce naming convention              │     │
│   │     ├── webhook-5: deny privileged pods                   │     │
│   │     └── webhook-6: check resource quotas                  │     │
│   │  6. Persist to etcd ✓                                     │     │
│   │                                                           │     │
│   └──────────────┬────────────────┬──────────────────────────┘     │
│                  │ HTTPS POST     │ HTTPS POST                     │
│                  ▼                ▼                                 │
│   ┌──────────────────┐  ┌──────────────────┐                      │
│   │  Mutating Webhook │  │ Validating Webhook│                     │
│   │  Server (Pod)     │  │ Server (Pod)      │                     │
│   │                   │  │                    │                     │
│   │  Receives:        │  │  Receives:         │                     │
│   │  AdmissionReview  │  │  AdmissionReview   │                     │
│   │                   │  │                    │                     │
│   │  Returns:         │  │  Returns:          │                     │
│   │  Patched object   │  │  Allow / Deny      │                     │
│   └──────────────────┘  └──────────────────┘                      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Mutating vs Validating

| Feature | Mutating | Validating |
|---------|----------|------------|
| Can modify the object | Yes (via JSON patch) | No |
| Can reject the request | Yes | Yes |
| Execution order | First | Second (sees mutated object) |
| Typical use | Inject sidecars, set defaults, add labels | Enforce policies, naming rules |
| Runs how many times | May run again if other mutating webhooks change the object | Once (after all mutations) |

### 1.3 AdmissionReview API

The API Server sends an `AdmissionReview` request:

```json
{
  "apiVersion": "admission.k8s.io/v1",
  "kind": "AdmissionReview",
  "request": {
    "uid": "705ab4f5-6393-11e8-b7cc-42010a800002",
    "kind": {"group": "", "version": "v1", "kind": "Pod"},
    "resource": {"group": "", "version": "v1", "resource": "pods"},
    "namespace": "default",
    "operation": "CREATE",
    "userInfo": {
      "username": "admin",
      "groups": ["system:masters"]
    },
    "object": {
      "apiVersion": "v1",
      "kind": "Pod",
      "metadata": {"name": "my-pod", "namespace": "default"},
      "spec": {
        "containers": [{"name": "app", "image": "nginx:1.27"}]
      }
    },
    "oldObject": null
  }
}
```

Your webhook responds:

```json
{
  "apiVersion": "admission.k8s.io/v1",
  "kind": "AdmissionReview",
  "response": {
    "uid": "705ab4f5-6393-11e8-b7cc-42010a800002",
    "allowed": true,
    "patchType": "JSONPatch",
    "patch": "W3sib3AiOiJhZGQiLCJwYXRoIjoiL3NwZWMvY29udGFpbmVycy8xIiwidmFsdWUiOnsi..."
  }
}
```

---

## Part 2: Implementing Webhooks with Kubebuilder

### 2.1 Scaffold the Webhook

```bash
cd ~/extending-k8s/webapp-operator

# Create a defaulting (mutating) webhook
kubebuilder create webhook --group apps --version v1beta1 --kind WebApp \
  --defaulting

# Create a validating webhook
kubebuilder create webhook --group apps --version v1beta1 --kind WebApp \
  --validation

# Generated files:
# api/v1beta1/webapp_webhook.go          # YOUR webhook implementations
# api/v1beta1/webapp_webhook_test.go     # Test scaffolding
# config/webhook/                        # Webhook server config
# config/certmanager/                    # cert-manager integration
```

### 2.2 Defaulting (Mutating) Webhook

```go
// api/v1beta1/webapp_webhook.go
package v1beta1

import (
	"fmt"

	"k8s.io/apimachinery/pkg/runtime"
	ctrl "sigs.k8s.io/controller-runtime"
	logf "sigs.k8s.io/controller-runtime/pkg/log"
	"sigs.k8s.io/controller-runtime/pkg/webhook"
	"sigs.k8s.io/controller-runtime/pkg/webhook/admission"
)

var webapplog = logf.Log.WithName("webapp-webhook")

// SetupWebhookWithManager registers the webhooks with the manager.
func (r *WebApp) SetupWebhookWithManager(mgr ctrl.Manager) error {
	return ctrl.NewWebhookManagedBy(mgr).
		For(r).
		Complete()
}

// +kubebuilder:webhook:path=/mutate-apps-kubedojo-io-v1beta1-webapp,mutating=true,failurePolicy=fail,sideEffects=None,groups=apps.kubedojo.io,resources=webapps,verbs=create;update,versions=v1beta1,name=mwebapp.kb.io,admissionReviewVersions=v1

var _ webhook.Defaulter = &WebApp{}

// Default implements webhook.Defaulter.
// This is called for every CREATE and UPDATE of a WebApp.
func (r *WebApp) Default() {
	webapplog.Info("Applying defaults", "name", r.Name, "namespace", r.Namespace)

	// Set default replicas
	if r.Spec.Replicas == nil {
		defaultReplicas := int32(2)
		r.Spec.Replicas = &defaultReplicas
		webapplog.Info("Set default replicas", "replicas", defaultReplicas)
	}

	// Set default port
	if r.Spec.Port == 0 {
		r.Spec.Port = 8080
		webapplog.Info("Set default port", "port", 8080)
	}

	// Set default resource limits
	if r.Spec.Resources == nil {
		r.Spec.Resources = &ResourceSpec{
			CPURequest:    "100m",
			CPULimit:      "500m",
			MemoryRequest: "128Mi",
			MemoryLimit:   "512Mi",
		}
		webapplog.Info("Set default resource limits")
	}

	// Ensure standard labels
	if r.Labels == nil {
		r.Labels = make(map[string]string)
	}
	r.Labels["app.kubernetes.io/managed-by"] = "webapp-operator"
	r.Labels["app.kubernetes.io/part-of"] = r.Name

	// Ensure ingress path has a default
	if r.Spec.Ingress != nil && r.Spec.Ingress.Path == "" {
		r.Spec.Ingress.Path = "/"
	}
}
```

### 2.3 Validating Webhook

```go
// +kubebuilder:webhook:path=/validate-apps-kubedojo-io-v1beta1-webapp,mutating=false,failurePolicy=fail,sideEffects=None,groups=apps.kubedojo.io,resources=webapps,verbs=create;update;delete,versions=v1beta1,name=vwebapp.kb.io,admissionReviewVersions=v1

var _ webhook.Validator = &WebApp{}

// ValidateCreate implements webhook.Validator.
func (r *WebApp) ValidateCreate() (admission.Warnings, error) {
	webapplog.Info("Validating create", "name", r.Name)

	var warnings admission.Warnings

	// Validate image is not 'latest'
	if r.Spec.Image == "" {
		return warnings, fmt.Errorf("image must not be empty")
	}

	if isLatestTag(r.Spec.Image) {
		warnings = append(warnings,
			"Using ':latest' tag is not recommended for production. "+
				"Consider pinning to a specific version.")
	}

	// Validate replicas
	if r.Spec.Replicas != nil && *r.Spec.Replicas > 50 {
		warnings = append(warnings,
			fmt.Sprintf("High replica count (%d). Ensure your cluster has sufficient resources.",
				*r.Spec.Replicas))
	}

	// Validate ingress TLS requires host
	if r.Spec.Ingress != nil && r.Spec.Ingress.TLSEnabled && r.Spec.Ingress.Host == "" {
		return warnings, fmt.Errorf(
			"ingress.host is required when ingress.tlsEnabled is true")
	}

	// Validate naming convention
	if err := validateName(r.Name); err != nil {
		return warnings, err
	}

	return warnings, nil
}

// ValidateUpdate implements webhook.Validator.
func (r *WebApp) ValidateUpdate(old runtime.Object) (admission.Warnings, error) {
	webapplog.Info("Validating update", "name", r.Name)

	oldWebApp := old.(*WebApp)
	var warnings admission.Warnings

	// Prevent changing the port on update (could break existing connections)
	if oldWebApp.Spec.Port != 0 && r.Spec.Port != oldWebApp.Spec.Port {
		return warnings, fmt.Errorf(
			"port cannot be changed after creation (was %d, attempting %d). "+
				"Delete and recreate the WebApp to change the port",
			oldWebApp.Spec.Port, r.Spec.Port)
	}

	// Warn on large scaling changes
	oldReplicas := int32(2)
	if oldWebApp.Spec.Replicas != nil {
		oldReplicas = *oldWebApp.Spec.Replicas
	}
	newReplicas := int32(2)
	if r.Spec.Replicas != nil {
		newReplicas = *r.Spec.Replicas
	}

	diff := newReplicas - oldReplicas
	if diff < 0 {
		diff = -diff
	}
	if diff > 10 {
		warnings = append(warnings,
			fmt.Sprintf("Large scaling change: %d -> %d replicas. "+
				"Consider gradual scaling.", oldReplicas, newReplicas))
	}

	return warnings, nil
}

// ValidateDelete implements webhook.Validator.
func (r *WebApp) ValidateDelete() (admission.Warnings, error) {
	webapplog.Info("Validating delete", "name", r.Name)

	// Example: prevent deletion of WebApps with a specific annotation
	if r.Annotations != nil && r.Annotations["apps.kubedojo.io/prevent-deletion"] == "true" {
		return nil, fmt.Errorf(
			"WebApp %s has deletion protection enabled. "+
				"Remove the 'apps.kubedojo.io/prevent-deletion' annotation first",
			r.Name)
	}

	return nil, nil
}

// Helper functions

func isLatestTag(image string) bool {
	// Check for :latest or no tag at all
	if len(image) == 0 {
		return false
	}
	// No colon = no tag = defaults to latest
	lastColon := -1
	lastSlash := -1
	for i, c := range image {
		if c == ':' {
			lastColon = i
		}
		if c == '/' {
			lastSlash = i
		}
	}
	// If no colon after the last slash, there's no tag
	if lastColon <= lastSlash {
		return true
	}
	tag := image[lastColon+1:]
	return tag == "latest"
}

func validateName(name string) error {
	if len(name) > 40 {
		return fmt.Errorf("name must be 40 characters or fewer (got %d)", len(name))
	}
	return nil
}
```

### 2.4 Register the Webhook

In `cmd/main.go`, enable the webhook:

```go
// After setting up the controller
if os.Getenv("ENABLE_WEBHOOKS") != "false" {
    if err = (&appsv1beta1.WebApp{}).SetupWebhookWithManager(mgr); err != nil {
        setupLog.Error(err, "unable to create webhook", "webhook", "WebApp")
        os.Exit(1)
    }
}
```

---

## Part 3: Custom Webhook Server (Without Kubebuilder)

For webhooks that operate on resources you do not own (e.g., all Pods), you need a standalone webhook server:

### 3.1 Standalone Mutating Webhook

```go
// cmd/sidecar-injector/main.go
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"syscall"

	admissionv1 "k8s.io/api/admission/v1"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/klog/v2"
)

const (
	sidecarImage = "busybox:1.36"
	sidecarName  = "logging-sidecar"
	certFile     = "/etc/webhook/certs/tls.crt"
	keyFile      = "/etc/webhook/certs/tls.key"
)

type jsonPatchEntry struct {
	Op    string      `json:"op"`
	Path  string      `json:"path"`
	Value interface{} `json:"value,omitempty"`
}

func handleMutate(w http.ResponseWriter, r *http.Request) {
	klog.V(2).Info("Received admission request")

	// Decode the AdmissionReview
	var admissionReview admissionv1.AdmissionReview
	if err := json.NewDecoder(r.Body).Decode(&admissionReview); err != nil {
		klog.Errorf("Failed to decode request: %v", err)
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	request := admissionReview.Request
	klog.Infof("Processing %s %s/%s by %s",
		request.Operation, request.Namespace, request.Name,
		request.UserInfo.Username)

	// Decode the Pod
	var pod corev1.Pod
	if err := json.Unmarshal(request.Object.Raw, &pod); err != nil {
		sendResponse(w, request.UID, false, "", fmt.Sprintf("Failed to decode pod: %v", err))
		return
	}

	// Check if the sidecar should be injected
	if !shouldInject(&pod) {
		klog.Infof("Skipping injection for %s/%s", pod.Namespace, pod.Name)
		sendResponse(w, request.UID, true, "", "")
		return
	}

	// Check if sidecar already exists
	for _, c := range pod.Spec.Containers {
		if c.Name == sidecarName {
			klog.Infof("Sidecar already present in %s/%s", pod.Namespace, pod.Name)
			sendResponse(w, request.UID, true, "", "")
			return
		}
	}

	// Build JSON patch to inject sidecar
	sidecar := corev1.Container{
		Name:  sidecarName,
		Image: sidecarImage,
		Command: []string{
			"/bin/sh", "-c",
			"while true; do echo '[sidecar] heartbeat'; sleep 30; done",
		},
		Resources: corev1.ResourceRequirements{
			Limits: corev1.ResourceList{
				corev1.ResourceCPU:    resource.MustParse("50m"),
				corev1.ResourceMemory: resource.MustParse("64Mi"),
			},
			Requests: corev1.ResourceList{
				corev1.ResourceCPU:    resource.MustParse("10m"),
				corev1.ResourceMemory: resource.MustParse("32Mi"),
			},
		},
	}

	patches := []jsonPatchEntry{
		{
			Op:    "add",
			Path:  "/spec/containers/-",
			Value: sidecar,
		},
		{
			Op:    "add",
			Path:  "/metadata/annotations/sidecar.kubedojo.io~1injected",
			Value: "true",
		},
	}

	patchBytes, err := json.Marshal(patches)
	if err != nil {
		sendResponse(w, request.UID, false, "", fmt.Sprintf("Failed to marshal patch: %v", err))
		return
	}

	klog.Infof("Injecting sidecar into %s/%s", pod.Namespace, pod.Name)
	sendPatchResponse(w, request.UID, patchBytes)
}

func shouldInject(pod *corev1.Pod) bool {
	// Only inject if the annotation is set
	annotations := pod.GetAnnotations()
	if annotations == nil {
		return false
	}
	return annotations["sidecar.kubedojo.io/inject"] == "true"
}

func sendResponse(w http.ResponseWriter, uid types.UID, allowed bool, patchType string, message string) {
	response := admissionv1.AdmissionReview{
		TypeMeta: metav1.TypeMeta{
			APIVersion: "admission.k8s.io/v1",
			Kind:       "AdmissionReview",
		},
		Response: &admissionv1.AdmissionResponse{
			UID:     uid,
			Allowed: allowed,
		},
	}
	if !allowed && message != "" {
		response.Response.Result = &metav1.Status{
			Message: message,
		}
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func sendPatchResponse(w http.ResponseWriter, uid types.UID, patch []byte) {
	patchType := admissionv1.PatchTypeJSONPatch
	response := admissionv1.AdmissionReview{
		TypeMeta: metav1.TypeMeta{
			APIVersion: "admission.k8s.io/v1",
			Kind:       "AdmissionReview",
		},
		Response: &admissionv1.AdmissionResponse{
			UID:       uid,
			Allowed:   true,
			PatchType: &patchType,
			Patch:     patch,
		},
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func main() {
	klog.InitFlags(nil)

	mux := http.NewServeMux()
	mux.HandleFunc("/mutate", handleMutate)
	mux.HandleFunc("/healthz", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("ok"))
	})

	server := &http.Server{
		Addr:    ":8443",
		Handler: mux,
	}

	// Graceful shutdown
	go func() {
		sigCh := make(chan os.Signal, 1)
		signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
		<-sigCh
		klog.Info("Shutting down webhook server")
		server.Shutdown(context.Background())
	}()

	klog.Infof("Starting webhook server on :8443")
	if err := server.ListenAndServeTLS(certFile, keyFile); err != http.ErrServerClosed {
		klog.Fatalf("Failed to start server: %v", err)
	}
}
```

> **Note**: This example needs the imports `"k8s.io/apimachinery/pkg/types"` and `"k8s.io/apimachinery/pkg/api/resource"`. Your IDE will add them.

---

## Part 4: TLS and cert-manager

### 4.1 Why TLS Is Required

The API Server communicates with webhooks over HTTPS. There are no exceptions. You must provide:
1. A TLS certificate for the webhook server
2. The CA certificate in the webhook configuration so the API Server trusts the webhook

### 4.2 Option 1: cert-manager (Recommended)

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.17.0/cert-manager.yaml

# Wait for it to be ready
kubectl wait --for=condition=Available deployment -n cert-manager --all --timeout=120s
```

Create a self-signed issuer and certificate:

```yaml
# config/certmanager/certificate.yaml
apiVersion: cert-manager.io/v1
kind: Issuer
metadata:
  name: webapp-selfsigned-issuer
  namespace: webapp-system
spec:
  selfSigned: {}
---
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: webapp-webhook-cert
  namespace: webapp-system
spec:
  secretName: webapp-webhook-tls
  duration: 8760h    # 1 year
  renewBefore: 720h  # Renew 30 days before expiry
  issuerRef:
    name: webapp-selfsigned-issuer
    kind: Issuer
  dnsNames:
  - webapp-webhook-service.webapp-system.svc
  - webapp-webhook-service.webapp-system.svc.cluster.local
```

### 4.3 Option 2: Self-Signed Certificates (Dev/Testing)

```bash
# Generate CA
openssl genrsa -out ca.key 2048
openssl req -new -x509 -days 365 -key ca.key -out ca.crt -subj "/CN=webapp-webhook-ca"

# Generate server certificate
openssl genrsa -out server.key 2048
openssl req -new -key server.key -out server.csr \
  -subj "/CN=webapp-webhook-service.webapp-system.svc" \
  -config <(cat /etc/ssl/openssl.cnf <(printf "\n[SAN]\nsubjectAltName=DNS:webapp-webhook-service.webapp-system.svc,DNS:webapp-webhook-service.webapp-system.svc.cluster.local"))

openssl x509 -req -days 365 -in server.csr -CA ca.crt -CAkey ca.key \
  -CAcreateserial -out server.crt \
  -extensions SAN \
  -extfile <(cat /etc/ssl/openssl.cnf <(printf "\n[SAN]\nsubjectAltName=DNS:webapp-webhook-service.webapp-system.svc,DNS:webapp-webhook-service.webapp-system.svc.cluster.local"))

# Create the TLS secret
k create secret tls webapp-webhook-tls \
  --cert=server.crt --key=server.key \
  -n webapp-system

# Base64 encode CA for webhook config
CA_BUNDLE=$(cat ca.crt | base64 | tr -d '\n')
```

### 4.4 Webhook Configuration with caBundle Injection

With cert-manager, you can use the `cert-manager.io/inject-ca-from` annotation to automatically inject the CA:

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: MutatingWebhookConfiguration
metadata:
  name: webapp-mutating-webhook
  annotations:
    cert-manager.io/inject-ca-from: webapp-system/webapp-webhook-cert
webhooks:
- name: mwebapp.kubedojo.io
  admissionReviewVersions: ["v1"]
  sideEffects: None
  failurePolicy: Fail
  clientConfig:
    service:
      name: webapp-webhook-service
      namespace: webapp-system
      path: /mutate
      port: 443
    # caBundle is auto-injected by cert-manager
  rules:
  - apiGroups: ["apps.kubedojo.io"]
    apiVersions: ["v1beta1"]
    operations: ["CREATE", "UPDATE"]
    resources: ["webapps"]
  namespaceSelector:
    matchExpressions:
    - key: kubernetes.io/metadata.name
      operator: NotIn
      values: ["kube-system", "kube-public"]
---
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingWebhookConfiguration
metadata:
  name: webapp-validating-webhook
  annotations:
    cert-manager.io/inject-ca-from: webapp-system/webapp-webhook-cert
webhooks:
- name: vwebapp.kubedojo.io
  admissionReviewVersions: ["v1"]
  sideEffects: None
  failurePolicy: Fail
  clientConfig:
    service:
      name: webapp-webhook-service
      namespace: webapp-system
      path: /validate
      port: 443
  rules:
  - apiGroups: ["apps.kubedojo.io"]
    apiVersions: ["v1beta1"]
    operations: ["CREATE", "UPDATE", "DELETE"]
    resources: ["webapps"]
```

---

## Part 5: Failure Policies

### 5.1 What Happens When the Webhook Is Down?

| Policy | Behavior | Use When |
|--------|----------|----------|
| `Fail` | Request is rejected | Security-critical webhooks (deny privileged pods) |
| `Ignore` | Request is allowed without mutation/validation | Convenience webhooks (optional sidecars) |

```yaml
webhooks:
- name: security-policy.kubedojo.io
  failurePolicy: Fail         # Block if webhook is down
  timeoutSeconds: 5            # Default is 10, max is 30

- name: sidecar-injector.kubedojo.io
  failurePolicy: Ignore        # Allow if webhook is down
  timeoutSeconds: 3
```

### 5.2 Matching and Filtering

```yaml
webhooks:
- name: mwebapp.kubedojo.io
  rules:
  - apiGroups: [""]
    apiVersions: ["v1"]
    operations: ["CREATE"]
    resources: ["pods"]
    scope: "Namespaced"          # Only namespaced resources

  # Only match specific namespaces
  namespaceSelector:
    matchLabels:
      webhook: enabled

  # Only match specific objects
  objectSelector:
    matchLabels:
      inject-sidecar: "true"

  # Timeout
  timeoutSeconds: 10

  # Reinvocation policy (for mutating)
  reinvocationPolicy: IfNeeded   # Re-run if another webhook mutated the object
```

### 5.3 Match Conditions (Kubernetes 1.30+)

```yaml
webhooks:
- name: vwebapp.kubedojo.io
  matchConditions:
  - name: "not-system-namespace"
    expression: "!request.namespace.startsWith('kube-')"
  - name: "has-annotation"
    expression: "object.metadata.annotations['validate'] == 'true'"
```

---

## Part 6: Debugging Webhooks

### 6.1 Common Failure Modes

```
┌──────────────────────────────────────────────────────────┐
│             Webhook Debugging Flowchart                    │
│                                                           │
│   Request rejected with webhook error?                    │
│       │                                                   │
│       ├── "connection refused"                            │
│       │   → Webhook pod not running or Service misconfigured │
│       │   → Check: k get pods -n webapp-system            │
│       │   → Check: k get svc -n webapp-system             │
│       │                                                   │
│       ├── "x509: certificate" error                       │
│       │   → TLS misconfigured or caBundle wrong           │
│       │   → Check: cert-manager Certificate status        │
│       │   → Check: caBundle matches serving cert CA       │
│       │                                                   │
│       ├── "context deadline exceeded"                     │
│       │   → Webhook too slow or unreachable               │
│       │   → Check: timeoutSeconds, increase if needed     │
│       │   → Check: webhook server performance             │
│       │                                                   │
│       ├── "webhook denied the request"                    │
│       │   → Your validation logic rejected it             │
│       │   → Check: webhook server logs for reason         │
│       │                                                   │
│       └── No error but mutations not applied              │
│           → Patch format wrong or mutating webhook        │
│             not matching the resource                     │
│           → Check: webhook configuration rules            │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

### 6.2 Debugging Commands

```bash
# Check webhook configurations
k get mutatingwebhookconfigurations
k get validatingwebhookconfigurations
k describe mutatingwebhookconfiguration webapp-mutating-webhook

# Check webhook pod logs
k logs -n webapp-system -l app=webapp-webhook -f

# Check cert-manager certificate
k get certificate -n webapp-system
k describe certificate webapp-webhook-cert -n webapp-system

# Check the TLS secret
k get secret webapp-webhook-tls -n webapp-system -o yaml

# Test webhook connectivity from inside the cluster
k run test-curl --rm -it --image=curlimages/curl --restart=Never -- \
  curl -vk https://webapp-webhook-service.webapp-system.svc:443/healthz

# Check API Server logs for webhook errors (if you have access)
k logs -n kube-system kube-apiserver-<node> | grep webhook
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| Missing TLS certificate | API Server cannot connect to webhook | Use cert-manager or generate valid certs |
| Wrong `caBundle` | x509 trust errors | Ensure caBundle matches the cert's CA |
| Wrong Service name/namespace in config | Connection refused | Match exactly: `{svc}.{ns}.svc` |
| No `sideEffects: None` | Webhook calls fail on dry-run | Always set `sideEffects: None` unless you have side effects |
| `failurePolicy: Fail` on optional webhooks | Cluster breaks when webhook is down | Use `Ignore` for non-critical webhooks |
| Not excluding system namespaces | kube-system pods blocked by webhook | Add `namespaceSelector` to exclude system namespaces |
| Mutating webhook not idempotent | Duplicate sidecars on retry | Check if mutation already applied before patching |
| No health check endpoint | Cannot configure readiness probe | Add `/healthz` endpoint to webhook server |
| Webhook too slow | API calls time out | Keep webhook logic fast (<5 seconds) |

---

## Quiz

1. **What is the execution order of mutating and validating webhooks?**
   <details>
   <summary>Answer</summary>
   Mutating webhooks run first. They can modify the incoming object. Then schema validation runs. Then validating webhooks run on the final, mutated object. Validating webhooks cannot modify the object, only accept or reject it. Within mutating webhooks, execution order is undefined unless you use ordered webhook configurations.
   </details>

2. **A mutating webhook adds a sidecar container. A validating webhook then rejects the pod because it has too many containers. What happens?**
   <details>
   <summary>Answer</summary>
   The entire request is rejected. The pod is not created. The mutation (sidecar injection) has no effect because the object was never persisted to etcd. The client receives the validation error message. This is by design -- validating webhooks see the final mutated object and can reject changes made by mutating webhooks.
   </details>

3. **Why must webhook servers use TLS, and what role does `caBundle` play?**
   <details>
   <summary>Answer</summary>
   The API Server communicates with webhooks over HTTPS to prevent man-in-the-middle attacks. Since webhook servers use self-signed or internally-issued certificates (not public CA certificates), the API Server needs to know which CA to trust. `caBundle` is the base64-encoded CA certificate that the API Server uses to verify the webhook server's TLS certificate. Without it, the API Server would reject the connection as untrusted.
   </details>

4. **What is `reinvocationPolicy: IfNeeded` and when is it useful?**
   <details>
   <summary>Answer</summary>
   When multiple mutating webhooks exist, webhook A might change the object in a way that affects webhook B's decision. `reinvocationPolicy: IfNeeded` tells the API Server to re-run this webhook if another webhook modified the object after this one ran. This ensures the webhook sees the final mutated state. It is useful for webhooks that make decisions based on the full object (e.g., a resource quota webhook that needs to see all injected sidecars).
   </details>

5. **You deploy a validating webhook with `failurePolicy: Fail` and the webhook pod crashes. What happens to all API requests that match the webhook's rules?**
   <details>
   <summary>Answer</summary>
   All matching API requests are rejected with a webhook connection error. If the webhook matches Pods (a common pattern), no new Pods can be created in matching namespaces. This effectively makes the webhook a critical dependency of the API Server. This is why `failurePolicy: Ignore` is safer for non-security-critical webhooks, and why you should always exclude `kube-system` via `namespaceSelector`.
   </details>

6. **How do admission warnings work, and when should you use them?**
   <details>
   <summary>Answer</summary>
   Admission warnings are non-blocking messages returned alongside an "allowed" response. They appear as warnings in the kubectl output (yellow text). Use them for: (a) deprecation notices ("this field will be removed in v2"), (b) best practice suggestions ("using :latest tag is not recommended"), (c) informational notices ("high replica count may exceed cluster capacity"). Warnings do not block the request -- the object is still created/updated. They are ideal for soft policies.
   </details>

---

## Hands-On Exercise

**Task**: Build and deploy a mutating webhook that auto-injects a logging sidecar into Pods that have the annotation `sidecar.kubedojo.io/inject: "true"`, with TLS managed by cert-manager.

**Setup**:
```bash
kind create cluster --name webhook-lab

# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.17.0/cert-manager.yaml
kubectl wait --for=condition=Available deployment -n cert-manager --all --timeout=120s
```

**Steps**:

1. **Create the namespace and cert-manager resources**:
```bash
k create namespace webhook-demo

# Create self-signed issuer
cat << 'EOF' | k apply -f -
apiVersion: cert-manager.io/v1
kind: Issuer
metadata:
  name: selfsigned-issuer
  namespace: webhook-demo
spec:
  selfSigned: {}
---
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: sidecar-webhook-cert
  namespace: webhook-demo
spec:
  secretName: sidecar-webhook-tls
  duration: 8760h
  renewBefore: 720h
  issuerRef:
    name: selfsigned-issuer
    kind: Issuer
  dnsNames:
  - sidecar-webhook.webhook-demo.svc
  - sidecar-webhook.webhook-demo.svc.cluster.local
EOF

# Verify certificate is ready
k get certificate -n webhook-demo
```

2. **Build the sidecar injector** from Part 3.1 (adapt the code for your Go project)

3. **Create a Deployment for the webhook server** that mounts the TLS secret

4. **Create the Service**:
```bash
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Service
metadata:
  name: sidecar-webhook
  namespace: webhook-demo
spec:
  selector:
    app: sidecar-webhook
  ports:
  - port: 443
    targetPort: 8443
EOF
```

5. **Create the MutatingWebhookConfiguration** with cert-manager CA injection

6. **Test the injection**:
```bash
# Pod without annotation — no injection
k run no-inject --image=nginx --restart=Never
k get pod no-inject -o jsonpath='{.spec.containers[*].name}'
# Expected: nginx

# Pod with annotation — should get sidecar
cat << 'EOF' | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: with-inject
  annotations:
    sidecar.kubedojo.io/inject: "true"
spec:
  containers:
  - name: app
    image: nginx:1.27
EOF

k get pod with-inject -o jsonpath='{.spec.containers[*].name}'
# Expected: app logging-sidecar

# Check the injection annotation
k get pod with-inject -o jsonpath='{.metadata.annotations}'
```

7. **Cleanup**:
```bash
kind delete cluster --name webhook-lab
```

**Success Criteria**:
- [ ] cert-manager issues a valid certificate
- [ ] Webhook server starts and passes health checks
- [ ] Pods without annotation are not modified
- [ ] Pods with annotation get the sidecar container injected
- [ ] The injection annotation is set on injected pods
- [ ] Webhook logs show request processing
- [ ] Pods in `kube-system` are not affected (namespace selector)

---

## Next Module

[Module 1.7: Customizing the Scheduler](../module-1.7-scheduler-plugins/) - Extend the Kubernetes scheduler with custom scoring and filtering plugins.

---
title: "Module 5.4: Admission Controllers"
slug: k8s/cks/part5-supply-chain-security/module-5.4-admission-controllers
sidebar:
  order: 4
lab:
  id: cks-5.4-admission-controllers
  url: https://killercoda.com/kubedojo/scenario/cks-5.4-admission-controllers
  duration: "40 min"
  difficulty: advanced
  environment: kubernetes
---
> **Complexity**: `[MEDIUM]` - Critical CKS topic
>
> **Time to Complete**: 45-50 minutes
>
> **Prerequisites**: Module 5.3 (Static Analysis), API server basics

---

## What You'll Be Able to Do

After completing this module, you will be able to:

1. **Configure** validating and mutating admission webhooks for custom security enforcement
2. **Implement** ImagePolicyWebhook to restrict which container registries are allowed
3. **Audit** enabled admission controllers and their impact on cluster security posture
4. **Debug** admission controller rejections by interpreting webhook response errors

---

## Why This Module Matters

Admission controllers are gatekeepers that intercept API requests before objects are persisted. They can validate, mutate, or reject requests based on custom logic. Understanding how to enable and configure admission controllers is essential for cluster security.

CKS tests admission controller configuration and usage.

---

## Admission Controller Flow

```
┌─────────────────────────────────────────────────────────────┐
│              ADMISSION CONTROLLER PIPELINE                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  kubectl create/apply                                       │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Authentication (who is this?)                       │   │
│  └─────────────────────────────────────────────────────┘   │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Authorization (can they do this?)                   │   │
│  └─────────────────────────────────────────────────────┘   │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Mutating Admission (modify the request)            │   │
│  │  ├── MutatingAdmissionWebhook                       │   │
│  │  ├── DefaultStorageClass                            │   │
│  │  └── PodPreset (deprecated)                         │   │
│  └─────────────────────────────────────────────────────┘   │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Validating Admission (approve/deny)                │   │
│  │  ├── ValidatingAdmissionWebhook                     │   │
│  │  ├── PodSecurity (PSA)                              │   │
│  │  └── ResourceQuota                                  │   │
│  └─────────────────────────────────────────────────────┘   │
│         │                                                   │
│         ▼                                                   │
│  etcd (persist object)                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Built-in Admission Controllers

### Security-Critical Controllers

```
┌─────────────────────────────────────────────────────────────┐
│              SECURITY ADMISSION CONTROLLERS                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  PodSecurity (Kubernetes 1.25+)                            │
│  └── Enforces Pod Security Standards                       │
│      Replaces PodSecurityPolicy                            │
│                                                             │
│  NodeRestriction                                           │
│  └── Limits what kubelets can modify                       │
│      Prevents compromised nodes from affecting others      │
│                                                             │
│  AlwaysPullImages                                          │
│  └── Forces image pull on every pod start                  │
│      Prevents using cached malicious images                │
│                                                             │
│  ImagePolicyWebhook                                        │
│  └── External image verification                           │
│      Can block unsigned or vulnerable images               │
│                                                             │
│  DenyServiceExternalIPs                                    │
│  └── Blocks Service externalIPs                            │
│      Prevents CVE-2020-8554 attacks                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Check Enabled Controllers

```bash
# On kubeadm clusters
cat /etc/kubernetes/manifests/kube-apiserver.yaml | grep enable-admission-plugins

# Or via API
kubectl get pod kube-apiserver-<node> -n kube-system -o yaml | \
  grep enable-admission-plugins
```

### Enable Additional Controllers

```yaml
# /etc/kubernetes/manifests/kube-apiserver.yaml
apiVersion: v1
kind: Pod
metadata:
  name: kube-apiserver
spec:
  containers:
  - command:
    - kube-apiserver
    - --enable-admission-plugins=NodeRestriction,PodSecurity,AlwaysPullImages
    # Other flags...
```

---

## ValidatingAdmissionWebhook

ValidatingAdmissionWebhooks call external services to validate requests.

### Webhook Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              VALIDATING WEBHOOK FLOW                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  kubectl apply -f pod.yaml                                 │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │            Kubernetes API Server                     │   │
│  └─────────────────────────────────────────────────────┘   │
│         │                                                   │
│         │  AdmissionReview request (JSON)                  │
│         ▼                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │          Webhook Service (HTTPS)                     │   │
│  │  ┌─────────────────────────────────────────────┐    │   │
│  │  │  Validate request                           │    │   │
│  │  │  • Check image signatures                   │    │   │
│  │  │  • Verify security context                  │    │   │
│  │  │  • Custom business logic                    │    │   │
│  │  └─────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────┘   │
│         │                                                   │
│         │  AdmissionReview response                        │
│         │  { "allowed": true/false, "status": {...} }     │
│         ▼                                                   │
│  API Server allows or denies request                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Creating a ValidatingWebhookConfiguration

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingWebhookConfiguration
metadata:
  name: pod-validator
webhooks:
- name: pod-validator.example.com
  admissionReviewVersions: ["v1"]
  sideEffects: None
  clientConfig:
    service:
      name: pod-validator
      namespace: security
      path: /validate
    caBundle: <base64-encoded-ca-cert>
  rules:
  - apiGroups: [""]
    apiVersions: ["v1"]
    operations: ["CREATE", "UPDATE"]
    resources: ["pods"]
  failurePolicy: Fail  # Fail or Ignore
  matchPolicy: Equivalent
  namespaceSelector:
    matchLabels:
      validate-pods: "true"
```

### Key Configuration Options

```yaml
# failurePolicy: What happens if webhook is unavailable
failurePolicy: Fail    # Reject request (secure but may block cluster)
failurePolicy: Ignore  # Allow request (less secure but more available)

# sideEffects: Does webhook have side effects?
sideEffects: None      # Safe to call multiple times
sideEffects: Unknown   # May have side effects

# timeoutSeconds: How long to wait for response
timeoutSeconds: 10     # Default is 10 seconds

# namespaceSelector: Which namespaces to apply to
namespaceSelector:
  matchLabels:
    env: production

# objectSelector: Which objects to validate
objectSelector:
  matchLabels:
    validate: "true"
```

---

## ImagePolicyWebhook

ImagePolicyWebhook validates image names before pods are created.

### Enable ImagePolicyWebhook

```yaml
# /etc/kubernetes/manifests/kube-apiserver.yaml
spec:
  containers:
  - command:
    - kube-apiserver
    - --enable-admission-plugins=ImagePolicyWebhook
    - --admission-control-config-file=/etc/kubernetes/admission/config.yaml
    volumeMounts:
    - mountPath: /etc/kubernetes/admission
      name: admission-config
      readOnly: true
  volumes:
  - hostPath:
      path: /etc/kubernetes/admission
      type: DirectoryOrCreate
    name: admission-config
```

### ImagePolicyWebhook Configuration

```yaml
# /etc/kubernetes/admission/config.yaml
apiVersion: apiserver.config.k8s.io/v1
kind: AdmissionConfiguration
plugins:
- name: ImagePolicyWebhook
  configuration:
    imagePolicy:
      kubeConfigFile: /etc/kubernetes/admission/kubeconfig
      allowTTL: 50
      denyTTL: 50
      retryBackoff: 500
      defaultAllow: false  # IMPORTANT: Deny by default
```

### kubeconfig for ImagePolicyWebhook

```yaml
# /etc/kubernetes/admission/kubeconfig
apiVersion: v1
kind: Config
clusters:
- name: image-checker
  cluster:
    certificate-authority: /etc/kubernetes/admission/ca.crt
    server: https://image-checker.security.svc:443/check
contexts:
- name: image-checker
  context:
    cluster: image-checker
current-context: image-checker
```

### ImageReview Request/Response

```json
// Request sent to webhook
{
  "apiVersion": "imagepolicy.k8s.io/v1alpha1",
  "kind": "ImageReview",
  "spec": {
    "containers": [
      {
        "image": "nginx:1.25"
      }
    ],
    "namespace": "production"
  }
}

// Response from webhook
{
  "apiVersion": "imagepolicy.k8s.io/v1alpha1",
  "kind": "ImageReview",
  "status": {
    "allowed": true,
    "reason": "Image signed and scanned"
  }
}
```

---

## MutatingAdmissionWebhook

MutatingWebhooks modify requests before validation.

### Common Use Cases

```
┌─────────────────────────────────────────────────────────────┐
│              MUTATING WEBHOOK USE CASES                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Inject sidecars                                           │
│  └── Add logging, monitoring, or security containers       │
│      (Istio, Linkerd service mesh)                         │
│                                                             │
│  Add default labels/annotations                            │
│  └── Automatically add team, cost-center labels            │
│                                                             │
│  Set default security context                              │
│  └── Add runAsNonRoot: true if not specified              │
│                                                             │
│  Add imagePullSecrets                                      │
│  └── Inject registry credentials automatically             │
│                                                             │
│  Modify resource requests                                  │
│  └── Set default memory/CPU if not specified              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### MutatingWebhookConfiguration

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: MutatingWebhookConfiguration
metadata:
  name: pod-mutator
webhooks:
- name: pod-mutator.example.com
  admissionReviewVersions: ["v1"]
  sideEffects: None
  clientConfig:
    service:
      name: pod-mutator
      namespace: security
      path: /mutate
    caBundle: <base64-encoded-ca-cert>
  rules:
  - apiGroups: [""]
    apiVersions: ["v1"]
    operations: ["CREATE"]
    resources: ["pods"]
  reinvocationPolicy: Never  # or IfNeeded
```

---

## Real Exam Scenarios

### Scenario 1: Enable AlwaysPullImages

```bash
# Edit API server manifest
sudo vi /etc/kubernetes/manifests/kube-apiserver.yaml

# Find or add the --enable-admission-plugins flag
# Add AlwaysPullImages to the list:
# --enable-admission-plugins=NodeRestriction,PodSecurity,AlwaysPullImages

# Wait for API server to restart
kubectl get nodes

# Test: Pods should always pull images
kubectl run test --image=nginx
kubectl get pod test -o yaml | grep imagePullPolicy
# Should show "Always"
```

### Scenario 2: Create ValidatingWebhookConfiguration

```bash
# Create webhook configuration that blocks pods without labels
cat <<EOF | kubectl apply -f -
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingWebhookConfiguration
metadata:
  name: require-labels
webhooks:
- name: require-labels.example.com
  admissionReviewVersions: ["v1"]
  sideEffects: None
  failurePolicy: Fail
  clientConfig:
    service:
      name: label-validator
      namespace: default
      path: /validate
    caBundle: LS0tLS1CRUdJTi...  # Base64 CA cert
  rules:
  - apiGroups: [""]
    apiVersions: ["v1"]
    operations: ["CREATE"]
    resources: ["pods"]
  namespaceSelector:
    matchLabels:
      require-labels: "true"
EOF
```

### Scenario 3: Configure ImagePolicyWebhook

```bash
# Create admission config directory
sudo mkdir -p /etc/kubernetes/admission

# Create admission configuration
sudo tee /etc/kubernetes/admission/admission-config.yaml << 'EOF'
apiVersion: apiserver.config.k8s.io/v1
kind: AdmissionConfiguration
plugins:
- name: ImagePolicyWebhook
  configuration:
    imagePolicy:
      kubeConfigFile: /etc/kubernetes/admission/kubeconfig
      allowTTL: 50
      denyTTL: 50
      retryBackoff: 500
      defaultAllow: false
EOF

# Create kubeconfig for webhook
sudo tee /etc/kubernetes/admission/kubeconfig << 'EOF'
apiVersion: v1
kind: Config
clusters:
- name: image-policy
  cluster:
    certificate-authority: /etc/kubernetes/admission/ca.crt
    server: https://image-policy.security.svc:443/check
contexts:
- name: image-policy
  context:
    cluster: image-policy
current-context: image-policy
EOF

# Update API server manifest to enable ImagePolicyWebhook
sudo vi /etc/kubernetes/manifests/kube-apiserver.yaml
# Add: --enable-admission-plugins=...,ImagePolicyWebhook
# Add: --admission-control-config-file=/etc/kubernetes/admission/admission-config.yaml
# Add volume mount for /etc/kubernetes/admission
```

---

## Admission Controller Security Recommendations

```
┌─────────────────────────────────────────────────────────────┐
│              ADMISSION CONTROLLER RECOMMENDATIONS           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ENABLE (Security-critical):                               │
│  ├── NodeRestriction (always)                              │
│  ├── PodSecurity (Kubernetes 1.25+)                       │
│  ├── AlwaysPullImages (multi-tenant clusters)             │
│  └── DenyServiceExternalIPs (if not needed)               │
│                                                             │
│  CONSIDER (Based on requirements):                         │
│  ├── ImagePolicyWebhook (image validation)                │
│  ├── ValidatingAdmissionWebhook (custom policies)         │
│  └── MutatingAdmissionWebhook (default values)            │
│                                                             │
│  DISABLED BY DEFAULT (Enable carefully):                  │
│  ├── AlwaysDeny (testing only)                            │
│  └── EventRateLimit (can break cluster)                   │
│                                                             │
│  DEPRECATED:                                               │
│  └── PodSecurityPolicy (removed 1.25)                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Did You Know?

- **Admission controllers run in order**: Mutating webhooks run first, then validating webhooks. This allows mutations to be validated.

- **failurePolicy is critical**: Setting it to `Fail` is more secure but can cause cluster-wide outages if the webhook service is down.

- **NodeRestriction prevents node takeover**: It limits kubelets to only modify pods running on their node and their own Node object.

- **AlwaysPullImages has performance impact**: Every pod start requires an image pull, which increases latency and registry load.

---

## Common Mistakes

| Mistake | Why It Hurts | Solution |
|---------|--------------|----------|
| failurePolicy: Ignore | Bypasses security checks | Use Fail with high availability |
| No namespaceSelector | Applies to all namespaces | Exclude kube-system |
| Webhook timeout too short | False failures | Set 10-30 seconds |
| Not enabling NodeRestriction | Compromised node attacks | Always enable |
| defaultAllow: true | Unsigned images allowed | Set to false |

---

## Quiz

1. **What's the difference between Mutating and Validating admission webhooks?**
   <details>
   <summary>Answer</summary>
   Mutating webhooks can modify the request (add labels, inject sidecars). Validating webhooks can only approve or deny requests. Mutating runs before Validating.
   </details>

2. **What does failurePolicy: Fail do?**
   <details>
   <summary>Answer</summary>
   If the webhook is unavailable or times out, the API request is rejected. This is more secure but can cause cluster issues if the webhook service is down.
   </details>

3. **How do you enable an admission controller in kubeadm clusters?**
   <details>
   <summary>Answer</summary>
   Add it to the `--enable-admission-plugins` flag in `/etc/kubernetes/manifests/kube-apiserver.yaml`. The API server will automatically restart.
   </details>

4. **What does the ImagePolicyWebhook defaultAllow setting control?**
   <details>
   <summary>Answer</summary>
   It determines what happens when the webhook is unavailable. `defaultAllow: false` denies all images if the webhook can't be reached (more secure).
   </details>

---

## Hands-On Exercise

**Task**: Enable admission controllers and create a webhook configuration.

```bash
# Step 1: Check current admission controllers
echo "=== Current Admission Controllers ==="
kubectl get pod kube-apiserver-* -n kube-system -o yaml 2>/dev/null | \
  grep -A1 enable-admission-plugins || \
  echo "Check /etc/kubernetes/manifests/kube-apiserver.yaml on control plane"

# Step 2: Create a ValidatingWebhookConfiguration (dry-run)
cat <<EOF > webhook.yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingWebhookConfiguration
metadata:
  name: test-webhook
webhooks:
- name: test.webhook.example.com
  admissionReviewVersions: ["v1"]
  sideEffects: None
  failurePolicy: Ignore  # Using Ignore for testing
  clientConfig:
    url: "https://webhook.example.com/validate"
    caBundle: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSUJrVENDQVRlZ0F3SUJBZ0lJYzNrMGJHRnVaR1V3Q2dZSUtvWkl6ajBFQXdJd0l6RWhNQjhHQTFVRQpBeE1ZYXpOekxXTnNhV1Z1ZEMxallVQXhOekUwT0RRME5qRXdNQjRYRFRJME1EUXdOREUyTkRNeE1Gb1gKRFRJMU1EUXdOREUyTkRNeE1Gb3dJekVoTUI4R0ExVUVBeE1ZYXpOekxXTnNhV1Z1ZEMxallVQXhOekUwCk9EUTBOakV3V1RBVEJnY3Foa2pPUFFJQkJnZ3Foa2pPUFFNQkJ3TkNBQVRITCs9PT0KLS0tLS1FTkQgQ0VSVElGSUNBVEUtLS0tLQo=
  rules:
  - apiGroups: [""]
    apiVersions: ["v1"]
    operations: ["CREATE"]
    resources: ["pods"]
  namespaceSelector:
    matchLabels:
      test-webhook: "enabled"
EOF

echo "=== Webhook Configuration ==="
cat webhook.yaml

# Step 3: List existing webhook configurations
echo "=== Existing Webhooks ==="
kubectl get validatingwebhookconfigurations
kubectl get mutatingwebhookconfigurations

# Step 4: Check built-in admission controller recommendations
echo "=== Recommended Security Controllers ==="
cat <<EOF
1. NodeRestriction - Limit kubelet permissions (ALWAYS enable)
2. PodSecurity - Pod Security Standards enforcement
3. AlwaysPullImages - Force image pulls (multi-tenant)
4. DenyServiceExternalIPs - Prevent CVE-2020-8554
EOF

# Cleanup
rm -f webhook.yaml
```

**Success criteria**: Understand admission controller configuration.

---

## Summary

**Admission Controller Types**:
- Built-in controllers (enable via API server flag)
- ValidatingAdmissionWebhooks (external validation)
- MutatingAdmissionWebhooks (external mutation)

**Key Security Controllers**:
- NodeRestriction (always enable)
- PodSecurity (PSA)
- AlwaysPullImages (multi-tenant)
- ImagePolicyWebhook (image validation)

**Webhook Configuration**:
- failurePolicy: Fail vs Ignore
- namespaceSelector for scoping
- sideEffects declaration
- timeout settings

**Exam Tips**:
- Know how to enable controllers in API server
- Understand webhook configuration YAML
- Remember failurePolicy implications

---

## Part 5 Complete!

You've finished **Supply Chain Security** (20% of CKS). You now understand:
- Container image security best practices
- Image scanning with Trivy
- Static analysis with kubesec and OPA
- Admission controllers and webhooks

**Next Part**: [Part 6: Monitoring, Logging & Runtime Security](../part6-runtime-security/module-6.1-audit-logging/) - Detecting and responding to security incidents.
